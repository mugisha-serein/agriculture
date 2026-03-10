import React, { useMemo, useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../../api/client';
import { Button, Badge } from '../../components/ui';
import { Truck, MapPin, CheckCircle2, Clock, ChevronLeft, Package, User, Phone, AlertTriangle, Circle, ArrowRight } from 'lucide-react';
import { reportApiError } from '../../lib/identityError';

interface ShipmentEvent {
    id: string;
    status: string;
    location: string;
    timestamp: string;
    description: string;
}

interface ShipmentDetail {
    id: string;
    order_id: string;
    status: 'pending' | 'in_transit' | 'at_destination' | 'delivered' | 'cancelled';
    origin: string;
    destination: string;
    transporter_name: string;
    transporter_phone: string;
    estimated_delivery?: string;
    events: ShipmentEvent[];
}

interface StatusStyle {
    label: string;
    color: string;
    bg: string;
    border: string;
    icon: React.ReactNode;
}

const getStatusStyle = (status: string): StatusStyle => {
    switch (status) {
        case 'delivered':
            return { label: 'Delivered', color: 'var(--success)', bg: 'rgba(16,185,129,0.12)', border: 'rgba(16,185,129,0.28)', icon: <CheckCircle2 size={20} /> };
        case 'in_transit':
            return { label: 'In Transit', color: 'var(--primary)', bg: 'rgba(45,90,39,0.12)', border: 'rgba(45,90,39,0.28)', icon: <Truck size={20} /> };
        case 'at_destination':
            return { label: 'At Destination', color: 'var(--info)', bg: 'rgba(59,130,246,0.12)', border: 'rgba(59,130,246,0.24)', icon: <MapPin size={20} /> };
        case 'cancelled':
            return { label: 'Cancelled', color: 'var(--error)', bg: 'rgba(239,68,68,0.12)', border: 'rgba(239,68,68,0.24)', icon: <AlertTriangle size={20} /> };
        default:
            return { label: 'Pending', color: 'var(--warning)', bg: 'rgba(245,158,11,0.12)', border: 'rgba(245,158,11,0.24)', icon: <Clock size={20} /> };
    }
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

const formatDateTime = (value: string) => {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit'
    });
};

