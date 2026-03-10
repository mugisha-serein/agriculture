import React from 'react';
import { ShoppingCart, AlertTriangle, AlertCircle, CreditCard, Box } from 'lucide-react';

interface ActivityItem {
    type: string;
    description: string;
    timestamp: string;
}

interface ActivityFeedProps {
    activities: ActivityItem[];
}

export const ActivityFeed: React.FC<ActivityFeedProps> = ({ activities }) => {
    const getIcon = (type: string) => {
        switch (type) {
            case 'sale': return <ShoppingCart size={16} />;
            case 'stock_low': return <AlertTriangle size={16} />;
            case 'out_of_stock': return <AlertCircle size={16} />;
            case 'transaction': return <CreditCard size={16} />;
            case 'shipment': return <Box size={16} />;
            default: return <Box size={16} />;
        }
    };

    const getColor = (type: string) => {
        switch (type) {
            case 'sale': return 'var(--primary)';
            case 'stock_low': return 'var(--warning)';
            case 'out_of_stock': return 'var(--error)';
            case 'transaction': return 'var(--accent)';
            case 'shipment': return 'var(--info)';
            default: return 'var(--text-muted)';
        }
    };

    const getLabel = (type: string) => {
        switch (type) {
            case 'sale': return 'Sale';
            case 'stock_low': return 'Low Stock';
            case 'out_of_stock': return 'Out of Stock';
            case 'transaction': return 'Transaction';
            case 'shipment': return 'Shipment';
            default: return 'Activity';
        }
    };

    const formatTimestamp = (value: string) => {
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return value;
        return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: 'numeric',
            minute: '2-digit'
        });
    };

    return (
        <div className="dashboard-activity-card">
            <div className="dashboard-activity-header">
                <h3 className="dashboard-activity-title">Recent Activity</h3>
                <span className="dashboard-activity-count">{activities.length} events</span>
            </div>

            <div className="dashboard-activity-list">
                {activities.map((activity, i) => {
                    const color = getColor(activity.type);
                    const label = getLabel(activity.type);

                    return (
                        <article
                            key={`${activity.type}-${activity.timestamp}-${i}`}
                            className="dashboard-activity-item"
                            style={{
                                '--activity-color': color,
                                animationDelay: `${i * 55}ms`
                            } as React.CSSProperties}
                        >
                            <div className="dashboard-activity-icon">
                                {getIcon(activity.type)}
                            </div>
                            <div className="dashboard-activity-body">
                                <p className="dashboard-activity-description">{activity.description}</p>
                                <div className="dashboard-activity-meta">
                                    <span className="dashboard-activity-kind">{label}</span>
                                    <time dateTime={activity.timestamp} className="dashboard-activity-time">
                                        {formatTimestamp(activity.timestamp)}
                                    </time>
                                </div>
                            </div>
                        </article>
                    );
                })}

                {activities.length === 0 && (
                    <p className="dashboard-activity-empty">No recent activity.</p>
                )}
            </div>

            <style>{`
                .dashboard-activity-card {
                    background: #fff;
                    border-radius: 20px;
                    border: 1px solid rgba(0,0,0,0.05);
                    box-shadow: 0 2px 4px rgba(15,23,42,0.06);
                    padding: 26px;
                    height: 100%;
                    transition: transform 0.24s cubic-bezier(0.22,1,0.36,1), 0.24s ease, border-color 0.24s ease;
                    animation: activityCardIn 0.45s cubic-bezier(0.22,1,0.36,1) both;
                }

                .dashboard-activity-header {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    gap: 12px;
                    margin-bottom: 20px;
                }

                .dashboard-activity-title {
                    font-size: 1.05rem;
                    font-weight: 700;
                    color: var(--text-dark);
                    margin: 0;
                }

                .dashboard-activity-count {
                    background: rgba(45,90,39,0.08);
                    color: var(--primary);
                    border: 1px solid rgba(45,90,39,0.16);
                    border-radius: 999px;
                    padding: 4px 10px;
                    font-size: 0.74rem;
                    font-weight: 700;
                    letter-spacing: 0.04em;
                    text-transform: uppercase;
                    white-space: nowrap;
                }

                .dashboard-activity-list {
                    display: flex;
                    flex-direction: column;
                    gap: 10px;
                }

                .dashboard-activity-item {
                    display: flex;
                    gap: 12px;
                    border-radius: 12px;
                    padding: 10px;
                    transition: background 0.2s ease, transform 0.2s ease;
                    opacity: 0;
                    animation: activityItemIn 0.35s cubic-bezier(0.22,1,0.36,1) both;
                }

                .dashboard-activity-item:hover {
                    background: rgba(16,185,129,0.04);
                    transform: translateX(2px);
                }

                .dashboard-activity-icon {
                    position: relative;
                    width: 34px;
                    height: 34px;
                    border-radius: 9px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: var(--activity-color);
                    flex-shrink: 0;
                    overflow: hidden;
                }

                .dashboard-activity-icon::before {
                    content: '';
                    position: absolute;
                    inset: 0;
                    border-radius: inherit;
                    background: var(--activity-color);
                    opacity: 0.14;
                }

                .dashboard-activity-icon > * {
                    position: relative;
                    z-index: 1;
                }

                .dashboard-activity-body {
                    min-width: 0;
                    flex: 1;
                }

                .dashboard-activity-description {
                    margin: 0 0 6px;
                    font-size: 0.9rem;
                    line-height: 1.45;
                    color: var(--text-dark);
                    font-weight: 500;
                }

                .dashboard-activity-meta {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    flex-wrap: wrap;
                }

                .dashboard-activity-kind {
                    background: rgba(15,23,42,0.06);
                    color: var(--text-muted);
                    border-radius: 999px;
                    padding: 2px 8px;
                    font-size: 0.68rem;
                    font-weight: 700;
                    letter-spacing: 0.03em;
                    text-transform: uppercase;
                }

                .dashboard-activity-time {
                    font-size: 0.76rem;
                    color: var(--text-muted);
                    font-weight: 500;
                }

                .dashboard-activity-empty {
                    text-align: center;
                    color: var(--text-muted);
                    padding: 36px 0;
                    border: 1px dashed rgba(0,0,0,0.12);
                    border-radius: 12px;
                    background: rgba(0,0,0,0.02);
                    margin: 0;
                }

                @keyframes activityCardIn {
                    from { opacity: 0; transform: translateY(12px); }
                    to { opacity: 1; transform: translateY(0); }
                }

                @keyframes activityItemIn {
                    from { opacity: 0; transform: translateY(8px); }
                    to { opacity: 1; transform: translateY(0); }
                }

                @media (max-width: 640px) {
                    .dashboard-activity-card {
                        padding: 20px;
                    }

                    .dashboard-activity-title {
                        font-size: 1rem;
                    }
                }

                @media (prefers-reduced-motion: reduce) {
                    .dashboard-activity-card,
                    .dashboard-activity-item {
                        transition: none !important;
                        animation: none !important;
                        opacity: 1;
                        transform: none !important;
                    }
                }
            `}</style>
        </div>
    );
};
