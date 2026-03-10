import React, { useMemo, useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../../api/client';
import { Button } from '../../components/ui';
import { Plus, Tag, Edit2, Trash2, Eye, Package, CheckCircle2, AlertTriangle, Leaf } from 'lucide-react';
import { reportApiError } from '../../lib/identityError';

interface Product {
    id: string;
    title: string;
    crop_name: string;
    price_per_unit: string;
    unit: string;
    quantity_available: number;
    status: string;
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

const getStatusInfo = (status: string): StatusInfo => {
    const normalized = status?.toLowerCase();
    if (normalized === 'active') {
        return {
            label: 'Active',
            color: 'var(--success)',
            bg: 'rgba(16,185,129,0.12)',
            border: 'rgba(16,185,129,0.28)',
            icon: <CheckCircle2 size={14} />
        };
    }
    if (normalized === 'inactive') {
        return {
            label: 'Inactive',
            color: 'var(--warning)',
            bg: 'rgba(245,158,11,0.12)',
            border: 'rgba(245,158,11,0.28)',
            icon: <AlertTriangle size={14} />
        };
    }
    return {
        label: normalized ? normalized.replace(/_/g, ' ') : 'Unknown',
        color: 'var(--text-muted)',
        bg: 'rgba(148,163,184,0.15)',
        border: 'rgba(148,163,184,0.28)',
        icon: <Package size={14} />
    };
};

export const SellerProductsPage: React.FC = () => {
    const [products, setProducts] = useState<Product[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        fetchMyProducts();
    }, []);

    const fetchMyProducts = async () => {
        setIsLoading(true);
        try {
            const response = await api.get('/marketplace/products/me/');
            setProducts(response.data.results || response.data || []);
        } catch (err: unknown) {
            reportApiError('Product Inventory Load Failed', err);
        } finally {
            setIsLoading(false);
        }
    };

    const summary = useMemo(() => {
        const total = products.length;
        const active = products.filter((product) => product.status?.toLowerCase() === 'active').length;
        const inactive = products.filter((product) => product.status?.toLowerCase() === 'inactive').length;
        return { total, active, inactive };
    }, [products]);

    return (
        <div className="container seller-products-page">
            <header className="seller-products-hero">
                <div>
                    <h1 className="seller-products-title">My Products</h1>
                    <p className="seller-products-subtitle">Manage listings, monitor stock, and keep pricing sharp.</p>
                </div>
                <div className="seller-products-actions">
                    <div className="seller-products-badges">
                        <span className="seller-products-pill">{summary.total} total</span>
                        <span className="seller-products-pill seller-products-pill-success">{summary.active} active</span>
                        <span className="seller-products-pill seller-products-pill-muted">{summary.inactive} inactive</span>
                    </div>
                    <Link to="/products/create">
                        <Button size="lg" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <Plus size={18} /> Create New Listing
                        </Button>
                    </Link>
                </div>
            </header>

            <div className="seller-products-grid">
                {isLoading ? (
                    Array.from({ length: 6 }).map((_, i) => (
                        <div key={i} className="seller-product-skeleton">
                            <div className="seller-product-skeleton-bar" />
                        </div>
                    ))
                ) : products.length > 0 ? (
                    products.map((product, index) => {
                        const statusInfo = getStatusInfo(product.status);
                        const availableLabel = `${product.quantity_available} ${product.unit}${product.quantity_available === 1 ? '' : 's'}`;
                        return (
                            <div key={product.id} className="seller-product-card" style={{ animationDelay: `${index * 0.06}s` }}>
                                <div className="seller-product-head">
                                    <div className="seller-product-title-wrap">
                                        <div className="seller-product-crop">
                                            <span className="seller-product-icon">
                                                <Leaf size={14} />
                                            </span>
                                            <span className="seller-product-tag">{product.crop_name}</span>
                                        </div>
                                        <h3 className="seller-product-title">{product.title}</h3>
                                    </div>
                                    <div className="seller-product-price">
                                        <div>{formatCurrency(product.price_per_unit)}</div>
                                        <span>per {product.unit}</span>
                                    </div>
                                </div>

                                <div className="seller-product-metrics">
                                    <div className="seller-product-metric">
                                        <span className="seller-product-metric-icon">
                                            <Package size={16} />
                                        </span>
                                        <div>
                                            <div className="seller-product-metric-label">Available</div>
                                            <div className="seller-product-metric-value">{availableLabel}</div>
                                        </div>
                                    </div>
                                    <div className="seller-product-metric">
                                        <span className="seller-product-metric-icon">
                                            <Eye size={16} />
                                        </span>
                                        <div>
                                            <div className="seller-product-metric-label">Status</div>
                                            <span
                                                className="seller-product-status"
                                                style={{ color: statusInfo.color, background: statusInfo.bg, borderColor: statusInfo.border }}
                                            >
                                                {statusInfo.icon}
                                                {statusInfo.label}
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                <div className="seller-product-actions">
                                    <Link to={`/products/${product.id}`} style={{ flex: 1 }}>
                                        <Button variant="outline" size="sm" style={{ width: '100%' }}>
                                            <Eye size={16} /> View Details
                                        </Button>
                                    </Link>
                                    <Button variant="outline" size="sm" style={{ flex: 1 }}>
                                        <Edit2 size={16} /> Edit
                                    </Button>
                                    <Button variant="outline" size="sm" style={{ flex: 0.5, borderColor: 'var(--error)', color: 'var(--error)' }}>
                                        <Trash2 size={16} />
                                    </Button>
                                </div>
                            </div>
                        );
                    })
                ) : (
                    <div className="seller-products-empty">
                        <Tag size={56} />
                        <h3>No products found</h3>
                        <p>You have not listed any produce yet.</p>
                        <Link to="/products/create">
                            <Button>Create Your First Listing</Button>
                        </Link>
                    </div>
                )}
            </div>

            <style>{`
                .seller-products-page {
                    animation: sellerProductsIn 0.45s cubic-bezier(0.16, 1, 0.3, 1) both;
                }

                .seller-products-hero {
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-end;
                    gap: 14px;
                    margin-bottom: 26px;
                    flex-wrap: wrap;
                }

                .seller-products-title {
                    margin: 0 0 8px;
                    font-size: 2rem;
                    font-weight: 800;
                    color: var(--text-dark);
                    letter-spacing: -0.4px;
                }

                .seller-products-subtitle {
                    margin: 0;
                    color: var(--text-muted);
                    font-size: 0.94rem;
                }

                .seller-products-actions {
                    display: flex;
                    align-items: center;
                    gap: 14px;
                    flex-wrap: wrap;
                    justify-content: flex-end;
                }

                .seller-products-badges {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    flex-wrap: wrap;
                }

                .seller-products-pill {
                    background: rgba(15, 23, 42, 0.06);
                    color: var(--text-muted);
                    border-radius: 999px;
                    padding: 6px 12px;
                    font-size: 0.74rem;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 0.04em;
                }

                .seller-products-pill-success {
                    background: rgba(16,185,129,0.12);
                    color: var(--success);
                }

                .seller-products-pill-muted {
                    background: rgba(148,163,184,0.15);
                    color: #64748b;
                }

                .seller-products-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
                    gap: 20px;
                }

                .seller-product-card,
                .seller-product-skeleton {
                    background: #fff;
                    border-radius: 18px;
                    border: 1px solid rgba(0,0,0,0.05);
                    box-shadow: 0 4px 22px rgba(15,23,42,0.06);
                    padding: 22px;
                    min-height: 360px;
                    transition: transform 0.24s cubic-bezier(0.22,1,0.36,1), box-shadow 0.24s ease, border-color 0.24s ease;
                }

                .seller-product-card {
                    opacity: 0;
                    animation: sellerProductCardIn 0.42s cubic-bezier(0.22,1,0.36,1) both;
                    display: flex;
                    flex-direction: column;
                }

                .seller-product-card:hover {
                    transform: translateY(-2px);
                    border-color: rgba(45,90,39,0.2);
                    box-shadow: 0 14px 32px rgba(15,23,42,0.1);
                }

                .seller-product-skeleton-bar {
                    height: 280px;
                    border-radius: 14px;
                    background: linear-gradient(110deg, rgba(0,0,0,0.04) 20%, rgba(0,0,0,0.08) 35%, rgba(0,0,0,0.04) 50%);
                    background-size: 220% 100%;
                    animation: sellerProductShimmer 1.2s linear infinite;
                }

                .seller-product-head {
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                    gap: 12px;
                    margin-bottom: 16px;
                }

                .seller-product-title-wrap {
                    flex: 1;
                    min-width: 0;
                }

                .seller-product-crop {
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                }

                .seller-product-icon {
                    width: 26px;
                    height: 26px;
                    border-radius: 8px;
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    background: rgba(45,90,39,0.12);
                    color: var(--primary);
                }

                .seller-product-tag {
                    display: inline-block;
                    font-size: 0.72rem;
                    font-weight: 700;
                    text-transform: uppercase;
                    color: var(--primary);
                    background: var(--accent-soft);
                    padding: 4px 10px;
                    border-radius: 999px;
                }

                .seller-product-title {
                    margin: 10px 0 0;
                    font-size: 1.1rem;
                    color: var(--text-dark);
                    line-height: 1.35;
                }

                .seller-product-price {
                    text-align: right;
                    font-weight: 800;
                    font-size: 1.15rem;
                    color: var(--text-dark);
                    white-space: nowrap;
                }

                .seller-product-price span {
                    display: block;
                    font-size: 0.82rem;
                    font-weight: 600;
                    color: var(--text-muted);
                }

                .seller-product-metrics {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 12px;
                    margin-bottom: 18px;
                    padding: 16px;
                    background: linear-gradient(135deg, rgba(17, 94, 89, 0.06), rgba(14, 116, 144, 0.04));
                    border-radius: 16px;
                    border: 1px solid rgba(15,23,42,0.06);
                }

                .seller-product-metric {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }

                .seller-product-metric-icon {
                    width: 32px;
                    height: 32px;
                    border-radius: 10px;
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    background: rgba(15,23,42,0.06);
                    color: var(--text-muted);
                    flex-shrink: 0;
                }

                .seller-product-metric-label {
                    font-size: 0.74rem;
                    color: var(--text-muted);
                    font-weight: 600;
                }

                .seller-product-metric-value {
                    font-weight: 700;
                    color: var(--text-dark);
                }

                .seller-product-status {
                    display: inline-flex;
                    align-items: center;
                    gap: 6px;
                    border: 1px solid;
                    border-radius: 999px;
                    padding: 3px 10px;
                    font-size: 0.72rem;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 0.03em;
                }

                .seller-product-actions {
                    display: flex;
                    gap: 10px;
                    margin-top: auto;
                }

                .seller-products-empty {
                    grid-column: 1 / -1;
                    text-align: center;
                    padding: 80px 0;
                    border-radius: 18px;
                    border: 1px dashed rgba(0,0,0,0.14);
                    background: #fff;
                }

                .seller-products-empty svg {
                    color: rgba(0,0,0,0.2);
                    margin-bottom: 16px;
                }

                .seller-products-empty h3 {
                    margin: 0 0 6px;
                    color: var(--text-dark);
                }

                .seller-products-empty p {
                    margin: 0 0 20px;
                    color: var(--text-muted);
                }

                @keyframes sellerProductsIn {
                    from { opacity: 0; transform: translateY(12px); }
                    to { opacity: 1; transform: translateY(0); }
                }

                @keyframes sellerProductCardIn {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }

                @keyframes sellerProductShimmer {
                    to { background-position-x: -220%; }
                }

                @media (max-width: 720px) {
                    .seller-products-title {
                        font-size: 1.7rem;
                    }

                    .seller-product-metrics {
                        grid-template-columns: 1fr;
                    }
                }

                @media (prefers-reduced-motion: reduce) {
                    .seller-products-page,
                    .seller-product-card,
                    .seller-product-skeleton {
                        animation: none !important;
                        transition: none !important;
                    }
                }
            `}</style>
        </div>
    );
};
