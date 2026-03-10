import React, { useEffect, useMemo, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../../api/client';
import { useAuthStore } from '../../store/authStore';
import { Button } from '../../components/ui';
import {
    Truck,
    ShieldCheck,
    CreditCard,
    ChevronLeft,
    Calendar,
    User,
    ShoppingBag,
    CheckCircle2,
    AlertCircle,
    Clock,
    Package,
    ArrowUpRight,
    LifeBuoy,
    Circle
} from 'lucide-react';
import { reportApiError } from '../../lib/identityError';

interface OrderItem {
    id: string;
    product_name: string;
    quantity: number;
    unit_price: string;
    total_price: string;
}

interface OrderDetail {
    id: string;
    total_amount: string;
    status: string;
    created_at: string;
    seller_name: string;
    items: OrderItem[];
    escrow_status: 'waiting_for_payment' | 'held_in_escrow' | 'released' | 'refunded';
    shipment_id?: string;
    shipment_status?: string;
}

interface StatusInfo {
    label: string;
    color: string;
    bg: string;
    border: string;
    icon: React.ReactNode;
}

const formatCurrency = (value: string | number) => {
    const amount = Number(value);
    if (Number.isNaN(amount)) return `$${value}`;
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        maximumFractionDigits: 2
    }).format(amount);
};

const formatDate = (value: string) => {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    });
};

const normalizeLabel = (value: string) => value.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());

const getOrderStatusInfo = (status: string): StatusInfo => {
    switch (status) {
        case 'delivered':
            return {
                label: 'Delivered',
                color: 'var(--success)',
                bg: 'rgba(16,185,129,0.1)',
                border: 'rgba(16,185,129,0.24)',
                icon: <CheckCircle2 size={14} />
            };
        case 'fulfilled':
            return {
                label: 'In Transit',
                color: 'var(--primary)',
                bg: 'rgba(45,90,39,0.1)',
                border: 'rgba(45,90,39,0.24)',
                icon: <Truck size={14} />
            };
        case 'confirmed':
            return {
                label: 'Confirmed',
                color: 'var(--info)',
                bg: 'rgba(14,165,233,0.1)',
                border: 'rgba(14,165,233,0.24)',
                icon: <CheckCircle2 size={14} />
            };
        case 'pending':
            return {
                label: 'Pending Payment',
                color: 'var(--warning)',
                bg: 'rgba(245,158,11,0.1)',
                border: 'rgba(245,158,11,0.24)',
                icon: <Clock size={14} />
            };
        case 'cancelled':
            return {
                label: 'Cancelled',
                color: 'var(--error)',
                bg: 'rgba(239,68,68,0.1)',
                border: 'rgba(239,68,68,0.24)',
                icon: <AlertCircle size={14} />
            };
        default:
            return {
                label: normalizeLabel(status),
                color: 'var(--text-muted)',
                bg: 'rgba(148,163,184,0.15)',
                border: 'rgba(148,163,184,0.28)',
                icon: <Circle size={12} />
            };
    }
};

const getEscrowInfo = (status: string): StatusInfo => {
    switch (status) {
        case 'waiting_for_payment':
            return {
                label: 'Waiting For Payment',
                color: 'var(--warning)',
                bg: 'rgba(245,158,11,0.12)',
                border: 'rgba(245,158,11,0.26)',
                icon: <Clock size={14} />
            };
        case 'held_in_escrow':
            return {
                label: 'Held In Escrow',
                color: 'var(--primary)',
                bg: 'rgba(45,90,39,0.12)',
                border: 'rgba(45,90,39,0.26)',
                icon: <ShieldCheck size={14} />
            };
        case 'released':
            return {
                label: 'Released',
                color: 'var(--success)',
                bg: 'rgba(16,185,129,0.12)',
                border: 'rgba(16,185,129,0.26)',
                icon: <CheckCircle2 size={14} />
            };
        case 'refunded':
            return {
                label: 'Refunded',
                color: 'var(--error)',
                bg: 'rgba(239,68,68,0.12)',
                border: 'rgba(239,68,68,0.26)',
                icon: <AlertCircle size={14} />
            };
        default:
            return {
                label: normalizeLabel(status),
                color: 'var(--text-muted)',
                bg: 'rgba(148,163,184,0.15)',
                border: 'rgba(148,163,184,0.28)',
                icon: <Circle size={12} />
            };
    }
};

