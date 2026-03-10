import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '../../api/client';
import { useAuthStore } from '../../store/authStore';
import { Button } from '../../components/ui';
import { Leaf, Eye, EyeOff, Mail, Lock, CheckCircle2 } from 'lucide-react';
import { reportApiError } from '../../lib/identityError';
import { SystemInlineError } from '../Error';

import agricultureVideo from '../../assets/videos/agriculture.mp4';

export const LoginPage: React.FC = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [isLoading, setIsLoading] = useState(false);

    const navigate = useNavigate();
    const setAuth = useAuthStore((state) => state.setAuth);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);

        try {
            const response = await api.post('/identity/login/', { email, password });
            const { user, access_token, refresh_token } = response.data;

            setAuth(user, access_token, refresh_token);
            navigate('/');
        } catch (err: unknown) {
            reportApiError('Login Failed', err);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div style={{ display: 'flex', height: '100vh', width: '100%', backgroundColor: '#fff', overflow: 'hidden' }}>
            {/* Left Side: Visuals & Branding */}
            <div className="login-left" style={{ flex: 1.4, position: 'relative', flexDirection: 'column', overflow: 'hidden', borderTopRightRadius: '48px', borderBottomRightRadius: '48px', boxShadow: '10px 0 24px rgba(0,0,0,0.1)', zIndex: 1, animation: 'slideInLeft 1s cubic-bezier(0.16, 1, 0.3, 1) forwards' }}>
                <video
                    autoPlay
                    loop
                    muted
                    playsInline
                    style={{ position: 'absolute', width: '100%', height: '100%', objectFit: 'cover' }}
                >
                    {/* Using a placeholder high-quality agriculture stock video */}
                    <source src={agricultureVideo} type="video/mp4" />
                </video>
                <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(135deg, rgba(6, 78, 59, 0.96), rgba(19, 175, 123, 0.07))' }} />

                <div style={{ position: 'relative', zIndex: 10, display: 'flex', flexDirection: 'column', height: '100%', justifyContent: 'space-between', padding: '60px', color: 'white' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <Leaf size={40} />
                        <span style={{ fontSize: '2rem', fontWeight: 800, letterSpacing: '-0.5px' }}>AgriMarket</span>
                    </div>

                    <div style={{ maxWidth: '480px' }}>
                        <h1 style={{ fontSize: '3.5rem', fontWeight: 800, lineHeight: 1.1, marginBottom: '24px', color: 'white' }}>
                            Cultivating<br />Connections.
                        </h1>
                        <p style={{ fontSize: '1.25rem', opacity: 0.9, lineHeight: 1.6, marginBottom: '40px' }}>
                            Our digital ecosystem bridges the gap between rural farmers, reliable transporters, and nationwide buyers. Experience transparent pricing, verified quality, and seamless logistics.
                        </p>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                <CheckCircle2 size={24} color="#a7f3d0" />
                                <span style={{ fontSize: '1.1rem', fontWeight: 500 }}>Verified Farmers & Produce</span>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                <CheckCircle2 size={24} color="#a7f3d0" />
                                <span style={{ fontSize: '1.1rem', fontWeight: 500 }}>Secure Payment Escrow</span>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                <CheckCircle2 size={24} color="#a7f3d0" />
                                <span style={{ fontSize: '1.1rem', fontWeight: 500 }}>Integrated Logistics Tracking</span>
                            </div>
                        </div>
                    </div>

                    <div style={{ fontSize: '0.9rem', opacity: 0.7 }}>
                        &copy; 2026 Triple S International. Empowering Agriculture.
                    </div>
                </div>
            </div>

            {/* Right Side: Login Form */}
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', padding: '40px 20px', background: '#ffffff', opacity: 0, animation: 'slideInBottom 1s cubic-bezier(0.16, 1, 0.3, 1) 0.2s forwards' }}>
                <div style={{ width: '100%', maxWidth: '420px' }}>

                    {/* Mobile Header (Hidden on large screens) */}
                    <div className="mobile-header" style={{ display: 'flex', alignItems: 'center', gap: '12px', justifyContent: 'center', marginBottom: '48px', color: 'var(--primary)' }}>
                        <Leaf size={32} />
                        <span style={{ fontSize: '1.75rem', fontWeight: 800 }}>AgriMarket</span>
                    </div>

                    <div style={{ marginBottom: '40px' }}>
                        <h2 style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '8px', color: 'var(--text-dark)' }}>Welcome back</h2>
                        <p style={{ color: 'var(--text-muted)', fontSize: '1rem' }}>Enter your credentials to access your account.</p>
                    </div>
                    <SystemInlineError marginBottom="24px" />

                    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>

                        {/* Custom robust Email input */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            <label style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-muted)' }}>Email Address</label>
                            <div style={{ position: 'relative' }}>
                                <div style={{ position: 'absolute', top: '50%', left: '16px', transform: 'translateY(-50%)', color: '#9ca3af', pointerEvents: 'none' }}>
                                    <Mail size={20} />
                                </div>
                                <input
                                    type="email"
                                    placeholder="farmer@example.com"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                    className="custom-input"
                                />
                            </div>
                        </div>

                        {/* Custom robust Password input */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <label style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-muted)' }}>Password</label>
                                <Link to="/forgot-password" style={{ fontSize: '0.875rem', color: 'var(--primary)', fontWeight: 600 }}>
                                    Forgot password?
                                </Link>
                            </div>
                            <div style={{ position: 'relative' }}>
                                <div style={{ position: 'absolute', top: '50%', left: '16px', transform: 'translateY(-50%)', color: '#9ca3af', pointerEvents: 'none' }}>
                                    <Lock size={20} />
                                </div>
                                <input
                                    type={showPassword ? 'text' : 'password'}
                                    placeholder="********"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                    className="custom-input"
                                    style={{ paddingRight: '48px' }}
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    style={{ position: 'absolute', top: '50%', right: '16px', transform: 'translateY(-50%)', background: 'none', border: 'none', color: '#9ca3af', cursor: 'pointer', padding: 0 }}
                                    aria-label={showPassword ? "Hide password" : "Show password"}
                                >
                                    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                                </button>
                            </div>
                        </div>

                        <Button type="submit" fullWidth isLoading={isLoading} size="lg" style={{ height: '56px', fontSize: '1.1rem', marginTop: '8px' }}>
                            Sign In
                        </Button>
                    </form>

                    <div style={{ marginTop: '40px', textAlign: 'center', fontSize: '0.95rem', color: 'var(--text-muted)' }}>
                        Don't have an account?{' '}
                        <Link to="/register" style={{ color: 'var(--primary)', fontWeight: 600, textDecoration: 'underline' }}>
                            Create an account
                        </Link>
                    </div>
                </div>
            </div>

            <style>{`
                .login-left { display: none !important; }
                .mobile-header { display: flex !important; }
                
                @media (min-width: 900px) {
                    .login-left { display: flex !important; }
                    .mobile-header { display: none !important; }
                }

                /* Override Input component styles to match our robust design if needed */
                .custom-input {
                    width: 100%;
                    height: 56px;
                    padding: 12px 16px 12px 48px;
                    border-radius: var(--radius-md);
                    border: 1px solid #e5e7eb;
                    font-size: 1rem;
                    outline: none;
                    transition: all 0.2s ease;
                }
                .custom-input:focus {
                    border-color: var(--primary);
                    box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.2);
                }

                @keyframes slideInLeft {
                    from { transform: translateX(-10%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }

                @keyframes slideInBottom {
                    from { transform: translateY(40px); opacity: 0; }
                    to { transform: translateY(0); opacity: 1; }
                }
            `}</style>
        </div>
    );
};
