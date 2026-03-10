import React, { useEffect, useState } from 'react';
import { Package, ShoppingBag, Leaf, Truck, Star } from 'lucide-react';

import { api } from '../../api/client';
import { useAuthStore } from '../../store/authStore';
import { ActivityFeed } from './ActivityFeed';
import { StatsCard } from './StatsCard';
import { UsageChart } from './UsageChart.tsx';

interface DashboardStats {
    total_products: number;
    total_orders: number;
    total_crops: number;
    total_shipments: number;
    total_reputation: string | number;
}

interface ChartItem {
    name: string;
    value: number;
}

interface ActivityItem {
    type: string;
    description: string;
    timestamp: string;
}

const monthOptions = [
    { v: '1', l: 'January' }, { v: '2', l: 'February' }, { v: '3', l: 'March' },
    { v: '4', l: 'April' }, { v: '5', l: 'May' }, { v: '6', l: 'June' },
    { v: '7', l: 'July' }, { v: '8', l: 'August' }, { v: '9', l: 'September' },
    { v: '10', l: 'October' }, { v: '11', l: 'November' }, { v: '12', l: 'December' }
];

export const Dashboard: React.FC = () => {
    const { user } = useAuthStore();
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [chartData, setChartData] = useState<ChartItem[]>([]);
    const [activity, setActivity] = useState<ActivityItem[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    const now = new Date();
    const [year, setYear] = useState(now.getFullYear().toString());
    const [month, setMonth] = useState((now.getMonth() + 1).toString());

    useEffect(() => {
        const fetchDashboardData = async () => {
            setIsLoading(true);
            try {
                const response = await api.get('/dashboard/stats/', {
                    params: { year, month }
                });
                setStats(response.data.stats);
                setChartData(response.data.chart_data);
                setActivity(response.data.activity);
            } catch (err) {
                console.error('Failed to fetch dashboard data', err);
            } finally {
                setIsLoading(false);
            }
        };

        fetchDashboardData();
    }, [year, month]);

    const monthLabel = monthOptions.find((item) => item.v === month)?.l || 'This Month';
    const years = [now.getFullYear() - 1, now.getFullYear(), now.getFullYear() + 1].map((value) => String(value));

    if (isLoading && !stats) {
        return (
            <div className="container dashboard-page">
                <div className="dashboard-loading dashboard-anim-bottom">
                    <div style={{ textAlign: 'center' }}>
                        <div className="dashboard-loader" />
                        <p style={{ fontWeight: 600, color: 'var(--text-muted)' }}>Loading dashboard...</p>
                    </div>
                </div>
                <style>{`
                    .dashboard-page {
                        display: flex;
                        flex-direction: column;
                        gap: 20px;
                    }

                    .dashboard-loading {
                        min-height: 260px;
                        display: grid;
                        place-items: center;
                        border-radius: 16px;
                        border: 1px solid #e8ece8;
                        background: #fff;
                        box-shadow: 0 2px 4px rgba(15, 23, 42, 0.05);
                    }

                    .dashboard-loader {
                        width: 32px;
                        height: 32px;
                        margin: 0 auto 12px;
                        border-radius: 50%;
                        border: 2px solid rgba(45, 90, 39, 0.25);
                        border-top-color: var(--primary);
                        animation: dashboardSpin 0.2s linear infinite;
                    }

                    .dashboard-anim-bottom {
                        opacity: 0;
                        animation: slideInBottom 0.45s cubic-bezier(0.16, 1, 0.3, 1) forwards;
                    }

                    @keyframes slideInBottom {
                        from { transform: translateY(30px); opacity: 0; }
                        to { transform: translateY(0); opacity: 1; }
                    }

                    @keyframes dashboardSpin {
                        from { transform: rotate(0deg); }
                        to { transform: rotate(360deg); }
                    }
                `}</style>
            </div>
        );
    }

    return (
        <div className="container dashboard-page">
            <section className="dashboard-hero dashboard-anim-left">
                <div>
                    <h1 style={{ fontSize: '2rem', marginBottom: '6px' }}>Welcome back, {user?.first_name || 'Farmer'}!</h1>
                    <p style={{ color: 'var(--text-muted)', marginBottom: '8px' }}>
                        Here is what is happening on your farm dashboard today.
                    </p>
                    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', color: 'var(--primary)', fontWeight: 700 }}>
                        <Leaf size={16} />
                        <span>Focus period: {monthLabel} {year}</span>
                    </div>
                </div>

                <div className="dashboard-filter-row">
                    <div className="dashboard-select-wrap">
                        <select
                            value={year}
                            onChange={(e) => setYear(e.target.value)}
                            className="dashboard-select"
                        >
                            {years.map((optionYear) => <option key={optionYear} value={optionYear}>{optionYear}</option>)}
                        </select>
                    </div>
                    <div className="dashboard-select-wrap">
                        <select
                            value={month}
                            onChange={(e) => setMonth(e.target.value)}
                            className="dashboard-select"
                        >
                            {monthOptions.map((item) => <option key={item.v} value={item.v}>{item.l}</option>)}
                        </select>
                    </div>
                </div>
            </section>

            <div className="dashboard-stats dashboard-anim-bottom" style={{ animationDelay: '0.08s' }}>
                {user?.role === 'seller' ? (
                    <>
                        <StatsCard title="Total Products" value={stats?.total_products || 0} icon={<Package size={24} />} />
                        <StatsCard title="Total Orders" value={stats?.total_orders || 0} icon={<ShoppingBag size={24} />} color="var(--accent)" />
                        <StatsCard title="Total Crops" value={stats?.total_crops || 0} icon={<Leaf size={24} />} color="var(--success)" />
                        <StatsCard title="Total Shipments" value={stats?.total_shipments || 0} icon={<Truck size={24} />} color="var(--info)" />
                        <StatsCard
                            title="Total Reputation"
                            value={typeof stats?.total_reputation === 'number' ? stats.total_reputation.toFixed(1) : (stats?.total_reputation || '0.0')}
                            icon={<Star size={24} />}
                            color="var(--warning)"
                        />
                    </>
                ) : (
                    <>
                        <StatsCard title="Total Orders" value={stats?.total_orders || 0} icon={<ShoppingBag size={32} />} color="var(--accent)" />
                        <StatsCard title="Total Shipments" value={stats?.total_shipments || 0} icon={<Truck size={32} />} color="var(--info)" />
                        <StatsCard
                            title="Total Reputation"
                            value={typeof stats?.total_reputation === 'number' ? stats.total_reputation.toFixed(1) : (stats?.total_reputation || '0.0')}
                            icon={<Star size={32} />}
                            color="var(--warning)"
                        />
                    </>
                )}
            </div>

            <div className="dashboard-panels dashboard-anim-bottom" style={{ animationDelay: '0.12s' }}>
                {user?.role === 'seller' && (
                    <UsageChart title="Top Products by Volume" data={chartData} />
                )}
                <ActivityFeed activities={activity} />
            </div>

            <style>{`
                .dashboard-page {
                    display: flex;
                    flex-direction: column;
                    gap: 20px;
                }

                .dashboard-hero {
                    border-radius: 18px;
                    border: 1px solid #e8ece8;
                    background: #fff;
                    padding: 24px;
                    display: flex;
                    align-items: flex-start;
                    justify-content: space-between;
                    gap: 18px;
                    transition: box-shadow 0.16s ease, transform 0.16s ease;
                }

                .dashboard-hero:hover {
                    transform: translateY(-1px);
                }

                .dashboard-filter-row {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    flex-wrap: wrap;
                }

                .dashboard-kyc-alert {
                    background: #fffbeb;
                    border: 1px solid #fef3c7;
                    border-radius: 14px;
                    padding: 16px;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    gap: 12px;
                    box-shadow: 0 4px 12px rgba(217, 119, 6, 0.08);
                }

                .dashboard-select-wrap {
                    position: relative;
                }

                .dashboard-select-wrap::after {
                    content: '';
                    position: absolute;
                    top: 50%;
                    right: 13px;
                    width: 8px;
                    height: 8px;
                    border-right: 2px solid #6b7280;
                    border-bottom: 2px solid #6b7280;
                    transform: translateY(-60%) rotate(45deg);
                    pointer-events: none;
                }

                .dashboard-select {
                    min-width: 110px;
                    height: 42px;
                    border-radius: 12px;
                    border: 1px solid #e5e7eb;
                    padding: 0 34px 0 14px;
                    background: #fff;
                    font-size: 0.93rem;
                    font-weight: 600;
                    color: #374151;
                    appearance: none;
                    transition: all 0.15s ease;
                }

                .dashboard-select:focus {
                    outline: none;
                    border-color: var(--primary);
                    box-shadow: 0 0 0 3px rgba(45, 90, 39, 0.12);
                }

                .dashboard-stats {
                    display: grid;
                    grid-template-columns: ${user?.role === 'transporter' ? 'repeat(3, minmax(0, 1fr))' : 'repeat(auto-fit, minmax(210px, 1fr))'};
                    gap: 8px;
                }

                .dashboard-stat-card {
                    background: #fff;
                    border-radius: 20px;
                    border: 1px solid rgba(0,0,0,0.05);
                    box-shadow: 0 2px 4px rgba(15,23,42,0.06);
                    padding: 15px;
                    display: flex;
                    align-items: center;
                    gap: 16px;
                    transition: transform 0.24s cubic-bezier(0.22,1,0.36,1), box-shadow 0.24s ease, border-color 0.24s ease;
                    will-change: transform, opacity;
                    opacity: 0;
                    animation: dashboardCardFloatIn 0.45s cubic-bezier(0.22,1,0.36,1) both;
                }

                .dashboard-stat-card:hover {
                    transform: translateY(-2px);
                    border-color: rgba(45,90,39,0.2);
                    box-shadow: 0 4px 12px rgba(15,23,42,0.1);
                }

                .dashboard-stat-icon {
                    position: relative;
                    width: 40px;
                    height: 40px;
                    border-radius: 14px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: var(--stat-color);
                    flex-shrink: 0;
                    overflow: hidden;
                }

                .dashboard-stat-icon::before {
                    content: '';
                    position: absolute;
                    inset: 0;
                    border-radius: inherit;
                    background: var(--stat-color);
                    opacity: 0.12;
                }

                .dashboard-stat-icon > * {
                    position: relative;
                    z-index: 1;
                }

                .dashboard-stat-title {
                    font-size: 0.84rem;
                    color: var(--text-muted);
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    margin-bottom: 4px;
                }

                .dashboard-stat-value {
                    font-size: 1.7rem;
                    font-weight: 800;
                    color: var(--text-dark);
                    line-height: 1.1;
                }

                .dashboard-stats .dashboard-stat-card:nth-child(2) { animation-delay: 0.04s; }
                .dashboard-stats .dashboard-stat-card:nth-child(3) { animation-delay: 0.08s; }
                .dashboard-stats .dashboard-stat-card:nth-child(4) { animation-delay: 0.12s; }
                .dashboard-stats .dashboard-stat-card:nth-child(5) { animation-delay: 0.16s; }

                .dashboard-panels {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
                    gap: 16px;
                }

                .dashboard-anim-left {
                    opacity: 0;
                    will-change: transform, opacity;
                    animation: slideInLeft 0.42s cubic-bezier(0.16, 1, 0.3, 1) forwards;
                }

                .dashboard-anim-bottom {
                    opacity: 0;
                    will-change: transform, opacity;
                    animation: slideInBottom 0.45s cubic-bezier(0.16, 1, 0.3, 1) forwards;
                }

                @keyframes slideInLeft {
                    from { transform: translateX(-10%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }

                @keyframes slideInBottom {
                    from { transform: translateY(30px); opacity: 0; }
                    to { transform: translateY(0); opacity: 1; }
                }

                @keyframes dashboardCardFloatIn {
                    from { opacity: 0; transform: translateY(12px); }
                    to { opacity: 1; transform: translateY(0); }
                }

                @media (max-width: 1199px) {
                    .dashboard-hero {
                        flex-direction: column;
                        align-items: flex-start;
                    }

                    .dashboard-kyc-alert {
                        flex-wrap: wrap;
                    }
                }

                @media (max-width: 640px) {
                    .dashboard-hero h1 {
                        font-size: 1.75rem !important;
                    }

                    .dashboard-stats {
                        grid-template-columns: 1fr;
                    }

                    .dashboard-panels {
                        grid-template-columns: 1fr;
                    }
                }

                @media (prefers-reduced-motion: reduce) {
                    .dashboard-anim-left,
                    .dashboard-anim-bottom {
                        animation: none !important;
                        opacity: 1;
                        transform: none !important;
                    }

                    .dashboard-hero,
                    .dashboard-stat-card {
                        transition: none;
                    }

                    .dashboard-stat-card {
                        animation: none !important;
                        opacity: 1;
                        transform: none !important;
                    }
                }
            `}</style>
        </div>
    );
};
