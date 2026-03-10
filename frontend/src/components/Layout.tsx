import React from 'react';
import { Link, NavLink, Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { Leaf, User, LogOut, Menu, X } from 'lucide-react';
import { Footer } from './Footer';
import { SystemInlineError } from '../pages/Error';

export const Layout: React.FC = () => {
    const { user, isAuthenticated, logout } = useAuthStore();
    const navigate = useNavigate();
    const [isMenuOpen, setIsMenuOpen] = React.useState(false);

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const location = useLocation();
    const isAuthPage = location.pathname === '/login' || location.pathname === '/register';
    const shouldShowLayoutError = !['/login', '/register'].includes(location.pathname);

    const [indicatorStyle, setIndicatorStyle] = React.useState({ left: 0, width: 0, opacity: 0 });
    const navRef = React.useRef<HTMLElement>(null);

    React.useEffect(() => {
        const updateIndicator = () => {
            if (!navRef.current) return;
            const activeItem = navRef.current.querySelector('.nav-link.active') as HTMLElement;
            if (activeItem) {
                setIndicatorStyle({
                    left: activeItem.offsetLeft,
                    width: activeItem.offsetWidth,
                    opacity: 1
                });
            } else {
                setIndicatorStyle(prev => ({ ...prev, opacity: 0 }));
            }
        };
        // Short timeout to allow NavLink classes to resolve after render
        const timeoutId = setTimeout(updateIndicator, 10);
        window.addEventListener('resize', updateIndicator);
        return () => {
            clearTimeout(timeoutId);
            window.removeEventListener('resize', updateIndicator);
        };
    }, [location.pathname, isAuthenticated, user?.role]);

    return (
        <div className="layout">
            {!isAuthPage && (
                <header style={{
                    position: 'sticky',
                    top: 0,
                    zIndex: 100,
                    background: 'rgba(255, 255, 255, 0.9)',
                    backdropFilter: 'blur(12px)',
                    borderBottom: '1px solid rgba(0,0,0,0.05)',
                    boxShadow: '0 0px 0px -1px rgba(0, 0, 0, 0.05), 0 0px 0px -1px rgba(0, 0, 0, 0.03)',
                    animation: 'slideDownNavbar 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards'
                }}>
                    <div className="container" style={{ height: '80px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--primary)', fontWeight: 800, fontSize: '1.6rem', letterSpacing: '-0.5px', textDecoration: 'none' }}>
                            <div style={{ background: 'var(--accent-soft)', padding: '8px', borderRadius: '12px', display: 'flex' }}>
                                <Leaf size={28} fill="currentColor" color="var(--primary)" />
                            </div>
                            <span>AgriMarket</span>
                        </Link>

                        <div style={{ flex: 1 }} /> {/* White-space separator */}

                        {/* Desktop Navigation */}
                        <nav className="desktop-nav" ref={navRef} style={{ position: 'relative' }}>
                            <div style={{
                                position: 'absolute',
                                bottom: 0,
                                left: indicatorStyle.left,
                                width: indicatorStyle.width,
                                height: '2px',
                                backgroundColor: 'var(--primary)',
                                borderRadius: '2px',
                                transition: 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
                                opacity: indicatorStyle.opacity,
                                pointerEvents: 'none'
                            }} />
                            {(!user || user.role === 'buyer') && <NavLink to="/" className={({ isActive }) => isActive && location.pathname === '/' ? 'nav-link active' : 'nav-link'}>Home</NavLink>}
                            {(!user || user.role === 'buyer') && <NavLink to="/discovery" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Marketplace</NavLink>}
                            {(!user || user.role === 'buyer') && <NavLink to="/about" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>About</NavLink>}
                            {(!user || user.role === 'buyer') && <NavLink to="/contact" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Contact</NavLink>}
                            {isAuthenticated ? (
                                <>
                                    {(user?.role === 'seller' || user?.role === 'transporter') && <NavLink to="/" className={({ isActive }) => isActive && location.pathname === '/' ? 'nav-link active' : 'nav-link'}>Home</NavLink>}
                                    <NavLink to="/orders" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Orders</NavLink>
                                    {user?.role === 'seller' && <NavLink to="/seller/crops" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Crops</NavLink>}
                                    {user?.role === 'seller' && <NavLink to="/products/me" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Products</NavLink>}
                                    {(user?.role === 'transporter' || user?.role === 'seller') && <NavLink to="/shipments" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Shipments</NavLink>}
                                    {(user?.role === 'transporter' || user?.role === 'seller') && <NavLink to={`/reputation/${user.id}`} className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Reputation</NavLink>}
                                    {user?.role === 'seller' && <NavLink to="/transactions" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Transactions</NavLink>}

                                    <div style={{ width: '1px', height: '32px', background: '#e5e7eb', margin: '0 8px' }} />

                                    <NavLink to="/profile" className={({ isActive }) => isActive ? 'profile-btn active' : 'profile-btn'}>
                                        <User size={18} />
                                        <span>Profile</span>
                                    </NavLink>
                                    <button onClick={handleLogout} className="logout-btn">
                                        <LogOut size={18} />
                                        <span>Logout</span>
                                    </button>
                                </>
                            ) : (
                                <Link to="/login" style={{ padding: '10px 24px', borderRadius: 'var(--radius-full)', background: 'var(--primary)', color: 'white', fontWeight: 600, textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '8px', transition: 'all 0.2s ease', boxShadow: '0 4px 12px rgba(16, 185, 129, 0.3)' }}>
                                    <User size={18} />
                                    Sign In
                                </Link>
                            )}
                        </nav>

                        {/* Mobile Menu Toggle */}
                        <button className="mobile-toggle" onClick={() => setIsMenuOpen(!isMenuOpen)} style={{ background: 'var(--accent-soft)', border: 'none', padding: '10px', borderRadius: '12px', color: 'var(--primary)', cursor: 'pointer' }}>
                            {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
                        </button>
                    </div>
                </header>
            )}

            {/* Mobile Menu (simplified) */}
            {isMenuOpen && !isAuthPage && (
                <div className="glass" style={{ padding: '16px', borderBottom: '1px solid #e5e7eb' }}>
                    <nav style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                        {(!user || user.role === 'buyer') && <Link to="/" style={{ fontWeight: 500 }}>Home</Link>}
                        {(!user || user.role === 'buyer') && <Link to="/discovery" onClick={() => setIsMenuOpen(false)}>Marketplace</Link>}
                        {(!user || user.role === 'buyer') && <Link to="/about" onClick={() => setIsMenuOpen(false)}>About</Link>}
                        {(!user || user.role === 'buyer') && <Link to="/contact" onClick={() => setIsMenuOpen(false)}>Contact</Link>}
                        {isAuthenticated ? (
                            <>
                                {(user?.role === 'seller' || user?.role === 'transporter') && <Link to="/" onClick={() => setIsMenuOpen(false)}>Home</Link>}
                                <Link to="/orders" onClick={() => setIsMenuOpen(false)}>Orders</Link>
                                {user?.role === 'seller' && <Link to="/seller/crops" onClick={() => setIsMenuOpen(false)}>Crops</Link>}
                                {user?.role === 'seller' && <Link to="/products/me" onClick={() => setIsMenuOpen(false)}>Products</Link>}
                                {(user?.role === 'transporter' || user?.role === 'seller') && <Link to="/shipments" onClick={() => setIsMenuOpen(false)}>Shipments</Link>}
                                {user?.role === 'seller' && <Link to={`/reputation/${user.id}`} onClick={() => setIsMenuOpen(false)}>Reputation</Link>}
                                {user?.role === 'seller' && <Link to="/transactions" onClick={() => setIsMenuOpen(false)}>Transactions</Link>}
                                <NavLink to="/profile" className={({ isActive }) => isActive ? 'profile-btn active' : 'profile-btn'} onClick={() => setIsMenuOpen(false)}>Profile</NavLink>
                                <button onClick={handleLogout} style={{ textAlign: 'left', color: 'var(--error)', background: 'none' }}>Logout</button>
                            </>
                        ) : (
                            <Link to="/login" onClick={() => setIsMenuOpen(false)}>Login</Link>
                        )}
                    </nav>
                </div>
            )}

            <main style={{ minHeight: isAuthPage ? '100vh' : 'calc(100vh - 144px)', padding: isAuthPage ? 0 : '40px 0' }}>
                {shouldShowLayoutError && (
                    <div className="container" style={{ marginBottom: '12px' }}>
                        <SystemInlineError marginBottom="0" />
                    </div>
                )}
                <Outlet />
            </main>

            {!isAuthPage && <Footer />}

            <style>{`
        .desktop-nav { 
          display: none; 
          gap: 18px; 
          align-items: center; 
        }
        .nav-link {
          color: var(--text-dark);
          text-decoration: none;
          font-weight: 600;
          font-size: 0.95rem;
          padding: 4px 2px;
          position: relative;
          transition: color 0.2s all-in-out;
          white-space: nowrap;
        }
        .nav-link:hover, .nav-link.active {
          color: var(--primary);
        }
        
        .profile-btn, .logout-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 14px;
          border-radius: var(--radius-full);
          font-weight: 600;
          text-decoration: none;
          border: none;
          cursor: pointer;
          transition: all 0.2s ease;
          height: 34px;
        }
        
        .profile-btn {
          font-size: 0.9rem;
          background: var(--accent-soft);
          color: var(--primary);
        }
        .profile-btn:hover, .profile-btn.active {
          background: var(--primary);
          color: white;
          box-shadow: 0 4px 8px rgba(16, 185, 129, 0.15);
        }

        .logout-btn {
          font-size: 0.9rem;
          background: #fff1f2;
          color: var(--error);  
        }
        .logout-btn:hover {
          background-color: #fee2e2;
          box-shadow: 0 4px 8px rgba(220, 38, 38, 0.15);
        }

        .mobile-toggle {
          background: none;
          display: block;
        }

        @keyframes slideDownNavbar {
            from { transform: translateY(-100%); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }

        @media (min-width: 900px) {
          .desktop-nav { display: flex; }
          .mobile-toggle { display: none; }
        }
      `}</style>
        </div>
    );
};
