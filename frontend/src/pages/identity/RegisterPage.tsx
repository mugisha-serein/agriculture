import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../../api/client';
import { Button } from '../../components/ui';
import { Shovel, Truck, ShoppingBag, ArrowRight, ArrowLeft, CheckCircle2, User, Phone, Mail, Lock } from 'lucide-react';
import agricultureVideo from '../../assets/videos/agriculture.mp4';
import { reportApiError, reportPasswordMismatchError, reportRequiredFieldsError } from '../../lib/identityError';
import { VerificationForm } from './VerificationForm';
import { SystemInlineError } from '../Error';

type Role = 'buyer' | 'seller' | 'transporter';

export const RegisterPage: React.FC = () => {
    const [step, setStep] = useState(1);
    const [role, setRole] = useState<Role | null>(null);
    const [formData, setFormData] = useState({
        email: '',
        password: '',
        confirmPassword: '',
        first_name: '',
        last_name: '',
        phone: '',
        company_name: '',
    });
    const [isLoading, setIsLoading] = useState(false);
    const [activationToken, setActivationToken] = useState<string>('');

    // const navigate = useNavigate();

    const handleRoleSelect = (selectedRole: Role) => {
        setRole(selectedRole);
    };

    const handleNextStep = (e: React.FormEvent) => {
        e.preventDefault();
        if (!role) {
            reportRequiredFieldsError('Registration Validation Error', ['Role selection']);
            return;
        }
        setStep(2);
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (formData.password !== formData.confirmPassword) {
            reportPasswordMismatchError('Registration Validation Error');
            return;
        }

        setIsLoading(true);

        try {
            const { confirmPassword, ...dataToSubmit } = formData;
            const response = await api.post('/identity/register/', {
                ...dataToSubmit,
                role: role,
            });
            setActivationToken(response.data.activation_token);
            if (role === 'buyer') {
                setStep(4);
            } else {
                setStep(3);
            }
        } catch (err: unknown) {
            reportApiError('Registration Failed', err);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div style={{ display: 'flex', height: '100vh', width: '100%', backgroundColor: '#fff', overflow: 'hidden' }}>
            {/* Left Side: Visuals & Branding */}
            <div className="register-left" style={{ flex: 1.4, position: 'relative', flexDirection: 'column', overflow: 'hidden', borderTopRightRadius: '48px', borderBottomRightRadius: '48px', boxShadow: '10px 0 24px rgba(0,0,0,0.1)', zIndex: 1, animation: 'slideInLeft 1s cubic-bezier(0.16, 1, 0.3, 1) forwards' }}>
                <video
                    autoPlay
                    loop
                    muted
                    playsInline
                    style={{ position: 'absolute', width: '100%', height: '100%', objectFit: 'cover' }}
                >
                    <source src={agricultureVideo} type="video/mp4" />
                </video>
                <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(135deg, rgba(6, 78, 59, 0.96), rgba(19, 175, 123, 0.07))' }} />

                <div style={{ position: 'relative', zIndex: 10, display: 'flex', flexDirection: 'column', height: '100%', justifyContent: 'space-between', padding: '60px', color: 'white' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <Button variant="ghost" size="sm" onClick={() => window.history.back()} style={{ color: 'white', padding: 0 }}>
                            <ArrowLeft size={24} />
                        </Button>
                        <span style={{ fontSize: '1.5rem', fontWeight: 800, letterSpacing: '-0.5px' }}>AgriMarket</span>
                    </div>

                    <div style={{ maxWidth: '480px' }}>
                        <h1 style={{ fontSize: '3.5rem', fontWeight: 800, lineHeight: 1.1, marginBottom: '24px', color: 'white' }}>
                            Join the<br />Ecosystem.
                        </h1>
                        <p style={{ fontSize: '1.25rem', opacity: 0.9, lineHeight: 1.6, marginBottom: '40px' }}>
                            Whether you're selling crops, transporting goods, or buying fresh produce, AgriMarket provides the tools you need to succeed.
                        </p>
                    </div>

                    <div style={{ fontSize: '0.9rem', opacity: 0.7 }}>
                        &copy; 2026 Triple S International. Empowering Agriculture.
                    </div>
                </div>
            </div>

            {/* Right Side: Registration Form */}
            <div className="register-right" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflowY: 'auto', padding: '40px 20px', background: '#ffffff', opacity: 0, animation: 'slideInBottom 1s cubic-bezier(0.16, 1, 0.3, 1) 0.2s forwards' }}>
                <div style={{ width: '100%', maxWidth: '500px', margin: 'auto' }}>

                    {/* Step Indicator */}
                    <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '32px', gap: '8px' }}>
                        {[1, 2, 3, 4].map((s) => (
                            <div key={s} style={{
                                width: '40px',
                                height: '4px',
                                borderRadius: 'var(--radius-full)',
                                background: s <= step ? 'var(--primary)' : '#e5e7eb',
                                display: (role === 'buyer' && s === 3) ? 'none' : 'block',
                                transition: 'var(--transition-normal)'
                            }} />
                        ))}
                    </div>

                    {step === 1 && (
                        <div style={{ animation: 'fadeIn 0.5s ease' }}>
                            <h2 style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '8px', color: 'var(--text-dark)' }}>Choose your role</h2>
                            <p style={{ color: 'var(--text-muted)', fontSize: '1rem', marginBottom: '32px' }}>How would you like to participate in the marketplace?</p>
                            <SystemInlineError marginBottom="24px" />

                            <form onSubmit={handleNextStep}>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '16px', marginBottom: '32px' }}>
                                    <CompactRoleCard
                                        icon={<ShoppingBag size={24} />}
                                        title="Buyer"
                                        desc="Purchase produce directly from verified farmers."
                                        selected={role === 'buyer'}
                                        onClick={() => handleRoleSelect('buyer')}
                                    />
                                    <CompactRoleCard
                                        icon={<Shovel size={24} />}
                                        title="Seller / Farmer"
                                        desc="List your crops and reach buyers nationwide."
                                        selected={role === 'seller'}
                                        onClick={() => handleRoleSelect('seller')}
                                    />
                                    <CompactRoleCard
                                        icon={<Truck size={24} />}
                                        title="Transporter"
                                        desc="Coordinate logistics and deliver produce safely."
                                        selected={role === 'transporter'}
                                        onClick={() => handleRoleSelect('transporter')}
                                    />
                                </div>
                                <Button type="submit" size="lg" fullWidth style={{ height: '56px', fontSize: '1.1rem' }}>
                                    Continue <ArrowRight size={20} />
                                </Button>
                            </form>

                            <div style={{ marginTop: '32px', textAlign: 'center', fontSize: '0.95rem', color: 'var(--text-muted)' }}>
                                Already have an account?{' '}
                                <Link to="/login" style={{ color: 'var(--primary)', fontWeight: 600, textDecoration: 'underline' }}>
                                    Sign in
                                </Link>
                            </div>
                        </div>
                    )}

                    {step === 2 && (
                        <div style={{ animation: 'fadeIn 0.5s ease' }}>
                            <button onClick={() => setStep(1)} style={{ background: 'none', border: 'none', display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)', marginBottom: '24px', fontWeight: 600, cursor: 'pointer', padding: 0 }}>
                                <ArrowLeft size={16} /> Back to roles
                            </button>
                            <h2 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '8px', color: 'var(--text-dark)' }}>Create your account</h2>
                            <p style={{ color: 'var(--text-muted)', fontSize: '1rem', marginBottom: '32px' }}>Registering as a <strong><span style={{ textTransform: 'capitalize' }}>{role}</span></strong>.</p>
                            <SystemInlineError marginBottom="24px" />

                            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                                    <RobustInput icon={<User size={18} />} label="First Name" name="first_name" value={formData.first_name} onChange={handleChange} required />
                                    <RobustInput icon={<User size={18} />} label="Last Name" name="last_name" value={formData.last_name} onChange={handleChange} required />
                                </div>
                                <RobustInput icon={<Mail size={18} />} label="Email Address" type="email" name="email" value={formData.email} onChange={handleChange} required />
                                <RobustInput icon={<Phone size={18} />} label="Phone Number" name="phone" value={formData.phone} onChange={handleChange} required />

                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                                    <RobustInput icon={<Lock size={18} />} label="Password" type="password" name="password" value={formData.password} onChange={handleChange} required />
                                    <RobustInput icon={<Lock size={18} />} label="Confirm" type="password" name="confirmPassword" value={formData.confirmPassword} onChange={handleChange} required />
                                </div>
                                <Button type="submit" size="lg" isLoading={isLoading} fullWidth style={{ height: '56px', fontSize: '1.1rem', marginTop: '12px' }}>
                                    Register Account <ArrowRight size={20} />
                                </Button>
                            </form>
                        </div>
                    )}

                    {step === 3 && role !== 'buyer' && (
                        <div style={{ animation: 'fadeIn 0.5s ease' }}>
                            <VerificationForm
                                title="Identity Verification"
                                description={`To ensure a safe marketplace, please verify your identity before you can start ${role === 'seller' ? 'listing products' : 'coordinating shipments'}.`}
                                activationToken={activationToken}
                                submitLabel="Submit Verification"
                                onSubmitted={() => setStep(4)}
                            />
                        </div>
                    )}

                    {step === 4 && (
                        <div style={{ textAlign: 'center', padding: '40px 0', animation: 'fadeIn 0.5s ease' }}>
                            <div style={{ color: 'var(--success)', marginBottom: '24px', display: 'flex', justifyContent: 'center' }}>
                                <CheckCircle2 size={80} strokeWidth={1.5} />
                            </div>
                            <h2 style={{ fontSize: '2.25rem', fontWeight: 800, marginBottom: '16px' }}>Welcome Aboard!</h2>

                            {role === 'buyer' ? (
                                <>
                                    <p style={{ color: 'var(--text-muted)', marginBottom: '40px', maxWidth: '400px', margin: '0 auto 40px', fontSize: '1.1rem' }}>
                                        Your account has been created successfully. You can now log in and explore the marketplace.
                                    </p>
                                    <Link to="/login" style={{ textDecoration: 'none' }}>
                                        <Button size="lg" fullWidth style={{ height: '56px', fontSize: '1.1rem' }}>Go to Login</Button>
                                    </Link>
                                </>
                            ) : (
                                <>
                                    <p style={{ color: 'var(--text-muted)', marginBottom: '40px', maxWidth: '450px', margin: '0 auto 40px', fontSize: '1.1rem', lineHeight: 1.6 }}>
                                        Your registration and verification documents have been submitted!<br /><br />
                                        Our team will review your account closely (usually takes 24-48 hours).
                                        You will be able to sign in once an administrator approves your account.
                                    </p>
                                    <Link to="/login" style={{ textDecoration: 'none' }}>
                                        <Button size="md" variant="outline" fullWidth style={{ height: '20px', fontSize: '1.1rem', border: "none" }}><ArrowLeft /> Login</Button>
                                    </Link>
                                </>
                            )}
                        </div>
                    )}
                </div>
            </div>

            <style>{`
                .register-left { display: none !important; }
                .mobile-header { display: flex !important; }
                
                @media (min-width: 900px) {
                    .register-left { display: flex !important; }
                    .mobile-header { display: none !important; }
                }

                @keyframes slideInLeft {
                    from { transform: translateX(-10%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }

                @keyframes slideInBottom {
                    from { transform: translateY(40px); opacity: 0; }
                    to { transform: translateY(0); opacity: 1; }
                }
                
                @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }

                .robust-input-wrapper input {
                    transition: all 0.2s ease;
                }
                .robust-input-wrapper input:focus {
                    border-color: var(--primary) !important;
                    box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.2) !important;
                }
                
                /* Hide scrollbar for form area */
                .register-right::-webkit-scrollbar {
                    width: 6px;
                }
                .register-right::-webkit-scrollbar-thumb {
                    background-color: rgba(0,0,0,0.1);
                    border-radius: 10px;
                }
            `}</style>
        </div>
    );
};

