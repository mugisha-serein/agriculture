import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, Shovel, Truck, ShieldCheck, Star, Leaf, Users, ArrowRight, CheckCircle2, Package } from 'lucide-react';
import { api } from '../api/client';
import { reportApiError } from '../lib/identityError';
import { useAuthStore } from '../store/authStore';
import { Dashboard } from './dashboard/Dashboard';

interface HomeHero {
    title: string;
    subtitle: string;
    primary_cta_label: string;
    primary_cta_href: string;
    secondary_cta_label: string;
    secondary_cta_href: string;
}

interface HomeBannerCard {
    icon: string;
    label: string;
}

interface HomeBanner {
    kicker: string;
    title: string;
    subtitle: string;
    cards: HomeBannerCard[];
}

interface HomeSlide {
    title: string;
    description: string;
}

interface HomeSlideshowAside {
    title: string;
    description: string;
    metric_label: string;
    metric_value: number;
}

interface HomeSlideshow {
    slides: HomeSlide[];
    aside: HomeSlideshowAside;
}

interface HomeStats {
    total_crops: number;
    total_products: number;
    verified_sellers: number;
    verified_transporters: number;
}

interface HomeFeaturedMeta {
    title: string;
    subtitle: string;
    cta_label: string;
    cta_href: string;
    item_cta_label: string;
}

interface HomeVerifiedMeta {
    title: string;
    subtitle: string;
    sellers_label: string;
    transporters_label: string;
}

interface HomeStep {
    title: string;
    description: string;
    icon: string;
    tone: 'accent' | 'primary' | 'secondary';
}

interface HomeHowItWorks {
    title: string;
    subtitle: string;
    steps: HomeStep[];
}

interface HomeEmptyState {
    featured_products: string;
    verified_sellers: string;
    verified_transporters: string;
}

interface FeaturedProduct {
    id: number;
    title: string;
    description: string;
    crop_name: string;
    location_name?: string;
    price_per_unit: string | number;
    unit: string;
    quantity_available: string | number;
    seller_email: string;
}

interface VerifiedUser {
    user_id: number;
    display_name: string;
    email: string;
    role: string;
    review_count: number;
    average_rating: number;
    rating_label: string;
    review_label: string;
}

interface HomePayload {
    hero: HomeHero;
    banner: HomeBanner;
    slideshow: HomeSlideshow;
    stats: HomeStats;
    featured: HomeFeaturedMeta;
    featured_products: FeaturedProduct[];
    verified: HomeVerifiedMeta;
    verified_sellers: VerifiedUser[];
    verified_transporters: VerifiedUser[];
    how_it_works: HomeHowItWorks;
    empty_state: HomeEmptyState;
}

const iconMap: Record<string, React.ComponentType<{ size?: number }>> = {
    package: Package,
    shield: ShieldCheck,
    truck: Truck,
    star: Star,
    shovel: Shovel,
    leaf: Leaf,
    users: Users,
    check: CheckCircle2,
};

const toneMap: Record<HomeStep['tone'], { background: string; color: string }> = {
    accent: { background: 'var(--accent-soft)', color: 'var(--accent)' },
    primary: { background: 'var(--primary-light)', color: 'white' },
    secondary: { background: 'var(--secondary-light)', color: 'white' },
};

