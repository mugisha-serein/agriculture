import React from 'react';

interface ChartItem {
    name: string;
    value: number;
}

interface UsageChartProps {
    data: ChartItem[];
    title: string;
}

export const UsageChart: React.FC<UsageChartProps> = ({ data, title }) => {
    const maxValue = Math.max(...data.map(d => d.value), 1);
    const totalValue = data.reduce((sum, item) => sum + item.value, 0);

    return (
        <div className="dashboard-usage-card">
            <div className="dashboard-usage-header">
                <h3 className="dashboard-usage-title">{title}</h3>
                <span className="dashboard-usage-total">{totalValue.toLocaleString()} total</span>
            </div>

            <div className="dashboard-usage-list">
                {data.map((item, i) => {
                    const widthPercent = Math.max((item.value / maxValue) * 100, 2);

                    return (
                        <div key={`${item.name}-${item.value}-${i}`} className="dashboard-usage-row">
                            <div className="dashboard-usage-row-top">
                                <span className="dashboard-usage-label">{item.name}</span>
                                <span className="dashboard-usage-value">{item.value.toLocaleString()}</span>
                            </div>
                            <div className="dashboard-usage-track">
                                <div
                                    className="dashboard-usage-bar"
                                    style={{
                                        width: `${widthPercent}%`,
                                        animationDelay: `${i * 70}ms`
                                    }}
                                />
                            </div>
                        </div>
                    );
                })}
                {data.length === 0 && (
                    <div className="dashboard-usage-empty">
                        No usage data available for this period.
                    </div>
                )}
            </div>

            <style>{`
                .dashboard-usage-card {
                    background: #fff;
                    border-radius: 20px;
                    border: 1px solid rgba(0,0,0,0.05);
                    box-shadow: 0 2px 4px rgba(15,23,42,0.06);
                    padding: 26px;
                    height: 100%;
                    transition: transform 0.24s cubic-bezier(0.22,1,0.36,1), 0.24s ease, border-color 0.24s ease;
                    animation: usageCardIn 0.45s cubic-bezier(0.22,1,0.36,1) both;
                }

                .dashboard-usage-header {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    gap: 12px;
                    margin-bottom: 22px;
                }

                .dashboard-usage-title {
                    font-size: 1.05rem;
                    font-weight: 700;
                    color: var(--text-dark);
                    margin: 0;
                }

                .dashboard-usage-total {
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

                .dashboard-usage-list {
                    display: flex;
                    flex-direction: column;
                    gap: 16px;
                }

                .dashboard-usage-row {
                    padding: 10px 12px;
                    border-radius: 12px;
                    transition: background 0.2s ease, transform 0.2s ease;
                }

                .dashboard-usage-row:hover {
                    background: rgba(16,185,129,0.04);
                    transform: translateX(2px);
                }

                .dashboard-usage-row-top {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    gap: 10px;
                    margin-bottom: 8px;
                }

                .dashboard-usage-label {
                    font-size: 0.88rem;
                    font-weight: 600;
                    color: var(--text-dark);
                }

                .dashboard-usage-value {
                    font-size: 0.84rem;
                    font-weight: 700;
                    color: var(--text-muted);
                    white-space: nowrap;
                }

                .dashboard-usage-track {
                    height: 8px;
                    background: rgba(15,23,42,0.06);
                    border-radius: 999px;
                    overflow: hidden;
                }

                .dashboard-usage-bar {
                    height: 100%;
                    border-radius: inherit;
                    background: linear-gradient(90deg, var(--primary), var(--accent));
                    transform-origin: left center;
                    animation: usageBarIn 0.7s cubic-bezier(0.22,1,0.36,1) both;
                }

                .dashboard-usage-empty {
                    text-align: center;
                    padding: 36px 0;
                    color: var(--text-muted);
                    font-size: 0.92rem;
                    border: 1px dashed rgba(0,0,0,0.12);
                    border-radius: 12px;
                    background: rgba(0,0,0,0.02);
                }

                @keyframes usageCardIn {
                    from { opacity: 0; transform: translateY(12px); }
                    to { opacity: 1; transform: translateY(0); }
                }

                @keyframes usageBarIn {
                    from { transform: scaleX(0); opacity: 0.6; }
                    to { transform: scaleX(1); opacity: 1; }
                }

                @media (max-width: 640px) {
                    .dashboard-usage-card {
                        padding: 20px;
                    }

                    .dashboard-usage-title {
                        font-size: 1rem;
                    }
                }

                @media (prefers-reduced-motion: reduce) {
                    .dashboard-usage-card,
                    .dashboard-usage-row,
                    .dashboard-usage-bar {
                        transition: none !important;
                        animation: none !important;
                    }
                }
            `}</style>
        </div>
    );
};