const getShipmentInfo = (status?: string): StatusInfo => {
    if (!status) {
        return {
            label: 'Pending Assignment',
            color: 'var(--text-muted)',
            bg: 'rgba(148,163,184,0.15)',
            border: 'rgba(148,163,184,0.28)',
            icon: <Clock size={14} />
        };
    }

    switch (status) {
        case 'in_transit':
            return {
                label: 'In Transit',
                color: 'var(--primary)',
                bg: 'rgba(45,90,39,0.1)',
                border: 'rgba(45,90,39,0.24)',
                icon: <Truck size={14} />
            };
        case 'delivered':
            return {
                label: 'Delivered',
                color: 'var(--success)',
                bg: 'rgba(16,185,129,0.1)',
                border: 'rgba(16,185,129,0.24)',
                icon: <CheckCircle2 size={14} />
            };
        case 'cancelled':
            return {
                label: 'Cancelled',
                color: 'var(--error)',
                bg: 'rgba(239,68,68,0.1)',
                border: 'rgba(239,68,68,0.24)',
                icon: <AlertCircle size={14} />
            };
        default:
            return {
                label: normalizeLabel(status),
                color: 'var(--text-muted)',
                bg: 'rgba(148,163,184,0.15)',
                border: 'rgba(148,163,184,0.28)',
                icon: <Package size={14} />
            };
    }
};