const CompactRoleCard = ({ icon, title, desc, onClick, selected }: { icon: React.ReactNode, title: string, desc: string, onClick: () => void, selected: boolean }) => (
    <div onClick={onClick} className="compact-role-card" style={{
        padding: '16px 20px',
        borderRadius: 'var(--radius-md)',
        border: `2px solid ${selected ? 'var(--primary)' : '#e5e7eb'}`,
        backgroundColor: selected ? 'rgba(16, 185, 129, 0.05)' : '#fff',
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        display: 'flex',
        gap: '16px',
        alignItems: 'center'
    }}>
        <div style={{
            width: '48px',
            height: '48px',
            background: selected ? 'var(--primary)' : 'var(--accent-soft)',
            color: selected ? '#fff' : 'var(--primary)',
            borderRadius: 'var(--radius-md)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.2s ease',
            flexShrink: 0
        }}>
            {icon}
        </div>
        <div style={{ flex: 1 }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '2px', color: 'var(--text-dark)' }}>{title}</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', lineHeight: 1.4 }}>{desc}</p>
        </div>
        <div style={{
            width: '20px',
            height: '20px',
            borderRadius: '50%',
            border: `2px solid ${selected ? 'var(--primary)' : '#d1d5db'}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
        }}>
            {selected && <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: 'var(--primary)' }} />}
        </div>
        <style>{`
      .compact-role-card:hover {
        border-color: var(--primary);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
      }
    `}</style>
    </div>
);

const RobustInput = ({ icon, label, containerStyle, ...props }: any) => (
    <div className="robust-input-wrapper" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <label style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-muted)' }}>{label}</label>
        <div style={{ position: 'relative' }}>
            {icon && (
                <div style={{ position: 'absolute', top: '50%', left: '16px', transform: 'translateY(-50%)', color: '#9ca3af', pointerEvents: 'none' }}>
                    {icon}
                </div>
            )}
            <input
                className="custom-input"
                style={{
                    width: '100%',
                    height: '48px',
                    padding: icon ? '10px 16px 10px 44px' : '10px 16px',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid #e5e7eb',
                    fontSize: '0.95rem',
                    outline: 'none',
                    ...containerStyle
                }}
                {...props}
            />
        </div>
    </div>
);
