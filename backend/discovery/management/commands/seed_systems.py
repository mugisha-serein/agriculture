from django.core.management.base import BaseCommand
from discovery.models import PlatformSystem

class Command(BaseCommand):
    help = 'Seed initial platform systems'

    def handle(self, *args, **options):
        systems = [
            {
                'name': 'Listings & Inventory',
                'description': 'Real-time stock management and verified product listings.',
                'icon': 'package',
                'target_url': '/discovery',
                'position': 1
            },
            {
                'name': 'Escrow Protection',
                'description': 'Safe and secure payments held until delivery confirmation.',
                'icon': 'shield',
                'target_url': '/payments',
                'position': 2
            },
            {
                'name': 'Logistics Tracking',
                'description': 'End-to-end shipment visibility with verified transporters.',
                'icon': 'truck',
                'target_url': '/logistics',
                'position': 3
            },
            {
                'name': 'Reputation Scores',
                'description': 'Trust-based ratings for all market participants.',
                'icon': 'star',
                'target_url': '/reputation',
                'position': 4
            },
        ]

        for sys_data in systems:
            obj, created = PlatformSystem.objects.update_or_create(
                name=sys_data['name'],
                defaults=sys_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created system: {obj.name}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"Updated system: {obj.name}"))
