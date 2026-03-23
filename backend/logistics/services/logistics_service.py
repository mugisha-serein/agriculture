"""Shipment coordination workflows for transporter assignment and tracking."""

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import ValidationError

from logistics.domain.statuses import ShipmentStatus
from logistics.models import DeliveryPartner
from logistics.models import DeliveryRoute
from logistics.models import Shipment
from logistics.models import ShipmentItem
from logistics.models import ShipmentTrackingEvent
from orders.models import Order
from users.models import User


class LogisticsService:
    """Application service for logistics shipment workflows."""

    @transaction.atomic
    def create_shipment(
        self,
        *,
        actor,
        order_id,
        seller_id,
        pickup_address,
        delivery_address,
        scheduled_pickup_at=None,
    ):
        """Create shipment record for an order seller allocation."""
        order = self._get_order(order_id=order_id)
        seller = self._get_user(user_id=seller_id)
        if seller.id == order.buyer_id:
            raise ValidationError({'seller_id': ['Seller cannot be the order buyer.']})
        if not order.items.filter(seller_id=seller.id).exists():
            raise ValidationError({'seller_id': ['Seller is not allocated in this order.']})
        self._assert_can_create_shipment(actor=actor, order=order, seller=seller)

        existing = Shipment.objects.filter(
            order=order,
            seller=seller,
        ).exclude(status=ShipmentStatus.CANCELLED)
        if existing.exists():
            raise ValidationError({'shipment': ['Active shipment already exists for this order and seller.']})

        return Shipment.objects.create(
            shipment_reference=Shipment.generate_shipment_reference(),
            tracking_code=Shipment.generate_tracking_code(),
            order=order,
            seller=seller,
            buyer=order.buyer,
            pickup_address=pickup_address,
            delivery_address=delivery_address,
            scheduled_pickup_at=scheduled_pickup_at,
            created_by=actor,
            status=ShipmentStatus.CREATED,
        )

    def list_shipments(self, *, actor, status=None):
        """List shipments visible to actor based on logistics role."""
        if not actor.is_authenticated:
            raise PermissionDenied('Authentication is required.')
        queryset = Shipment.objects.select_related('order', 'seller', 'buyer', 'transporter')
        if self._is_admin(actor):
            pass
        elif getattr(actor, 'role', None) == 'buyer':
            queryset = queryset.filter(buyer=actor)
        elif getattr(actor, 'role', None) == 'seller':
            queryset = queryset.filter(seller=actor)
        elif getattr(actor, 'role', None) == 'transporter':
            queryset = queryset.filter(transporter=actor)
        else:
            raise PermissionDenied('You do not have shipment access.')
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_shipment(self, *, actor, shipment_id):
        """Retrieve shipment details for authorized participant."""
        try:
            shipment = Shipment.objects.select_related(
                'order',
                'seller',
                'buyer',
                'transporter',
                'created_by',
                'delivered_by',
            ).get(id=shipment_id)
        except Shipment.DoesNotExist as exc:
            raise NotFound('Shipment was not found.') from exc
        self._assert_shipment_access(actor=actor, shipment=shipment)
        return shipment

    @transaction.atomic
    def assign_transporter(self, *, actor, shipment_id, transporter_id):
        """Assign transporter to shipment as admin-only action."""
        self._assert_admin(actor)
        shipment = self._get_locked_shipment(shipment_id=shipment_id)
        transporter = self._get_user(user_id=transporter_id)
        if getattr(transporter, 'role', None) != 'transporter':
            raise ValidationError({'transporter_id': ['Assigned user must have transporter role.']})
        if shipment.status in {ShipmentStatus.CANCELLED, ShipmentStatus.DELIVERED}:
            raise ValidationError({'status': ['Cannot assign transporter for finalized shipment.']})

        shipment.transporter = transporter
        shipment.status = ShipmentStatus.ASSIGNED
        shipment.assigned_at = timezone.now()
        shipment.save(update_fields=['transporter', 'status', 'assigned_at', 'updated_at'])
        return shipment

    @transaction.atomic
    def update_status(
        self,
        *,
        actor,
        shipment_id,
        status,
        location_note='',
        delivery_proof='',
        lat=None,
        lng=None,
        timestamp=None,
    ):
        """Update shipment tracking status through valid transitions."""
        shipment = self._get_locked_shipment(shipment_id=shipment_id)
        self._assert_status_update_access(actor=actor, shipment=shipment, next_status=status)

        allowed_next = {
            ShipmentStatus.CREATED: {ShipmentStatus.ASSIGNED, ShipmentStatus.CANCELLED, ShipmentStatus.FAILED},
            ShipmentStatus.ASSIGNED: {ShipmentStatus.PICKED_UP, ShipmentStatus.CANCELLED, ShipmentStatus.FAILED},
            ShipmentStatus.PICKED_UP: {ShipmentStatus.IN_TRANSIT, ShipmentStatus.CANCELLED, ShipmentStatus.FAILED},
            ShipmentStatus.IN_TRANSIT: {ShipmentStatus.OUT_FOR_DELIVERY, ShipmentStatus.CANCELLED, ShipmentStatus.FAILED},
            ShipmentStatus.OUT_FOR_DELIVERY: {ShipmentStatus.DELIVERED, ShipmentStatus.FAILED, ShipmentStatus.RETURNED},
            ShipmentStatus.FAILED: {ShipmentStatus.RETURNED, ShipmentStatus.CANCELLED},
            ShipmentStatus.RETURNED: {ShipmentStatus.CANCELLED},
            ShipmentStatus.DELIVERED: set(),
            ShipmentStatus.CANCELLED: set(),
        }
        if status not in allowed_next[shipment.status]:
            raise ValidationError({'status': ['Invalid shipment status transition.']})

        now = timezone.now()
        shipment.status = status
        if location_note:
            shipment.last_location_note = location_note
        if status == ShipmentStatus.PICKED_UP:
            shipment.picked_up_at = now
        if status == ShipmentStatus.IN_TRANSIT:
            shipment.in_transit_at = now
        if status == ShipmentStatus.DELIVERED:
            shipment.delivered_at = now
            shipment.delivered_by = actor
            shipment.delivery_proof = delivery_proof
        if status == ShipmentStatus.OUT_FOR_DELIVERY:
            shipment.in_transit_at = now
        if status == ShipmentStatus.CANCELLED:
            shipment.cancelled_at = now
        shipment.save(
            update_fields=[
                'status',
                'last_location_note',
                'picked_up_at',
                'in_transit_at',
                'delivered_at',
                'delivered_by',
                'delivery_proof',
                'cancelled_at',
                'updated_at',
            ]
        )
        if lat is not None and lng is not None:
            self._log_tracking_event(
                shipment=shipment,
                status=status,
                lat=lat,
                lng=lng,
                timestamp=timestamp,
            )
        return shipment

    @transaction.atomic
    def cancel_shipment(self, *, actor, shipment_id, reason):
        """Cancel shipment according to participant cancellation policy."""
        if not reason.strip():
            raise ValidationError({'reason': ['Cancellation reason is required.']})
        shipment = self._get_locked_shipment(shipment_id=shipment_id)
        if shipment.status in {ShipmentStatus.DELIVERED, ShipmentStatus.CANCELLED}:
            raise ValidationError({'status': ['Shipment is already finalized.']})
        if not self._can_cancel(actor=actor, shipment=shipment):
            raise PermissionDenied('You cannot cancel this shipment.')

        shipment.status = ShipmentStatus.CANCELLED
        shipment.cancelled_at = timezone.now()
        shipment.cancellation_reason = reason
        shipment.save(update_fields=['status', 'cancelled_at', 'cancellation_reason', 'updated_at'])
        return shipment

    @transaction.atomic
    def confirm_delivery(self, *, actor, shipment_id, confirmation_note=''):
        """Confirm delivered shipment receipt by buyer or admin."""
        shipment = self._get_locked_shipment(shipment_id=shipment_id)
        if not self._is_admin(actor) and actor.id != shipment.buyer_id:
            raise PermissionDenied('Only buyer or admin can confirm delivery.')
        if shipment.status != ShipmentStatus.DELIVERED:
            raise ValidationError({'status': ['Only delivered shipments can be confirmed.']})

        shipment.delivery_confirmed_at = timezone.now()
        shipment.delivery_confirmation_note = confirmation_note
        shipment.save(update_fields=['delivery_confirmed_at', 'delivery_confirmation_note', 'updated_at'])
        return shipment

    @transaction.atomic
    def plan_delivery_routes(
        self,
        *,
        actor,
        shipment_ids,
        vehicle_identifier,
        driver_name,
        capacity=4,
        delivery_partner_id=None,
    ):
        """Plan optimized routes for a list of shipments."""
        self._assert_route_planner(actor)
        if capacity <= 0:
            raise ValidationError({'capacity': ['Capacity must be greater than zero.']})
        shipments = list(
            Shipment.objects.select_for_update()
            .filter(id__in=shipment_ids, status__in=[ShipmentStatus.CREATED, ShipmentStatus.ASSIGNED])
            .order_by('id')
        )
        if not shipments:
            raise ValidationError({'shipment_ids': ['No eligible shipments found for routing.']})
        partner = self._resolve_delivery_partner(delivery_partner_id)
        optimizer = VehicleRoutingProblemSolver(vehicle_capacity=capacity)
        groups = optimizer.plan_routes(shipments)
        now = timezone.now()
        created_routes = []
        for group in groups:
            route = DeliveryRoute.objects.create(
                route_code=DeliveryRoute.generate_route_code(),
                delivery_partner=partner,
                vehicle_identifier=vehicle_identifier,
                driver_name=driver_name,
                capacity=capacity,
                estimated_start=now,
            )
            for sequence, shipment in enumerate(group, start=1):
                ShipmentItem.objects.create(
                    route=route,
                    shipment=shipment,
                    sequence=sequence,
                    status=shipment.status,
                )
                if shipment.status == ShipmentStatus.CREATED:
                    shipment.status = ShipmentStatus.ASSIGNED
                    shipment.assigned_at = now
                    shipment.save(update_fields=['status', 'assigned_at', 'updated_at'])
            created_routes.append(route)
        return created_routes

    def record_tracking_event(self, *, actor, shipment_id, lat, lng, status, timestamp=None):
        """Record an external tracking telemetry event."""
        shipment = self.get_shipment(actor=actor, shipment_id=shipment_id)
        return self._log_tracking_event(
            shipment=shipment,
            status=status,
            lat=lat,
            lng=lng,
            timestamp=timestamp,
        )

    def _assert_can_create_shipment(self, *, actor, order, seller):
        """Validate actor can create shipment for order seller pair."""
        if not actor.is_authenticated:
            raise PermissionDenied('Authentication is required.')
        if self._is_admin(actor):
            return
        if getattr(actor, 'role', None) != 'seller':
            raise PermissionDenied('Only seller or admin can create shipment.')
        if actor.id != seller.id:
            raise PermissionDenied('Seller can create shipment only for own order items.')
        if not order.items.filter(seller_id=actor.id).exists():
            raise PermissionDenied('Seller is not part of this order.')

    def _assert_route_planner(self, actor):
        if not actor.is_authenticated:
            raise PermissionDenied('Authentication is required.')
        if self._is_admin(actor):
            return
        raise PermissionDenied('Only admin actors can plan delivery routes.')

    def _assert_admin(self, actor):
        if not self._is_admin(actor):
            raise PermissionDenied('Only admin can perform this action.')

    def _resolve_delivery_partner(self, partner_id):
        if partner_id is None:
            return None
        try:
            return DeliveryPartner.objects.get(id=partner_id, is_active=True)
        except DeliveryPartner.DoesNotExist as exc:
            raise ValidationError({'delivery_partner_id': ['Delivery partner was not found.']}) from exc

    def _log_tracking_event(self, *, shipment, status, lat, lng, timestamp=None):
        return ShipmentTrackingEvent.objects.create(
            shipment=shipment,
            status=status,
            lat=lat,
            lng=lng,
            timestamp=timestamp or timezone.now(),
        )

    def _assert_shipment_access(self, *, actor, shipment):
        """Validate actor can read shipment record."""
        if not actor.is_authenticated:
            raise PermissionDenied('Authentication is required.')
        if self._is_admin(actor):
            return
        if actor.id in {
            shipment.buyer_id,
            shipment.seller_id,
            shipment.transporter_id,
        }:
            return
        raise PermissionDenied('You do not have access to this shipment.')

    def _assert_status_update_access(self, *, actor, shipment, next_status):
        """Validate actor can update shipment status transitions."""
        if not actor.is_authenticated:
            raise PermissionDenied('Authentication is required.')
        if self._is_admin(actor):
            return
        if next_status == ShipmentStatus.CANCELLED:
            if self._can_cancel(actor=actor, shipment=shipment):
                return
            raise PermissionDenied('You cannot cancel this shipment.')
        if actor.id == shipment.transporter_id and getattr(actor, 'role', None) == 'transporter':
            return
        raise PermissionDenied('Only assigned transporter or admin can update shipment status.')

    def _can_cancel(self, *, actor, shipment):
        """Evaluate shipment cancellation permissions."""
        if self._is_admin(actor):
            return True
        if actor.id in {shipment.buyer_id, shipment.seller_id}:
            return True
        if actor.id == shipment.transporter_id and shipment.status in {
            ShipmentStatus.ASSIGNED,
            ShipmentStatus.PICKED_UP,
        }:
            return True
        return False

    def _is_admin(self, actor):
        """Return whether actor has administrative privileges."""
        return actor.is_staff or getattr(actor, 'role', None) == 'admin'

    def _get_user(self, *, user_id):
        """Return user instance by identifier."""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist as exc:
            raise ValidationError({'user_id': ['User was not found.']}) from exc

    def _get_order(self, *, order_id):
        """Return order instance by identifier."""
        try:
            return Order.objects.prefetch_related('items').get(id=order_id)
        except Order.DoesNotExist as exc:
            raise NotFound('Order was not found.') from exc

    def _get_locked_shipment(self, *, shipment_id):
        """Fetch and lock shipment row for mutation workflows."""
        try:
            return Shipment.objects.select_for_update().get(id=shipment_id)
        except Shipment.DoesNotExist as exc:
            raise NotFound('Shipment was not found.') from exc


