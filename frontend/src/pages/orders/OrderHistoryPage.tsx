import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../../api/client';
import { useAuthStore } from '../../store/authStore';
import { Package, Clock, CheckCircle2, AlertCircle, ShoppingCart, ArrowUpRight, Store, Box, CalendarDays } from 'lucide-react';
import { reportApiError } from '../../lib/identityError';

interface Order {
    id: string;
    total_amount: string;
    status: 'draft' | 'pending' | 'confirmed' | 'cancelled' | 'fulfilled' | 'delivered';
    created_at: string;
    item_count: number;
    seller_name: string;
}

interface StatusInfo {
    label: string;
    color: string;
    bg: string;
    border: string;
    icon: React.ReactNode;
}

const getStatusInfo = (status: string): StatusInfo => {
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
                icon: <Package size={14} />
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
        case 'draft':
            return {
                label: 'Draft',
                color: 'var(--text-muted)',
                bg: 'rgba(148,163,184,0.15)',
                border: 'rgba(148,163,184,0.28)',
                icon: <Clock size={14} />
            };
        default:
            return {
                label: status.replace(/_/g, ' '),
                color: 'var(--text-muted)',
                bg: 'rgba(148,163,184,0.15)',
                border: 'rgba(148,163,184,0.28)',
                icon: <Clock size={14} />
            };
    }
};

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

const shortOrderId = (id: string) => id.slice(0, 8).toUpperCase();

const getRoleContent = (role?: string) => {
    if (role === 'seller') {
        return {
            title: 'Sales Orders',
            subtitle: 'Review buyer purchases, confirm fulfillment, and track delivery completion.',
            emptyTitle: 'No sales orders yet',
            emptyDescription: 'Buyer orders will appear here as soon as customers place them.'
        };
    }

    if (role === 'transporter') {
        return {
            title: 'Delivery Orders',
            subtitle: 'Monitor assigned order deliveries and keep shipment progress up to date.',
            emptyTitle: 'No delivery orders yet',
            emptyDescription: 'Assigned delivery orders will appear here once shipments are routed to you.'
        };
    }

    return {
        title: 'Your Orders',
        subtitle: 'Track every purchase from placement to final delivery.',
        emptyTitle: 'No orders yet',
        emptyDescription: 'Your purchases will appear here once you place your first order.'
    };
};

