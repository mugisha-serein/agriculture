import React, { useMemo, useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../../api/client';
import { useAuthStore } from '../../store/authStore';
import { Button, Badge } from '../../components/ui';
import { Truck, MapPin, ArrowRight, Package, Box, CheckCircle2, Clock, AlertTriangle } from 'lucide-react';
import { reportApiError } from '../../lib/identityError';

interface Shipment {
    id: string;
    shipment_reference: string;
    status: string;
    origin: string;
    destination: string;
    created_at: string;
    order_number: string;
}

interface StatusConfig {
    variant: 'warning' | 'primary' | 'success' | 'error' | 'neutral';
    label: string;
    icon: React.ReactNode;
}

const getStatusConfig = (status: string): StatusConfig => {
    const map: Record<string, StatusConfig> = {
        pending_assignment: { variant: 'warning', label: 'Unassigned', icon: <Clock size={14} /> },
        assigned: { variant: 'primary', label: 'Assigned', icon: <Truck size={14} /> },
        picked_up: { variant: 'primary', label: 'Picked Up', icon: <Truck size={14} /> },
        in_transit: { variant: 'primary', label: 'In Transit', icon: <Truck size={14} /> },
        delivered: { variant: 'success', label: 'Delivered', icon: <CheckCircle2 size={14} /> },
        cancelled: { variant: 'error', label: 'Cancelled', icon: <AlertTriangle size={14} /> }
    };
    const normalized = status?.toLowerCase();
    return map[normalized] || { variant: 'neutral', label: normalized || 'Unknown', icon: <Box size={14} /> };
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

export const ShipmentListPage: React.FC = () => {
    const [shipments, setShipments] = useState<Shipment[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const { user } = useAuthStore();

    useEffect(() => {
        fetchShipments();
    }, []);

    const fetchShipments = async () => {
        setIsLoading(true);
        try {
            const response = await api.get('/logistics/shipments/');
            setShipments(response.data.results || response.data || []);
        } catch (err: unknown) {
            reportApiError('Shipment List Load Failed', err);
        } finally {
            setIsLoading(false);
        }
    };

    const subtitle = useMemo(() => {
        if (user?.role === 'seller') {
            return 'Track shipments for your sales and keep buyers informed.';
        }
        if (user?.role === 'transporter') {
            return 'Manage assigned logistics tasks and update delivery progress.';
        }
        return 'Review shipment activity and delivery progress.';
    }, [user?.role]);

    const summary = useMemo(() => {
        const total = shipments.length;
        const delivered = shipments.filter((shipment) => shipment.status?.toLowerCase() === 'delivered').length;
        const active = shipments.filter((shipment) => !['delivered', 'cancelled'].includes(shipment.status?.toLowerCase())).length;
        return { total, delivered, active };
    }, [shipments]);

    return (
        <div className="container shipments-page">
            <header className="shipments-hero">
                <div>
                    <h1 className="shipments-title">Shipments</h1>
                    <p className="shipments-subtitle">{subtitle}</p>
                </div>
                <div className="shipments-actions">
                    <div className="shipments-badges">
                        <span className="shipments-pill">{summary.total} total</span>
                        <span className="shipments-pill shipments-pill-primary">{summary.active} active</span>
                        <span className="shipments-pill shipments-pill-success">{summary.delivered} delivered</span>
                    </div>
                    <span className="shipments-pill shipments-pill-highlight">
                        <Truck size={16} /> Real-time Logistics
                    </span>
                </div>
            </header>

            <section className="shipments-list">
                {isLoading ? (
                    Array.from({ length: 4 }).map((_, i) => (
                        <div key={i} className="shipment-skeleton">
                            <div className="shipment-skeleton-bar" />
                        </div>
                    ))
                ) : shipments.length > 0 ? (
                    shipments.map((shipment, index) => {
                        const statusConfig = getStatusConfig(shipment.status);
                        return (
                            <article key={shipment.id} className="shipment-card" style={{ animationDelay: `${index * 0.05}s` }}>
                                <div className="shipment-icon">
                                    <Box size={22} />
                                </div>
                                <div className="shipment-main">
                                    <div className="shipment-header">
                                        <div>
                                            <div className="shipment-id">#{shipment.shipment_reference || shipment.id}</div>
                                            <div className="shipment-date">{formatDate(shipment.created_at)}</div>
                                        </div>
                                        <span className="shipment-status">
                                            {statusConfig.icon}
                                            <Badge variant={statusConfig.variant}>{statusConfig.label}</Badge>
                                        </span>
                                    </div>
                                    <div className="shipment-route">
                                        <span><MapPin size={14} /> {shipment.origin}</span>
                                        <ArrowRight size={14} />
                                        <span>{shipment.destination}</span>
                                    </div>
                                    <div className="shipment-meta">
                                        Order {shipment.order_number || 'N/A'}
                                    </div>
                                </div>
                                <Link to={`/shipments/${shipment.id}`} className="shipment-track">
                                    <Button variant="outline" size="sm">
                                        Track
                                        <ArrowRight size={16} />
                                    </Button>
                                </Link>
                            </article>
                        );
                    })
                ) : (
                    <div className="shipments-empty">
                        <Package size={56} />
                        <h3>No shipments found</h3>
                        <p>When items are ready for transport, they will appear here.</p>
                    </div>
                )}
            </section>

            <style>{`
                .shipments-page {
                    animation: shipmentPageIn 0.45s cubic-bezier(0.16, 1, 0.3, 1) both;
                }

                .shipments-hero {
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-end;
                    gap: 14px;
                    margin-bottom: 26px;
                    flex-wrap: wrap;
                }

                .shipments-title {
                    margin: 0 0 8px;
                    font-size: 2rem;
                    font-weight: 800;
                    color: var(--text-dark);
                }

                .shipments-subtitle {
                    margin: 0;
                    color: var(--text-muted);
                    font-size: 0.94rem;
                }

                .shipments-actions {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    flex-wrap: wrap;
                    justify-content: flex-end;
                }

                .shipments-badges {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    flex-wrap: wrap;
                }

                .shipments-pill {
                    display: inline-flex;
                    align-items: center;
                    gap: 6px;
                    padding: 6px 12px;
                    border-radius: 999px;
                    font-size: 0.74rem;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 0.04em;
                    background: rgba(15, 23, 42, 0.06);
                    color: var(--text-muted);
                }

                .shipments-pill-primary {
                    background: rgba(59, 130, 246, 0.12);
                    color: #2563eb;
                }

                .shipments-pill-success {
                    background: rgba(16,185,129,0.12);
                    color: var(--success);
                }

                .shipments-pill-highlight {
                    background: var(--accent-soft);
                    color: var(--primary);
                }

                .shipments-list {
                    display: grid;
                    gap: 16px;
                }

                .shipment-card,
                .shipment-skeleton {
                    background: #fff;
                    border-radius: 18px;
                    border: 1px solid rgba(0,0,0,0.05);
                    box-shadow: 0 4px 22px rgba(15,23,42,0.06);
                    padding: 20px;
                    display: grid;
                    grid-template-columns: auto 1fr auto;
                    gap: 18px;
                    align-items: center;
                    transition: transform 0.24s cubic-bezier(0.22,1,0.36,1), box-shadow 0.24s ease, border-color 0.24s ease;
                }

                .shipment-card {
                    opacity: 0;
                    animation: shipmentCardIn 0.4s cubic-bezier(0.22,1,0.36,1) both;
                }

                .shipment-card:hover {
                    transform: translateY(-2px);
                    border-color: rgba(45,90,39,0.2);
                    box-shadow: 0 14px 32px rgba(15,23,42,0.1);
                }

                .shipment-icon {
                    width: 48px;
                    height: 48px;
                    border-radius: 14px;
                    display: grid;
                    place-items: center;
                    background: rgba(45,90,39,0.1);
                    color: var(--primary);
                }

                .shipment-header {
                    display: flex;
                    align-items: flex-start;
                    justify-content: space-between;
                    gap: 12px;
                    margin-bottom: 8px;
                }

                .shipment-id {
                    font-weight: 800;
                    font-size: 1.1rem;
                    color: var(--text-dark);
                }

                .shipment-date {
                    font-size: 0.8rem;
                    color: var(--text-muted);
                }

                .shipment-status {
                    display: inline-flex;
                    align-items: center;
                    gap: 6px;
                }

                .shipment-route {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    font-size: 0.9rem;
                    color: var(--text-muted);
                }

                .shipment-meta {
                    margin-top: 6px;
                    font-size: 0.82rem;
                    color: var(--text-muted);
                }

                .shipment-track {
                    justify-self: end;
                }

                .shipment-track button {
                    display: inline-flex;
                    align-items: center;
                    gap: 6px;
                }

                .shipment-skeleton {
                    grid-template-columns: 1fr;
                }

                .shipment-skeleton-bar {
                    height: 60px;
                    border-radius: 14px;
                    background: linear-gradient(110deg, rgba(0,0,0,0.04) 20%, rgba(0,0,0,0.08) 35%, rgba(0,0,0,0.04) 50%);
                    background-size: 220% 100%;
                    animation: shipmentShimmer 1.2s linear infinite;
                }

                .shipments-empty {
                    text-align: center;
                    padding: 80px 0;
                    border-radius: 18px;
                    border: 1px dashed rgba(0,0,0,0.14);
                    background: #fff;
                }

                .shipments-empty svg {
                    color: rgba(0,0,0,0.2);
                    margin-bottom: 16px;
                }

                .shipments-empty h3 {
                    margin: 0 0 6px;
                    color: var(--text-dark);
                }

                .shipments-empty p {
                    margin: 0;
                    color: var(--text-muted);
                }

                @keyframes shipmentPageIn {
                    from { opacity: 0; transform: translateY(12px); }
                    to { opacity: 1; transform: translateY(0); }
                }

                @keyframes shipmentCardIn {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }

                @keyframes shipmentShimmer {
                    to { background-position-x: -220%; }
                }

                @media (max-width: 900px) {
                    .shipment-card {
                        grid-template-columns: 1fr;
                    }

                    .shipment-track {
                        justify-self: start;
                    }
                }

                @media (max-width: 720px) {
                    .shipments-title {
                        font-size: 1.7rem;
                    }
                }

                @media (prefers-reduced-motion: reduce) {
                    .shipment-card,
                    .shipment-skeleton {
                        animation: none !important;
                        transition: none !important;
                    }
                }
            `}</style>
        </div>
    );
};