const getRoleDetailMessage = (role?: string) => {
    if (role === 'seller') {
        return 'Track buyer payment, escrow release, and shipment milestones for this sale.';
    }

    if (role === 'transporter') {
        return 'Use this view to monitor pickup, in-transit status, and final delivery confirmation.';
    }

    return 'Review payment, escrow protection, and shipment updates for this purchase.';
};
export const OrderDetailPage: React.FC = () => {
    const { orderId } = useParams();
    const { user } = useAuthStore();
    const [order, setOrder] = useState<OrderDetail | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isNotFound, setIsNotFound] = useState(false);

    useEffect(() => {
        void fetchOrderDetail();
    }, [orderId]);

    const fetchOrderDetail = async () => {
        if (!orderId) return;

        setIsLoading(true);
        setIsNotFound(false);

        try {
            const response = await api.get(`/orders/${orderId}/`);
            setOrder(response.data);
        } catch (err: unknown) {
            const statusCode = (err as { response?: { status?: number } })?.response?.status;
            if (statusCode === 404) {
                setIsNotFound(true);
                setOrder(null);
            } else {
                reportApiError('Order Detail Load Failed', err);
            }
        } finally {
            setIsLoading(false);
        }
    };

    const itemCount = useMemo(() => order?.items?.reduce((sum, item) => sum + item.quantity, 0) ?? 0, [order]);

    if (isLoading) {
        return (
            <div className="container" style={{ display: 'grid', gap: '14px' }}>
                <div className="order-detail-skeleton" style={{ height: '70px' }} />
                <div className="order-detail-skeleton" style={{ height: '230px' }} />
                <div className="order-detail-skeleton" style={{ height: '180px' }} />
                <style>{`
                    .order-detail-skeleton {
                        border-radius: 16px;
                        background: linear-gradient(110deg, rgba(0,0,0,0.04) 20%, rgba(0,0,0,0.08) 35%, rgba(0,0,0,0.04) 50%);
                        background-size: 220% 100%;
                        animation: orderDetailShimmer 1.2s linear infinite;
                    }
                    @keyframes orderDetailShimmer {
                        to { background-position-x: -220%; }
                    }
                `}</style>
            </div>
        );
    }

    if (isNotFound || !order) {
        return (
            <div className="container" style={{ maxWidth: '760px' }}>
                <div style={{ background: '#fff', border: '1px dashed rgba(0,0,0,0.14)', borderRadius: '18px', padding: '48px 24px', textAlign: 'center' }}>
                    <Package size={52} style={{ color: 'rgba(45,90,39,0.3)', marginBottom: '14px' }} />
                    <h2 style={{ margin: '0 0 8px', color: 'var(--text-dark)' }}>Order not found</h2>
                    <p style={{ margin: '0 0 18px', color: 'var(--text-muted)' }}>
                        The requested order is unavailable or you do not have permission to view it.
                    </p>
                    <Link to="/orders" style={{ textDecoration: 'none' }}>
                        <Button>Back to Orders</Button>
                    </Link>
                </div>
            </div>
        );
    }

    const orderStatus = getOrderStatusInfo(order.status);
    const escrowStatus = getEscrowInfo(order.escrow_status);
    const shipmentStatus = getShipmentInfo(order.shipment_status);
    const roleMessage = getRoleDetailMessage(user?.role);

    return (
        <div className="container order-detail-page">
            <Link to="/orders" className="order-detail-back">
                <ChevronLeft size={18} />
                Back to Orders
            </Link>

            <div className="order-detail-layout">
                <section className="order-detail-main">
                    <header className="order-detail-hero">
                        <div>
                            <h1>Order #{order.id.slice(0, 8).toUpperCase()}</h1>
                            <p className="order-detail-role-message">{roleMessage}</p>
                            <div className="order-detail-hero-meta">
                                <span><Calendar size={14} /> {formatDate(order.created_at)}</span>
                                <span><User size={14} /> Seller: {order.seller_name || 'Marketplace Seller'}</span>
                                <span><ShoppingBag size={14} /> {itemCount} units</span>
                            </div>
                        </div>
                        <span
                            className="order-detail-status"
                            style={{ color: orderStatus.color, background: orderStatus.bg, borderColor: orderStatus.border }}
                        >
                            {orderStatus.icon}
                            {orderStatus.label}
                        </span>
                    </header>

                    <article className="order-card">
                        <h3 className="order-card-title">
                            <ShoppingBag size={18} />
                            Item Summary
                        </h3>

                        <div className="order-item-list">
                            {order.items.map((item) => (
                                <div key={item.id} className="order-item-row">
                                    <div>
                                        <p className="order-item-name">{item.product_name}</p>
                                        <p className="order-item-meta">Quantity: {item.quantity} units</p>
                                    </div>
                                    <div className="order-item-price-wrap">
                                        <p className="order-item-total">{formatCurrency(item.total_price)}</p>
                                        <p className="order-item-meta">{formatCurrency(item.unit_price)} / unit</p>
                                    </div>
                                </div>
                            ))}
                        </div>

                        <div className="order-total-row">
                            <span>Total Amount</span>
                            <strong>{formatCurrency(order.total_amount)}</strong>
                        </div>
                    </article>

                    {order.shipment_id && (
                        <article className="order-card">
                            <div className="shipment-header">
                                <h3 className="order-card-title" style={{ marginBottom: 0 }}>
                                    <Truck size={18} />
                                    Shipment
                                </h3>
                                <Link to={`/shipments/${order.shipment_id}`} className="shipment-link">
                                    Track Shipment <ArrowUpRight size={15} />
                                </Link>
                            </div>

                            <div className="shipment-body">
                                <span
                                    className="order-detail-status"
                                    style={{ color: shipmentStatus.color, background: shipmentStatus.bg, borderColor: shipmentStatus.border }}
                                >
                                    {shipmentStatus.icon}
                                    {shipmentStatus.label}
                                </span>
                                <p className="shipment-id">Shipment ID: {order.shipment_id}</p>
                            </div>
                        </article>
                    )}
                </section>

                <aside className="order-detail-side">
                    <article className="escrow-card">
                        <h3><ShieldCheck size={18} /> Escrow Protection</h3>
                        <p>
                            Funds are protected in escrow until delivery is confirmed or disputes are resolved.
                        </p>

                        <div className="escrow-state">
                            <span>Current Escrow State</span>
                            <strong>{escrowStatus.label}</strong>
                        </div>

                        <span
                            className="order-detail-status"
                            style={{ color: escrowStatus.color, background: escrowStatus.bg, borderColor: escrowStatus.border }}
                        >
                            {escrowStatus.icon}
                            {escrowStatus.label}
                        </span>

                        {order.escrow_status === 'waiting_for_payment' && (
                            <Button fullWidth style={{ marginTop: '14px', background: '#fff', color: 'var(--primary-dark)' }}>
                                <CreditCard size={18} />
                                Pay and Secure Order
                            </Button>
                        )}
                    </article>

                    <article className="order-card">
                        <h3 className="order-card-title">
                            <LifeBuoy size={18} />
                            Need Help?
                        </h3>
                        <p className="support-copy">
                            Our support team is available to help with disputes, payment issues, and shipping questions.
                        </p>
                        <Button variant="outline" fullWidth>Contact Support</Button>
                    </article>
                </aside>
            </div>

            <style>{`
                .order-detail-page {
                    animation: orderDetailPageIn 0.5s cubic-bezier(0.16,1,0.3,1) both;
                }

                .order-detail-back {
                    display: inline-flex;
                    align-items: center;
                    gap: 6px;
                    color: var(--text-muted);
                    margin-bottom: 16px;
                    font-weight: 600;
                    text-decoration: none;
                    transition: color 0.2s ease;
                }

                .order-detail-back:hover {
                    color: var(--primary);
                }

                .order-detail-layout {
                    display: grid;
                    grid-template-columns: minmax(0, 1.65fr) minmax(300px, 1fr);
                    gap: 18px;
                    align-items: start;
                }

                .order-detail-main,
                .order-detail-side {
                    display: flex;
                    flex-direction: column;
                    gap: 14px;
                }

                .order-detail-hero,
                .order-card,
                .escrow-card {
                    background: #fff;
                    border-radius: 18px;
                    border: 1px solid rgba(0,0,0,0.05);
                    box-shadow: 0 4px 22px rgba(15,23,42,0.06);
                    transition: transform 0.24s cubic-bezier(0.22,1,0.36,1), box-shadow 0.24s ease, border-color 0.24s ease;
                    animation: orderCardIn 0.42s cubic-bezier(0.22,1,0.36,1) both;
                }

                .order-detail-hero:hover,
                .order-card:hover,
                .escrow-card:hover {
                    transform: translateY(-2px);
                    border-color: rgba(45,90,39,0.2);
                    box-shadow: 0 14px 32px rgba(15,23,42,0.1);
                }

                .order-detail-hero {
                    padding: 18px;
                    display: flex;
                    align-items: flex-start;
                    justify-content: space-between;
                    gap: 14px;
                }

                .order-detail-hero h1 {
                    margin: 0 0 8px;
                    font-size: 1.65rem;
                    font-weight: 800;
                    color: var(--text-dark);
                }
                .order-detail-role-message {
                    margin: 0 0 10px;
                    color: var(--text-muted);
                    font-size: 0.9rem;
                    line-height: 1.5;
                    max-width: 680px;
                }

                .order-detail-hero-meta {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 10px;
                }

                .order-detail-hero-meta span {
                    display: inline-flex;
                    align-items: center;
                    gap: 5px;
                    color: var(--text-muted);
                    font-size: 0.82rem;
                    font-weight: 500;
                }

                .order-detail-status {
                    display: inline-flex;
                    align-items: center;
                    gap: 6px;
                    border: 1px solid;
                    border-radius: 999px;
                    padding: 5px 10px;
                    font-size: 0.74rem;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 0.03em;
                    white-space: nowrap;
                }

                .order-card {
                    padding: 18px;
                }

                .order-card-title {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    margin: 0 0 14px;
                    font-size: 1rem;
                    font-weight: 700;
                    color: var(--text-dark);
                }

                .order-item-list {
                    display: flex;
                    flex-direction: column;
                }

                .order-item-row {
                    display: flex;
                    justify-content: space-between;
                    gap: 10px;
                    padding: 11px 0;
                    border-bottom: 1px solid rgba(0,0,0,0.06);
                }

                .order-item-row:last-child {
                    border-bottom: 0;
                }

                .order-item-name {
                    margin: 0 0 3px;
                    font-weight: 650;
                    color: var(--text-dark);
                }

                .order-item-meta {
                    margin: 0;
                    font-size: 0.8rem;
                    color: var(--text-muted);
                }

                .order-item-price-wrap {
                    text-align: right;
                }

                .order-item-total {
                    margin: 0 0 3px;
                    font-weight: 700;
                    color: var(--text-dark);
                }

                .order-total-row {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-top: 12px;
                    padding-top: 12px;
                    border-top: 1px solid rgba(0,0,0,0.08);
                    font-size: 1.04rem;
                    font-weight: 700;
                }

                .order-total-row strong {
                    color: var(--primary);
                }

                .shipment-header {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    gap: 10px;
                    margin-bottom: 12px;
                    flex-wrap: wrap;
                }

                .shipment-link {
                    display: inline-flex;
                    align-items: center;
                    gap: 4px;
                    text-decoration: none;
                    color: var(--primary);
                    font-size: 0.82rem;
                    font-weight: 700;
                }

                .shipment-body {
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                }

                .shipment-id {
                    margin: 0;
                    font-size: 0.82rem;
                    color: var(--text-muted);
                    font-weight: 600;
                }

                .escrow-card {
                    background: linear-gradient(145deg, var(--primary-dark), #123129);
                    color: #fff;
                    padding: 20px;
                }

                .escrow-card h3 {
                    margin: 0 0 10px;
                    font-size: 1rem;
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                }

                .escrow-card p {
                    margin: 0 0 12px;
                    font-size: 0.84rem;
                    line-height: 1.5;
                    color: rgba(255,255,255,0.82);
                }

                .escrow-state {
                    border: 1px solid rgba(255,255,255,0.18);
                    background: rgba(255,255,255,0.08);
                    border-radius: 12px;
                    padding: 10px 12px;
                    margin-bottom: 12px;
                }

                .escrow-state span {
                    display: block;
                    font-size: 0.68rem;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    color: rgba(255,255,255,0.72);
                    margin-bottom: 2px;
                    font-weight: 700;
                }

                .escrow-state strong {
                    font-size: 0.9rem;
                    letter-spacing: 0.01em;
                }

                .support-copy {
                    margin: 0 0 14px;
                    color: var(--text-muted);
                    font-size: 0.86rem;
                    line-height: 1.5;
                }

                @keyframes orderDetailPageIn {
                    from { opacity: 0; transform: translateY(14px); }
                    to { opacity: 1; transform: translateY(0); }
                }

                @keyframes orderCardIn {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }

                @media (max-width: 1024px) {
                    .order-detail-layout {
                        grid-template-columns: 1fr;
                    }
                }

                @media (max-width: 640px) {
                    .order-detail-hero {
                        flex-direction: column;
                    }

                    .order-detail-hero h1 {
                        font-size: 1.4rem;
                    }

                    .order-item-row {
                        flex-direction: column;
                    }

                    .order-item-price-wrap {
                        text-align: left;
                    }
                }

                @media (prefers-reduced-motion: reduce) {
                    .order-detail-page,
                    .order-detail-hero,
                    .order-card,
                    .escrow-card,
                    .order-detail-back {
                        animation: none !important;
                        transition: none !important;
                    }
                }
            `}</style>
        </div>
    );
};