class VehicleRoutingProblemSolver:
    """Greedy vehicle routing problem solver based on pull-forward clustering."""

    def __init__(self, vehicle_capacity: int):
        self.vehicle_capacity = max(1, vehicle_capacity)

    def plan_routes(self, shipments: list[Shipment]) -> list[list[Shipment]]:
        """Plan routes by clustering ships into capacity-constrained legs."""
        sorted_shipments = sorted(shipments, key=self._route_sort_key)
        routes = []
        current_route: list[Shipment] = []
        for shipment in sorted_shipments:
            if (
                len(current_route) >= self.vehicle_capacity
                or (current_route and self._zone_key(current_route[-1]) != self._zone_key(shipment))
            ):
                self._finalize_route(routes, current_route)
                current_route = []
            current_route.append(shipment)
        self._finalize_route(routes, current_route)
        return routes

    def _route_sort_key(self, shipment):
        scheduled = shipment.scheduled_pickup_at or timezone.now()
        return (self._zone_key(shipment), scheduled, shipment.id)

    def _zone_key(self, shipment):
        pickup = (shipment.pickup_address or '').lower()
        segments = [segment.strip() for segment in pickup.split(',') if segment.strip()]
        return segments[-1] if segments else 'default'

    def _finalize_route(self, routes, route):
        if route:
            routes.append(route[:])