export const ShipmentTrackingPage: React.FC = () => {
    const { shipmentId } = useParams();
    const [shipment, setShipment] = useState<ShipmentDetail | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        fetchShipmentDetail();
    }, [shipmentId]);

    const fetchShipmentDetail = async () => {
        setIsLoading(true);
        try {
            const response = await api.get(`/logistics/shipments/${shipmentId}/`);
            setShipment(response.data);
        } catch (err: unknown) {
            reportApiError('Shipment Detail Load Failed', err);
        } finally {
            setIsLoading(false);
        }
    };

    const latestEvent = useMemo(() => shipment?.events?.[0], [shipment]);

    if (isLoading) {
        return (
            <div className="container shipment-track-page">
                <div className="shipment-loading">
                    <div className="shipment-loading-bar" />
                    <p>Loading shipment details...</p>
                </div>
            </div>
        );
    }

    if (!shipment) {
        return (
            <div className="container shipment-track-page">
                <div className="shipment-empty">
                    <Package size={52} />
                    <h3>Shipment not found</h3>
                    <p>We could not load that shipment. Please try again.</p>
                    <Link to="/shipments">
                        <Button>Back to Shipments</Button>
                    </Link>
                </div>
            </div>
        );
    }

    const statusStyle = getStatusStyle(shipment.status);

    return (
        <div className="container shipment-track-page">
            <Link to={`/orders/${shipment.order_id}`} className="shipment-back">
                <ChevronLeft size={18} />
                Back to Order
            </Link>

            <div className="shipment-track-layout">
                <section className="shipment-track-main">
                    <header className="shipment-track-hero">
                        <div>
                            <h1>Shipment {shipment.id.slice(0, 8).toUpperCase()}</h1>
                            <p>Order {shipment.order_id}</p>
                        </div>
                        <span className="shipment-track-status" style={{ color: statusStyle.color, background: statusStyle.bg, borderColor: statusStyle.border }}>
                            {statusStyle.icon}
                            {statusStyle.label}
                        </span>
                    </header>

                    <div className="shipment-route-card">
                        <div className="shipment-route-info">
                            <div>
                                <span>Origin</span>
                                <strong>{shipment.origin}</strong>
                            </div>
                            <ArrowRight size={18} />
                            <div>
                                <span>Destination</span>
                                <strong>{shipment.destination}</strong>
                            </div>
                        </div>
                        {shipment.estimated_delivery && (
                            <div className="shipment-eta">
                                <div>Estimated Delivery</div>
                                <strong>{formatDate(shipment.estimated_delivery)}</strong>
                            </div>
                        )}
                    </div>

                    <div className="shipment-timeline">
                        <div className="shipment-timeline-title">
                            <h3>Tracking Timeline</h3>
                            <Badge variant="neutral">{shipment.events.length} updates</Badge>
                        </div>
                        <div className="shipment-timeline-line" />
                        <div className="shipment-timeline-events">
                            {shipment.events.map((event, index) => (
                                <div key={event.id} className="shipment-event" style={{ animationDelay: `${index * 0.06}s` }}>
                                    <div className={`shipment-event-dot ${index === 0 ? 'active' : ''}`}>
                                        {index === 0 ? <CheckCircle2 size={12} /> : <Circle size={10} />}
                                    </div>
                                    <div className="shipment-event-body">
                                        <div className="shipment-event-head">
                                            <span>{event.status.replace(/_/g, ' ')}</span>
                                            <time>{formatDateTime(event.timestamp)}</time>
                                        </div>
                                        <div className="shipment-event-location">
                                            <MapPin size={14} /> {event.location}
                                        </div>
                                        <p>{event.description}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </section>

                <aside className="shipment-track-aside">
                    <div className="shipment-aside-card">
                        <div className="shipment-aside-header">
                            <Package size={18} />
                            Route Info
                        </div>
                        <div className="shipment-aside-body">
                            <div>
                                <span>Origin</span>
                                <strong>{shipment.origin}</strong>
                            </div>
                            <div>
                                <span>Destination</span>
                                <strong>{shipment.destination}</strong>
                            </div>
                            {latestEvent && (
                                <div>
                                    <span>Last Update</span>
                                    <strong>{formatDateTime(latestEvent.timestamp)}</strong>
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="shipment-aside-card">
                        <div className="shipment-aside-header">
                            <User size={18} />
                            Transporter
                        </div>
                        <div className="shipment-aside-body">
                            <div className="shipment-transporter">
                                <div className="shipment-avatar">{shipment.transporter_name?.charAt(0) || 'T'}</div>
                                <div>
                                    <strong>{shipment.transporter_name || 'Assigned transporter'}</strong>
                                    <span>Verified Carrier</span>
                                </div>
                            </div>
                            <Button variant="outline" fullWidth style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <Phone size={18} /> {shipment.transporter_phone || 'Not available'}
                            </Button>
                        </div>
                    </div>
                </aside>
            </div>

            <style>{`
                .shipment-track-page {
                    animation: shipmentTrackIn 0.45s cubic-bezier(0.16, 1, 0.3, 1) both;
                }

                .shipment-back {
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    color: var(--text-muted);
                    margin-bottom: 20px;
                    font-weight: 600;
                    text-decoration: none;
                }

                .shipment-track-layout {
                    display: grid;
                    grid-template-columns: minmax(0, 2.2fr) minmax(0, 1fr);
                    gap: 24px;
                    align-items: start;
                }

                .shipment-track-hero {
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                    gap: 12px;
                    margin-bottom: 18px;
                    animation: shipmentCardIn 0.4s cubic-bezier(0.22,1,0.36,1) both;
                }

                .shipment-track-hero h1 {
                    margin: 0 0 6px;
                    font-size: 1.6rem;
                    color: var(--text-dark);
                }

                .shipment-track-hero p {
                    margin: 0;
                    color: var(--text-muted);
                }

                .shipment-track-status {
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    border: 1px solid;
                    border-radius: 999px;
                    padding: 6px 12px;
                    font-size: 0.78rem;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 0.04em;
                }

                .shipment-route-card {
                    background: #fff;
                    border-radius: 18px;
                    border: 1px solid rgba(0,0,0,0.05);
                    box-shadow: 0 4px 22px rgba(15,23,42,0.06);
                    padding: 18px;
                    margin-bottom: 20px;
                    animation: shipmentCardIn 0.45s cubic-bezier(0.22,1,0.36,1) both;
                    transition: transform 0.24s cubic-bezier(0.22,1,0.36,1), box-shadow 0.24s ease, border-color 0.24s ease;
                }

                .shipment-route-card:hover {
                    transform: translateY(-2px);
                    border-color: rgba(45,90,39,0.2);
                    box-shadow: 0 14px 32px rgba(15,23,42,0.1);
                }

                .shipment-route-info {
                    display: grid;
                    grid-template-columns: 1fr auto 1fr;
                    gap: 12px;
                    align-items: center;
                }

                .shipment-route-info span {
                    display: block;
                    font-size: 0.72rem;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    color: var(--text-muted);
                    margin-bottom: 6px;
                }

                .shipment-route-info strong {
                    color: var(--text-dark);
                }

                .shipment-eta {
                    margin-top: 14px;
                    padding: 12px;
                    border-radius: 12px;
                    background: var(--accent-soft);
                    color: var(--primary);
                    text-align: center;
                }

                .shipment-eta strong {
                    display: block;
                    font-size: 1rem;
                    color: var(--primary);
                }

                .shipment-timeline {
                    background: #fff;
                    border-radius: 18px;
                    border: 1px solid rgba(0,0,0,0.05);
                    box-shadow: 0 4px 22px rgba(15,23,42,0.06);
                    padding: 20px;
                    position: relative;
                    animation: shipmentCardIn 0.48s cubic-bezier(0.22,1,0.36,1) both;
                    transition: transform 0.24s cubic-bezier(0.22,1,0.36,1), box-shadow 0.24s ease, border-color 0.24s ease;
                }

                .shipment-timeline:hover {
                    transform: translateY(-2px);
                    border-color: rgba(45,90,39,0.2);
                    box-shadow: 0 14px 32px rgba(15,23,42,0.1);
                }

                .shipment-timeline-title {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    margin-bottom: 16px;
                }

                .shipment-timeline-title h3 {
                    margin: 0;
                    font-size: 1.05rem;
                    color: var(--text-dark);
                }

                .shipment-timeline-line {
                    position: absolute;
                    left: 24px;
                    top: 70px;
                    bottom: 24px;
                    width: 2px;
                    background: rgba(0,0,0,0.08);
                }

                .shipment-timeline-events {
                    display: flex;
                    flex-direction: column;
                    gap: 18px;
                }

                .shipment-event {
                    display: grid;
                    grid-template-columns: 24px 1fr;
                    gap: 16px;
                    position: relative;
                    opacity: 0;
                    animation: shipmentEventIn 0.32s cubic-bezier(0.22,1,0.36,1) both;
                }

                .shipment-event-dot {
                    width: 24px;
                    height: 24px;
                    border-radius: 50%;
                    background: #fff;
                    border: 2px solid rgba(45,90,39,0.2);
                    display: grid;
                    place-items: center;
                    color: var(--primary);
                    z-index: 1;
                }

                .shipment-event-dot.active {
                    background: var(--primary);
                    color: #fff;
                    border-color: rgba(45,90,39,0.4);
                }

                .shipment-event-head {
                    display: flex;
                    justify-content: space-between;
                    gap: 10px;
                    font-weight: 700;
                }

                .shipment-event-head span {
                    text-transform: capitalize;
                }

                .shipment-event-head time {
                    font-size: 0.82rem;
                    color: var(--text-muted);
                }

                .shipment-event-location {
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    color: var(--text-muted);
                    font-size: 0.88rem;
                    margin: 6px 0;
                }

                .shipment-event-body p {
                    margin: 0;
                    color: var(--text-dark);
                    line-height: 1.5;
                }

                .shipment-track-aside {
                    display: flex;
                    flex-direction: column;
                    gap: 18px;
                }

                .shipment-aside-card {
                    background: #fff;
                    border-radius: 18px;
                    border: 1px solid rgba(0,0,0,0.05);
                    box-shadow: 0 4px 22px rgba(15,23,42,0.06);
                    padding: 18px;
                    animation: shipmentCardIn 0.5s cubic-bezier(0.22,1,0.36,1) both;
                    transition: transform 0.24s cubic-bezier(0.22,1,0.36,1), box-shadow 0.24s ease, border-color 0.24s ease;
                }

                .shipment-aside-card:hover {
                    transform: translateY(-2px);
                    border-color: rgba(45,90,39,0.2);
                    box-shadow: 0 14px 32px rgba(15,23,42,0.1);
                }

                .shipment-aside-header {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    font-weight: 700;
                    color: var(--text-dark);
                    margin-bottom: 12px;
                }

                .shipment-aside-body {
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                    color: var(--text-muted);
                    font-size: 0.9rem;
                }

                .shipment-aside-body span {
                    display: block;
                    font-size: 0.72rem;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    margin-bottom: 4px;
                }

                .shipment-aside-body strong {
                    color: var(--text-dark);
                    font-size: 0.94rem;
                }

                .shipment-transporter {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }

                .shipment-avatar {
                    width: 44px;
                    height: 44px;
                    border-radius: 50%;
                    background: var(--primary-dark);
                    color: #fff;
                    display: grid;
                    place-items: center;
                    font-weight: 700;
                }

                .shipment-transporter span {
                    display: block;
                    font-size: 0.8rem;
                    color: var(--text-muted);
                    text-transform: none;
                    margin-top: 2px;
                }

                .shipment-loading {
                    background: #fff;
                    border-radius: 18px;
                    border: 1px solid rgba(0,0,0,0.05);
                    box-shadow: 0 4px 22px rgba(15,23,42,0.06);
                    padding: 24px;
                }

                .shipment-loading-bar {
                    height: 48px;
                    border-radius: 14px;
                    background: linear-gradient(110deg, rgba(0,0,0,0.04) 20%, rgba(0,0,0,0.08) 35%, rgba(0,0,0,0.04) 50%);
                    background-size: 220% 100%;
                    animation: shipmentShimmer 1.2s linear infinite;
                    margin-bottom: 12px;
                }

                .shipment-empty {
                    text-align: center;
                    padding: 80px 0;
                    border-radius: 18px;
                    border: 1px dashed rgba(0,0,0,0.14);
                    background: #fff;
                }

                .shipment-empty svg {
                    color: rgba(0,0,0,0.2);
                    margin-bottom: 16px;
                }

                .shipment-empty h3 {
                    margin: 0 0 6px;
                    color: var(--text-dark);
                }

                .shipment-empty p {
                    margin: 0 0 16px;
                    color: var(--text-muted);
                }

                @keyframes shipmentTrackIn {
                    from { opacity: 0; transform: translateY(12px); }
                    to { opacity: 1; transform: translateY(0); }
                }

                @keyframes shipmentCardIn {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }

                @keyframes shipmentEventIn {
                    from { opacity: 0; transform: translateY(8px); }
                    to { opacity: 1; transform: translateY(0); }
                }

                @keyframes shipmentShimmer {
                    to { background-position-x: -220%; }
                }

                @media (max-width: 980px) {
                    .shipment-track-layout {
                        grid-template-columns: 1fr;
                    }

                    .shipment-track-status {
                        align-self: flex-start;
                    }
                }

                @media (max-width: 640px) {
                    .shipment-track-hero {
                        flex-direction: column;
                    }

                    .shipment-track-hero h1 {
                        font-size: 1.4rem;
                    }

                    .shipment-route-info {
                        grid-template-columns: 1fr;
                        gap: 8px;
                    }

                    .shipment-timeline-line {
                        left: 18px;
                    }
                }

                @media (prefers-reduced-motion: reduce) {
                    .shipment-track-page,
                    .shipment-track-hero,
                    .shipment-route-card,
                    .shipment-timeline,
                    .shipment-aside-card {
                        animation: none !important;
                        transition: none !important;
                    }
                }
            `}</style>
        </div>
    );
};
