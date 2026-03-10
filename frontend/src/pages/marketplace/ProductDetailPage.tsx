import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { api } from '../../api/client';
import { Button, Badge } from '../../components/ui';
import {
    User,
    MapPin,
    ShoppingBag,
    ArrowLeft,
    ShieldCheck,
    Star,
    Clock,
    LayoutList
} from 'lucide-react';

interface Product {
    id: string;
    title: string;
    description: string;
    crop_name: string;
    unit: string;
    price_per_unit: string;
    quantity_available: number;
    minimum_order_quantity: number;
    location_name: string;
    available_from: string;
    expires_at: string;
    status: string;
    seller_email: string;
}

export const ProductDetailPage: React.FC = () => {
    const { productId } = useParams<{ productId: string }>();
    const [product, setProduct] = useState<Product | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        if (productId) {
            fetchProductDetail();
        }
    }, [productId]);

    const fetchProductDetail = async () => {
        setIsLoading(true);
        try {
            const response = await api.get(`/marketplace/products/${productId}/`);
            setProduct(response.data);
        } catch (err: any) {
            console.error('Failed to fetch product detail', err);
            setError(err.response?.data?.detail || 'Product not found.');
        } finally {
            setIsLoading(false);
        }
    };

    if (isLoading) {
        return (
            <div className="container" style={{ textAlign: 'center', padding: '100px 0' }}>
                <Clock size={48} className="spin" style={{ color: 'var(--primary)', marginBottom: '16px' }} />
                <p style={{ color: 'var(--text-muted)' }}>Loading product details...</p>
            </div>
        );
    }

    if (error || !product) {
        return (
            <div className="container" style={{ textAlign: 'center', padding: '100px 0' }}>
                <LayoutList size={48} style={{ color: 'var(--error)', marginBottom: '16px' }} />
                <h3>Oops! {error || 'Product not found'}</h3>
                <Link to="/discovery" style={{ marginTop: '24px', display: 'inline-block' }}>
                    <Button variant="outline">Back to Discovery</Button>
                </Link>
            </div>
        );
    }

    const {
        title,
        description,
        crop_name,
        unit,
        price_per_unit,
        quantity_available,
        minimum_order_quantity,
        location_name,
        available_from,
        expires_at,
        status,
        seller_email
    } = product;

    return (
        <div className="container" style={{ maxWidth: '1000px' }}>
            <button
                onClick={() => navigate(-1)}
                style={{ background: 'none', border: 'none', display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)', marginBottom: '32px', fontWeight: 600, cursor: 'pointer' }}
            >
                <ArrowLeft size={18} /> Back
            </button>

            <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '48px' }}>
                {/* Left Column: Media & Description */}
                <div>
                    <div style={{
                        aspectRatio: '16/10',
                        background: 'var(--accent-soft)',
                        borderRadius: 'var(--radius-lg)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'var(--primary)',
                        marginBottom: '32px',
                        overflow: 'hidden'
                    }}>
                        <ShoppingBag size={80} opacity={0.2} />
                    </div>

                    <div style={{ marginBottom: '40px' }}>
                        <h2 style={{ fontSize: '1.5rem', marginBottom: '16px' }}>Detailed Description</h2>
                        <p style={{ color: 'var(--text-muted)', lineHeight: '1.8', whiteSpace: 'pre-line' }}>{description}</p>
                    </div>

                    <div className="glass" style={{ padding: '32px', borderRadius: 'var(--radius-lg)' }}>
                        <h3 style={{ fontSize: '1.125rem', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <ShieldCheck size={20} color="var(--primary)" /> Listing Integrity
                        </h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                                <span style={{ color: 'var(--text-muted)' }}>Listing ID</span>
                                <span style={{ fontWeight: 600 }}>#{product.id}</span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                                <span style={{ color: 'var(--text-muted)' }}>Available From</span>
                                <span style={{ fontWeight: 600 }}>{new Date(available_from).toLocaleDateString()}</span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                                <span style={{ color: 'var(--text-muted)' }}>Expiry Date</span>
                                <span style={{ fontWeight: 600 }}>{new Date(expires_at).toLocaleDateString()}</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right Column: Key Details & Actions */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                    <div>
                        <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
                            <Badge variant="primary">{crop_name}</Badge>
                            <Badge variant={status === 'active' ? 'success' : 'warning'}>{status}</Badge>
                        </div>
                        <h1 style={{ fontSize: '2.5rem', marginBottom: '16px', lineHeight: '1.2' }}>{title}</h1>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '24px', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                <MapPin size={16} /> {location_name}
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                <Star size={16} fill="var(--accent)" color="var(--accent)" /> 4.8 (12 Reviews)
                            </div>
                        </div>
                    </div>

                    <div className="glass" style={{ padding: '32px', borderRadius: 'var(--radius-lg)', background: 'white', boxShadow: 'var(--shadow-md)' }}>
                        <div style={{ marginBottom: '24px' }}>
                            <span style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--primary)' }}>${price_per_unit}</span>
                            <span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}> / {unit}</span>
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '32px' }}>
                            <div style={{ padding: '16px', background: '#f9fafb', borderRadius: 'var(--radius-md)' }}>
                                <div style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '4px' }}>Available</div>
                                <div style={{ fontWeight: 800 }}>{quantity_available} {unit}s</div>
                            </div>
                            <div style={{ padding: '16px', background: '#f9fafb', borderRadius: 'var(--radius-md)' }}>
                                <div style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '4px' }}>Min Order</div>
                                <div style={{ fontWeight: 800 }}>{minimum_order_quantity} {unit}s</div>
                            </div>
                        </div>

                        <Button size="lg" fullWidth style={{ fontSize: '1.125rem', height: '60px' }}>
                            Place Order
                        </Button>
                    </div>

                    <div className="glass" style={{ padding: '32px', borderRadius: 'var(--radius-lg)' }}>
                        <h3 style={{ fontSize: '1.125rem', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <User size={20} color="var(--primary)" /> Seller Information
                        </h3>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '20px' }}>
                            <div style={{ width: '48px', height: '48px', borderRadius: 'var(--radius-full)', background: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 700 }}>
                                {seller_email[0].toUpperCase()}
                            </div>
                            <div>
                                <div style={{ fontWeight: 700 }}>{seller_email.split('@')[0]}</div>
                                <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Verified Seller</div>
                            </div>
                        </div>
                        <Link to={`/reputation/${product.id}`} style={{ display: 'block' }}>
                            <Button variant="outline" fullWidth>View Seller Profile</Button>
                        </Link>
                    </div>
                </div>
            </div>

            <style>{`
                .spin {
                    animation: spin 1s linear infinite;
                }
                @keyframes spin {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
            `}</style>
        </div>
    );
};