export const HomePage: React.FC = () => {
    const { user, isAuthenticated } = useAuthStore();
    const [activeSlide, setActiveSlide] = useState(0);
    const [homeData, setHomeData] = useState<HomePayload | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    // If authenticated as seller or transporter, show dashboard
    if (isAuthenticated && (user?.role === 'seller' || user?.role === 'transporter')) {
        return <Dashboard />;
    }

    const slides = homeData?.slideshow?.slides ?? [];
    const featuredProducts = homeData?.featured_products ?? [];
    const verifiedSellers = homeData?.verified_sellers ?? [];
    const verifiedTransporters = homeData?.verified_transporters ?? [];
    const hero = homeData?.hero;
    const banner = homeData?.banner;
    const slideshow = homeData?.slideshow;
    const featuredMeta = homeData?.featured;
    const verifiedMeta = homeData?.verified;
    const howItWorks = homeData?.how_it_works;
    const emptyState = homeData?.empty_state;
    const activeSlideData = slides[activeSlide];

    useEffect(() => {
        const fetchHomeContent = async () => {
            setIsLoading(true);
            try {
                const response = await api.get('/discovery/home/');
                setHomeData(response.data);
            } catch (err) {
                reportApiError('Home Page Load Failed', err);
            } finally {
                setIsLoading(false);
            }
        };

        fetchHomeContent();
    }, []);

    useEffect(() => {
        if (!slides.length) return;
        setActiveSlide(0);
    }, [slides.length]);

    useEffect(() => {
        if (!slides.length) return;
        const interval = window.setInterval(() => {
            setActiveSlide((prev) => (prev + 1) % slides.length);
        }, 4500);
        return () => window.clearInterval(interval);
    }, [slides.length]);

    return (
        <div className="home-page">
            <section className="gradient-hero" style={{ padding: '80px 0', borderRadius: '0 0 var(--radius-lg) var(--radius-lg)' }}>
                <div className="container" style={{ textAlign: 'center' }}>
                    <h1 style={{ color: 'white', fontSize: '3.5rem', marginBottom: '24px' }}>{hero?.title ?? ''}</h1>
                    <p style={{ fontSize: '1.25rem', opacity: 0.9, maxWidth: '600px', margin: '0 auto 40px' }}>
                        {hero?.subtitle ?? ''}
                    </p>
                    <div style={{ display: 'flex', gap: '16px', justifyContent: 'center' }}>
                        {hero?.primary_cta_label && hero?.primary_cta_href && (
                            <Link to={hero.primary_cta_href} className="glass" style={{ background: 'white', color: 'var(--primary)', padding: '12px 32px', borderRadius: 'var(--radius-full)', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <Search size={20} />
                                {hero.primary_cta_label}
                            </Link>
                        )}
                        {hero?.secondary_cta_label && hero?.secondary_cta_href && (
                            <Link to={hero.secondary_cta_href} style={{ border: '2px solid white', color: 'white', padding: '12px 32px', borderRadius: 'var(--radius-full)', fontWeight: 700 }}>
                                {hero.secondary_cta_label}
                            </Link>
                        )}
                    </div>
                </div>
            </section>

            <section className="home-banner">
                <div className="container home-banner-inner">
                    <div>
                        <span className="home-kicker"><Leaf size={14} /> {banner?.kicker ?? ''}</span>
                        <h2>{banner?.title ?? ''}</h2>
                        <p>{banner?.subtitle ?? ''}</p>
                    </div>
                    <div className="home-banner-grid">
                        {(banner?.cards ?? []).map((card, index) => {
                            const Icon = iconMap[card.icon] || Package;
                            return (
                                <div key={`${card.label}-${index}`} className="home-banner-card">
                                    <Icon size={18} />
                                    {card.label}
                                </div>
                            );
                        })}
                    </div>
                </div>
            </section>

            <section className="home-slideshow">
                <div className="container home-slideshow-inner">
                    <div className="home-slideshow-card">
                        <div className="home-slideshow-icon">
                            <CheckCircle2 size={20} />
                        </div>
                        <h3>{activeSlideData?.title ?? ''}</h3>
                        <p>{activeSlideData?.description ?? ''}</p>
                        <div className="home-slideshow-dots">
                            {slides.map((_, index) => (
                                <span key={index} className={index === activeSlide ? 'active' : ''} />
                            ))}
                        </div>
                    </div>
                    <div className="home-slideshow-aside">
                        <div>
                            <h4>{slideshow?.aside?.title ?? ''}</h4>
                            <p>{slideshow?.aside?.description ?? ''}</p>
                        </div>
                        <div className="home-slideshow-row">
                            <Users size={18} />
                            <span>
                                {slideshow?.aside?.metric_value !== undefined && slideshow?.aside?.metric_label
                                    ? `${slideshow.aside.metric_value.toLocaleString()} ${slideshow.aside.metric_label}`
                                    : ''}
                            </span>
                        </div>
                    </div>
                </div>
            </section>

            <section className="home-featured">
                <div className="container">
                    <div className="home-section-head">
                        <div>
                            <h2>{featuredMeta?.title ?? ''}</h2>
                            <p>{featuredMeta?.subtitle ?? ''}</p>
                        </div>
                        {featuredMeta?.cta_label && featuredMeta?.cta_href && (
                            <Link to={featuredMeta.cta_href} className="home-view-more">
                                {featuredMeta.cta_label} <ArrowRight size={16} />
                            </Link>
                        )}
                    </div>
                    <div className="home-featured-grid">
                        {isLoading ? (
                            Array.from({ length: 4 }).map((_, index) => (
                                <div key={`featured-skeleton-${index}`} className="home-featured-card home-skeleton-card" />
                            ))
                        ) : featuredProducts.length > 0 ? (
                            featuredProducts.map((item) => (
                                <div key={item.id} className="home-featured-card">
                                    <span className="home-featured-tag">{item.crop_name}</span>
                                    <h3>{item.title}</h3>
                                    <div className="home-featured-meta">
                                        <span>{item.location_name ?? ''}</span>
                                        <span>{`${item.quantity_available} ${item.unit}`}</span>
                                    </div>
                                    <div className="home-featured-price">
                                        ${item.price_per_unit} <span>per {item.unit}</span>
                                    </div>
                                    {featuredMeta?.item_cta_label && (
                                        <Link to={`/products/${item.id}`} className="home-featured-link">
                                            {featuredMeta.item_cta_label}
                                        </Link>
                                    )}
                                </div>
                            ))
                        ) : (
                            <div className="home-featured-empty">
                                <p>{emptyState?.featured_products ?? ''}</p>
                            </div>
                        )}
                    </div>
                </div>
            </section>

            <section className="home-verified">
                <div className="container">
                    <div className="home-section-head">
                        <div>
                            <h2>{verifiedMeta?.title ?? ''}</h2>
                            <p>{verifiedMeta?.subtitle ?? ''}</p>
                        </div>
                    </div>
                    <div className="home-verified-grid">
                        <div className="home-verified-column">
                            <h3>{verifiedMeta?.sellers_label ?? ''}</h3>
                            {isLoading ? (
                                Array.from({ length: 3 }).map((_, index) => (
                                    <div key={`seller-skeleton-${index}`} className="home-verified-card home-skeleton-card" />
                                ))
                            ) : verifiedSellers.length > 0 ? (
                                verifiedSellers.map((seller) => (
                                    <div key={seller.user_id} className="home-verified-card">
                                        <div>
                                            <strong>{seller.display_name}</strong>
                                            <span>{seller.email}</span>
                                        </div>
                                        <span className="home-verified-pill">
                                            <Star size={14} /> {seller.rating_label} · {seller.review_label}
                                        </span>
                                    </div>
                                ))
                            ) : (
                                <div className="home-verified-empty">
                                    <p>{emptyState?.verified_sellers ?? ''}</p>
                                </div>
                            )}
                        </div>
                        <div className="home-verified-column">
                            <h3>{verifiedMeta?.transporters_label ?? ''}</h3>
                            {isLoading ? (
                                Array.from({ length: 3 }).map((_, index) => (
                                    <div key={`transporter-skeleton-${index}`} className="home-verified-card home-skeleton-card" />
                                ))
                            ) : verifiedTransporters.length > 0 ? (
                                verifiedTransporters.map((carrier) => (
                                    <div key={carrier.user_id} className="home-verified-card">
                                        <div>
                                            <strong>{carrier.display_name}</strong>
                                            <span>{carrier.email}</span>
                                        </div>
                                        <span className="home-verified-pill">
                                            <Star size={14} /> {carrier.rating_label} · {carrier.review_label}
                                        </span>
                                    </div>
                                ))
                            ) : (
                                <div className="home-verified-empty">
                                    <p>{emptyState?.verified_transporters ?? ''}</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </section>

            <section style={{ padding: '100px 0' }}>
                <div className="container">
                    <div style={{ textAlign: 'center', marginBottom: '64px' }}>
                        <h2 style={{ fontSize: '2.5rem' }}>{howItWorks?.title ?? ''}</h2>
                        <p style={{ color: 'var(--text-muted)' }}>{howItWorks?.subtitle ?? ''}</p>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '32px' }}>
                        {isLoading ? (
                            Array.from({ length: 3 }).map((_, index) => (
                                <div key={`how-skeleton-${index}`} className="glass home-skeleton-card" style={{ padding: '32px', borderRadius: 'var(--radius-lg)', boxShadow: 'var(--shadow-md)' }} />
                            ))
                        ) : (
                            (howItWorks?.steps ?? []).map((step, index) => {
                                const Icon = iconMap[step.icon] || Shovel;
                                const tone = toneMap[step.tone] || toneMap.accent;
                                return (
                                    <div key={`${step.title}-${index}`} className="glass" style={{ padding: '32px', borderRadius: 'var(--radius-lg)', boxShadow: 'var(--shadow-md)' }}>
                                        <div style={{ width: '48px', height: '48px', background: tone.background, color: tone.color, borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '24px' }}>
                                            <Icon size={24} />
                                        </div>
                                        <h3 style={{ marginBottom: '16px' }}>{step.title}</h3>
                                        <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
                                            {step.description}
                                        </p>
                                    </div>
                                );
                            })
                        )}
                    </div>
                </div>
            </section>

            <style>{`
                .home-banner {
                    padding: 80px 0 40px;
                }

                .home-banner-inner {
                    background: linear-gradient(135deg, rgba(15, 118, 110, 0.12), rgba(14, 116, 144, 0.08));
                    border-radius: 28px;
                    padding: 40px;
                    display: grid;
                    gap: 24px;
                    border: 1px solid rgba(15, 23, 42, 0.08);
                }

                .home-banner-inner h2 {
                    margin: 10px 0 8px;
                    font-size: 2rem;
                }

                .home-banner-inner p {
                    margin: 0;
                    color: var(--text-muted);
                }

                .home-kicker {
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    padding: 6px 12px;
                    border-radius: 999px;
                    background: rgba(45, 90, 39, 0.12);
                    color: var(--primary);
                    font-weight: 700;
                    font-size: 0.75rem;
                    text-transform: uppercase;
                    letter-spacing: 0.04em;
                }

                .home-banner-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
                    gap: 12px;
                }

                .home-banner-card {
                    background: #fff;
                    border-radius: 16px;
                    padding: 14px 16px;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    font-weight: 700;
                    color: var(--text-dark);
                    box-shadow: 0 6px 16px rgba(15, 23, 42, 0.08);
                }

                .home-slideshow {
                    padding: 40px 0 80px;
                }

                .home-slideshow-inner {
                    display: grid;
                    grid-template-columns: 2fr 1fr;
                    gap: 24px;
                    align-items: stretch;
                }

                .home-slideshow-card {
                    background: #fff;
                    border-radius: 24px;
                    padding: 32px;
                    border: 1px solid rgba(0,0,0,0.06);
                    box-shadow: 0 12px 28px rgba(15, 23, 42, 0.12);
                    min-height: 220px;
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                    animation: homeSlideIn 0.35s ease;
                }

                .home-slideshow-card h3 {
                    margin: 0;
                    font-size: 1.5rem;
                }

                .home-slideshow-card p {
                    margin: 0;
                    color: var(--text-muted);
                }

                .home-slideshow-icon {
                    width: 42px;
                    height: 42px;
                    border-radius: 14px;
                    display: grid;
                    place-items: center;
                    background: rgba(45, 90, 39, 0.12);
                    color: var(--primary);
                }

                .home-slideshow-dots {
                    margin-top: auto;
                    display: flex;
                    gap: 8px;
                }

                .home-slideshow-dots span {
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    background: rgba(0,0,0,0.2);
                }

                .home-slideshow-dots span.active {
                    width: 20px;
                    border-radius: 999px;
                    background: var(--primary);
                }

                .home-slideshow-aside {
                    background: #0f172a;
                    color: #fff;
                    border-radius: 24px;
                    padding: 28px;
                    display: flex;
                    flex-direction: column;
                    gap: 16px;
                }

                .home-slideshow-aside h4 {
                    margin: 0 0 6px;
                    font-size: 1.2rem;
                }

                .home-slideshow-aside p {
                    margin: 0;
                    opacity: 0.8;
                }

                .home-slideshow-row {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    background: rgba(255,255,255,0.12);
                    border-radius: 14px;
                    padding: 10px 12px;
                    font-weight: 600;
                }

                .home-featured {
                    padding: 60px 0;
                }

                .home-section-head {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    gap: 16px;
                    margin-bottom: 24px;
                    flex-wrap: wrap;
                }

                .home-section-head h2 {
                    margin: 0 0 6px;
                    font-size: 2rem;
                }

                .home-section-head p {
                    margin: 0;
                    color: var(--text-muted);
                }

                .home-view-more {
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    padding: 10px 16px;
                    border-radius: 999px;
                    border: 1px solid rgba(0,0,0,0.1);
                    text-decoration: none;
                    color: var(--text-dark);
                    font-weight: 700;
                }

                .home-featured-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                    gap: 20px;
                }

                .home-featured-card {
                    background: #fff;
                    border-radius: 20px;
                    padding: 20px;
                    border: 1px solid rgba(0,0,0,0.05);
                    box-shadow: 0 6px 18px rgba(15,23,42,0.08);
                    display: flex;
                    flex-direction: column;
                    gap: 10px;
                }

                .home-featured-tag {
                    display: inline-flex;
                    align-items: center;
                    gap: 6px;
                    font-size: 0.72rem;
                    font-weight: 700;
                    text-transform: uppercase;
                    color: var(--primary);
                    background: var(--accent-soft);
                    padding: 4px 10px;
                    border-radius: 999px;
                }

                .home-featured-meta {
                    display: flex;
                    justify-content: space-between;
                    font-size: 0.86rem;
                    color: var(--text-muted);
                }

                .home-featured-price {
                    font-size: 1.25rem;
                    font-weight: 800;
                }

                .home-featured-price span {
                    font-size: 0.85rem;
                    color: var(--text-muted);
                    font-weight: 600;
                }

                .home-featured-link {
                    margin-top: auto;
                    color: var(--primary);
                    font-weight: 700;
                    text-decoration: none;
                }

                .home-featured-empty {
                    grid-column: 1 / -1;
                    text-align: center;
                    padding: 24px;
                    color: var(--text-muted);
                }

                .home-verified {
                    padding: 60px 0 80px;
                }

                .home-verified-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
                    gap: 24px;
                }

                .home-verified-column h3 {
                    margin: 0 0 14px;
                    font-size: 1.2rem;
                }

                .home-verified-card {
                    background: #fff;
                    border-radius: 16px;
                    padding: 16px;
                    border: 1px solid rgba(0,0,0,0.05);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 12px;
                }

                .home-verified-card strong {
                    display: block;
                }

                .home-verified-card span {
                    display: block;
                    font-size: 0.82rem;
                    color: var(--text-muted);
                }

                .home-verified-pill {
                    display: inline-flex;
                    align-items: center;
                    gap: 6px;
                    font-size: 0.76rem;
                    font-weight: 700;
                    padding: 6px 10px;
                    border-radius: 999px;
                    background: rgba(15,23,42,0.06);
                }

                .home-verified-empty {
                    padding: 12px 0 4px;
                    color: var(--text-muted);
                }

                .home-skeleton-card {
                    min-height: 120px;
                    background: linear-gradient(120deg, rgba(148, 163, 184, 0.15), rgba(226, 232, 240, 0.5), rgba(148, 163, 184, 0.15));
                    background-size: 200% 100%;
                    animation: homeSkeletonPulse 1.4s ease-in-out infinite;
                    border-radius: 20px;
                }

                @keyframes homeSkeletonPulse {
                    0% { background-position: 0% 50%; opacity: 0.7; }
                    50% { background-position: 100% 50%; opacity: 0.4; }
                    100% { background-position: 0% 50%; opacity: 0.7; }
                }

                @keyframes homeSlideIn {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }

                @media (max-width: 900px) {
                    .home-slideshow-inner {
                        grid-template-columns: 1fr;
                    }
                }

                @media (max-width: 720px) {
                    .home-banner-inner {
                        padding: 24px;
                    }

                    .home-section-head {
                        align-items: flex-start;
                    }
                }
            `}</style>
        </div>
    );
};
