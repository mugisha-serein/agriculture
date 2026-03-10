import React from 'react';

interface StatsCardProps {
    title: string;
    value: string | number;
    icon: React.ReactNode;
    color?: string;
}

export const StatsCard: React.FC<StatsCardProps> = ({ title, value, icon, color = 'var(--primary)' }) => (
    <div
        className="dashboard-stat-card"
        style={{ '--stat-color': color } as React.CSSProperties}
    >
        <div className="dashboard-stat-icon">
            {icon}
        </div>
        <div className="dashboard-stat-content">
            <div className="dashboard-stat-title">
                {title}
            </div>
            <div className="dashboard-stat-value">{value}</div>
        </div>
    </div>
);
