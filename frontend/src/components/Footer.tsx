import React from 'react';
import { Link } from 'react-router-dom';
import { Leaf } from 'lucide-react';

export const Footer: React.FC = () => {
    return (
        <footer style={{ background: 'var(--primary-dark)', color: 'white', padding: '64px 0' }}>
            <div className="container">
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '48px' }}>
                    <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '24px', fontWeight: 700, fontSize: '1.25rem' }}>
                            <Leaf size={24} />
                            <span>AgriMarket</span>
                        </div>
                        <p style={{ opacity: 0.7, fontSize: '0.9rem' }}>
                            The next-generation marketplace connecting farmers directly to buyers and transporters.
                        </p>
                    </div>
                    <div>
                        <h4 style={{ color: 'white', marginBottom: '16px' }}>Marketplace</h4>
                        <ul style={{ listStyle: 'none', opacity: 0.7, fontSize: '0.9rem', display: 'flex', flexDirection: 'column', gap: '8px', padding: 0, margin: 0 }}>
                            <li><Link to="/discovery" style={{ color: 'white', textDecoration: 'none' }}>Search Produce</Link></li>
                            <li><Link to="/sellers" style={{ color: 'white', textDecoration: 'none' }}>Top Sellers</Link></li>
                            <li><Link to="/pricing" style={{ color: 'white', textDecoration: 'none' }}>Pricing Plans</Link></li>
                        </ul>
                    </div>
                    <div>
                        <h4 style={{ color: 'white', marginBottom: '16px' }}>Company</h4>
                        <ul style={{ listStyle: 'none', opacity: 0.7, fontSize: '0.9rem', display: 'flex', flexDirection: 'column', gap: '8px', padding: 0, margin: 0 }}>
                            <li><Link to="/about" style={{ color: 'white', textDecoration: 'none' }}>About Us</Link></li>
                            <li><Link to="/contact" style={{ color: 'white', textDecoration: 'none' }}>Contact</Link></li>
                            <li><Link to="/privacy" style={{ color: 'white', textDecoration: 'none' }}>Privacy Policy</Link></li>
                        </ul>
                    </div>
                </div>
                <div style={{ borderTop: '1px solid rgba(255,255,255,0.1)', marginTop: '48px', paddingTop: '24px', display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', opacity: 0.5 }}>
                    <p>&copy; 2026 Triple S International Company Ltd. All rights reserved.</p>
                    <p>Designed for Sustainable Agriculture.</p>
                </div>
            </div>
        </footer>
    );
};
