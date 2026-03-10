import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../../api/client';
import { Input, Button } from '../../components/ui';
import { Search, Filter, Tag, Star, ChevronRight } from 'lucide-react';

interface Product {
    id: string;
    title: string;
    description: string;
    price_per_unit: string;
    unit: string;
    quantity_available: number;
    seller_email: string; // Backend source is seller.email
    crop_name: string;
    location_name?: string;
}

export const DiscoveryPage: React.FC = () => {
    const [products, setProducts] = useState<Product[]>([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        fetchProducts();
    }, []);

    const fetchProducts = async (q: string = '') => {
        setIsLoading(true);
        try {
            // Use discovery search endpoint
            const response = await api.get(`/discovery/search/`, {
                params: { q }
            });
            // The discovery search returns a list of result objects
            setProducts(response.data.results || response.data || []);
        } catch (err) {
            console.error('Failed to fetch products', err);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        fetchProducts(searchQuery);
    };

    return (
        <div className="container">
            <div style={{ marginBottom: '48px' }}>
                <h1 style={{ fontSize: '2.5rem', marginBottom: '16px' }}>Discover Fresh Produce</h1>
                <p style={{ color: 'var(--text-muted)', marginBottom: '32px' }}>
                    Browse verified listings from farmers across the region.
                </p>

                <form onSubmit={handleSearch} style={{ display: 'flex', gap: '12px', maxWidth: '800px' }}>
                    <div style={{ flex: 1, position: 'relative' }}>
                        <Search style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} size={20} />
                        <Input
                            placeholder="Search for crops (e.g. Wheat, Corn, Soybeans)..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            style={{ paddingLeft: '48px' }}
                        />
                    </div>
                    <Button variant="primary" type="submit" size="lg">
                        Search
                    </Button>
                    <Button variant="outline" type="button" size="lg">
                        <Filter size={20} />
                        Filters
                    </Button>
                </form>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '32px' }}>
                {isLoading ? (
                    Array.from({ length: 6 }).map((_, i) => (
                        <div key={i} className="glass" style={{ height: '400px', borderRadius: 'var(--radius-lg)', animation: 'pulse 2s infinite' }} />
                    ))
                ) : products.length > 0 ? (
                    products.map((product: Product) => (
                        <div key={product.id} className="glass card" style={{ padding: '0', overflow: 'hidden', borderRadius: 'var(--radius-lg)', transition: 'var(--transition-normal)' }}>
                            <div style={{ height: '200px', background: 'var(--accent-soft)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--primary)' }}>
                                <Tag size={48} opacity={0.3} />
                            </div>
                            <div style={{ padding: '24px' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                                    <span style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--primary)', background: 'var(--accent-soft)', padding: '2px 8px', borderRadius: 'var(--radius-sm)' }}>
                                        {product.crop_name}
                                    </span>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.875rem', fontWeight: 600 }}>
                                        <Star size={14} fill="var(--accent)" color="var(--accent)" />
                                        <span>4.8</span>
                                    </div>
                                </div>
                                <h3 style={{ marginBottom: '8px', fontSize: '1.25rem' }}>{product.title}</h3>
                                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '20px', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                                    {product.description}
                                </p>

                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid #f0f0f0', paddingTop: '20px' }}>
                                    <div>
                                        <span style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--primary)' }}>${product.price_per_unit}</span>
                                        <span style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}> / {product.unit}</span>
                                    </div>
                                    <Link to={`/products/${product.id}`}>
                                        <Button variant="ghost" size="sm" style={{ padding: '0' }}>
                                            View Details <ChevronRight size={16} />
                                        </Button>
                                    </Link>
                                </div>
                            </div>
                        </div>
                    ))
                ) : (
                    <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '100px 0' }}>
                        <p style={{ fontSize: '1.25rem', color: 'var(--text-muted)' }}>No products found matching your search.</p>
                    </div>
                )}
            </div>

            <style>{`
        @keyframes pulse {
          0% { opacity: 0.6; }
          50% { opacity: 0.3; }
          100% { opacity: 0.6; }
        }
        .card:hover {
          transform: translateY(-8px);
          box-shadow: var(--shadow-lg);
        }
      `}</style>
        </div>
    );
};