export const OrderHistoryPage: React.FC = () => {
    const [orders, setOrders] = useState<Order[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const { user } = useAuthStore();

    useEffect(() => {
        void fetchOrders();
    }, [user?.role]);

    const fetchOrders = async () => {
        setIsLoading(true);
        try {
            const endpoint = user?.role === 'seller' ? '/orders/seller/' : '/orders/';
            const response = await api.get(endpoint);
            setOrders(response.data.results || response.data || []);
        } catch (err: unknown) {
            reportApiError('Order History Load Failed', err);
        } finally {
            setIsLoading(false);
        }
    };

    const summary = useMemo(() => {
        const delivered = orders.filter((order) => order.status === 'delivered').length;
        const active = orders.filter((order) => !['delivered', 'cancelled'].includes(order.status)).length;
        return { delivered, active };
    }, [orders]);
    const roleContent = getRoleContent(user?.role);

    return (
        <div className="container orders-page">
            <header className="orders-hero">
                <div>
                    <h1 className="orders-title">{roleContent.title}</h1>
                    <p className="orders-subtitle">{roleContent.subtitle}</p>
                </div>
                <div className="orders-badges">
                    <span className="orders-pill">{orders.length} total</span>
                    <span className="orders-pill orders-pill-muted">{summary.active} active</span>
                    <span className="orders-pill orders-pill-success">{summary.delivered} delivered</span>
                </div>
            </header>

            <section className="orders-list" aria-live="polite">
                {isLoading ? (
                    Array.from({ length: 4 }).map((_, index) => (
                        <div key={index} className="order-skeleton" />
                    ))
                ) : orders.length > 0 ? (
                    orders.map((order, index) => {
                        const status = getStatusInfo(order.status);
                        return (
                            <Link
                                key={order.id}
                                to={`/orders/${order.id}`}
                                className="order-link"
                                style={{ animationDelay: `${index * 40}ms` }}
                            >
                                <article className="order-card" style={{ '--status-color': status.color } as React.CSSProperties}>
                                    <div className="order-icon-wrap">
                                        <ShoppingCart size={20} />
                                    </div>

                                    <div className="order-content">
                                        <div className="order-heading-row">
                                            <h2 className="order-id">Order #{shortOrderId(order.id)}</h2>
                                            <span className="order-date">
                                                <CalendarDays size={13} />
                                                {formatDate(order.created_at)}
                                            </span>
                                        </div>

                                        <div className="order-meta-row">
                                            <span className="order-meta-item">
                                                <Box size={13} />
                                                {order.item_count} items
                                            </span>
                                            <span className="order-meta-item">
                                                <Store size={13} />
                                                {order.seller_name || 'Marketplace Seller'}
                                            </span>
                                        </div>
                                    </div>

                                    <div className="order-right">
                                        <div className="order-price">{formatCurrency(order.total_amount)}</div>
                                        <span
                                            className="order-status"
                                            style={{
                                                color: status.color,
                                                background: status.bg,
                                                borderColor: status.border
                                            }}
                                        >
                                            {status.icon}
                                            {status.label}
                                        </span>
                                    </div>

                                    <div className="order-open-icon">
                                        <ArrowUpRight size={18} />
                                    </div>
                                </article>
                            </Link>
                        );
                    })
                ) : (
                    <div className="orders-empty">
                        <div className="orders-empty-icon">
                            <Package size={56} />
                        </div>
                        <h3>{roleContent.emptyTitle}</h3>
                        <p>{roleContent.emptyDescription}</p>
                    </div>
                )}
            </section>

            <style>{`
                .orders-page {
                    animation: orderPageIn 0.5s cubic-bezier(0.16,1,0.3,1) both;
                }

                .orders-hero {
                    display: flex;
                    align-items: flex-end;
                    justify-content: space-between;
                    gap: 20px;
                    flex-wrap: wrap;
                    margin-bottom: 24px;
                }

                .orders-title {
                    margin: 0 0 6px;
                    font-size: 2rem;
                    font-weight: 800;
                    letter-spacing: -0.4px;
                    color: var(--text-dark);
                }

                .orders-subtitle {
                    margin: 0;
                    color: var(--text-muted);
                    font-size: 0.95rem;
                }

                .orders-badges {
                    display: flex;
                    gap: 8px;
                    flex-wrap: wrap;
                }

                .orders-pill {
                    background: rgba(45,90,39,0.1);
                    color: var(--primary);
                    border: 1px solid rgba(45,90,39,0.18);
                    border-radius: 999px;
                    padding: 6px 12px;
                    font-size: 0.78rem;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 0.04em;
                }

                .orders-pill-muted {
                    background: rgba(15,23,42,0.06);
                    border-color: rgba(15,23,42,0.12);
                    color: var(--text-muted);
                }

                .orders-pill-success {
                    background: rgba(16,185,129,0.1);
                    border-color: rgba(16,185,129,0.2);
                    color: var(--success);
                }

                .orders-list {
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                }

                .order-link {
                    text-decoration: none;
                    color: inherit;
                    opacity: 0;
                    animation: orderCardIn 0.4s cubic-bezier(0.22,1,0.36,1) both;
                }

                .order-card {
                    position: relative;
                    background: #fff;
                    border: 1px solid rgba(0,0,0,0.05);
                    border-radius: 18px;
                    padding: 18px;
                    box-shadow: 0 4px 22px rgba(15,23,42,0.06);
                    display: grid;
                    grid-template-columns: auto 1fr auto auto;
                    align-items: center;
                    gap: 14px;
                    transition: transform 0.24s cubic-bezier(0.22,1,0.36,1), box-shadow 0.24s ease, border-color 0.24s ease;
                }

                .order-card::before {
                    content: '';
                    position: absolute;
                    left: 0;
                    top: 14px;
                    bottom: 14px;
                    width: 4px;
                    background: var(--status-color);
                    border-radius: 4px;
                    opacity: 0.9;
                }

                .order-link:hover .order-card {
                    transform: translateY(-2px);
                    border-color: rgba(45,90,39,0.2);
                    box-shadow: 0 14px 32px rgba(15,23,42,0.1);
                }

                .order-icon-wrap {
                    width: 42px;
                    height: 42px;
                    border-radius: 12px;
                    background: rgba(45,90,39,0.08);
                    color: var(--primary);
                    display: grid;
                    place-items: center;
                    margin-left: 8px;
                    flex-shrink: 0;
                }

                .order-content {
                    min-width: 0;
                }

                .order-heading-row {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    flex-wrap: wrap;
                    margin-bottom: 4px;
                }

                .order-id {
                    margin: 0;
                    font-size: 1.02rem;
                    font-weight: 750;
                    color: var(--text-dark);
                }

                .order-date {
                    display: inline-flex;
                    align-items: center;
                    gap: 5px;
                    color: var(--text-muted);
                    font-size: 0.8rem;
                    font-weight: 600;
                }

                .order-meta-row {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    flex-wrap: wrap;
                }

                .order-meta-item {
                    display: inline-flex;
                    align-items: center;
                    gap: 5px;
                    color: var(--text-muted);
                    font-size: 0.82rem;
                    font-weight: 500;
                }

                .order-right {
                    display: flex;
                    flex-direction: column;
                    align-items: flex-end;
                    gap: 6px;
                }

                .order-price {
                    font-size: 1.08rem;
                    font-weight: 800;
                    color: var(--text-dark);
                    white-space: nowrap;
                }

                .order-status {
                    display: inline-flex;
                    align-items: center;
                    gap: 6px;
                    border: 1px solid;
                    border-radius: 999px;
                    padding: 4px 10px;
                    font-size: 0.74rem;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 0.03em;
                    white-space: nowrap;
                }

                .order-open-icon {
                    width: 28px;
                    height: 28px;
                    border-radius: 8px;
                    background: rgba(0,0,0,0.04);
                    color: var(--text-muted);
                    display: grid;
                    place-items: center;
                    transition: transform 0.2s ease, background 0.2s ease;
                }

                .order-link:hover .order-open-icon {
                    transform: translate(2px, -2px);
                    background: rgba(45,90,39,0.12);
                    color: var(--primary);
                }

                .order-skeleton {
                    height: 92px;
                    border-radius: 16px;
                    background: linear-gradient(110deg, rgba(0,0,0,0.04) 20%, rgba(0,0,0,0.08) 35%, rgba(0,0,0,0.04) 50%);
                    background-size: 220% 100%;
                    animation: orderShimmer 1.2s linear infinite;
                }

                .orders-empty {
                    text-align: center;
                    padding: 56px 20px;
                    background: #fff;
                    border: 1px dashed rgba(0,0,0,0.14);
                    border-radius: 18px;
                }

                .orders-empty-icon {
                    color: rgba(45,90,39,0.25);
                    margin-bottom: 14px;
                }

                .orders-empty h3 {
                    margin: 0 0 8px;
                    color: var(--text-dark);
                }

                .orders-empty p {
                    margin: 0 0 18px;
                    color: var(--text-muted);
                }

                @keyframes orderPageIn {
                    from { opacity: 0; transform: translateY(14px); }
                    to { opacity: 1; transform: translateY(0); }
                }

                @keyframes orderCardIn {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }

                @keyframes orderShimmer {
                    to { background-position-x: -220%; }
                }

                @media (max-width: 900px) {
                    .order-card {
                        grid-template-columns: auto 1fr auto;
                        grid-template-areas:
                            'icon content open'
                            'icon right open';
                    }

                    .order-icon-wrap { grid-area: icon; }
                    .order-content { grid-area: content; }
                    .order-right {
                        grid-area: right;
                        align-items: flex-start;
                        margin-left: 8px;
                    }
                    .order-open-icon { grid-area: open; }
                }

                @media (max-width: 640px) {
                    .orders-title {
                        font-size: 1.75rem;
                    }

                    .order-card {
                        padding: 14px;
                        gap: 10px;
                    }

                    .order-id {
                        font-size: 0.95rem;
                    }
                }

                @media (prefers-reduced-motion: reduce) {
                    .orders-page,
                    .order-link,
                    .order-card,
                    .order-open-icon,
                    .order-skeleton {
                        animation: none !important;
                        transition: none !important;
                    }

                    .order-link {
                        opacity: 1;
                    }
                }
            `}</style>
        </div>
    );
};
