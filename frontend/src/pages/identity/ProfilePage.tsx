import React, { useState, useEffect } from 'react';
import { api } from '../../api/client';
import { useAuthStore } from '../../store/authStore';
import { Button } from '../../components/ui';
import {
    User, ShieldCheck, ShieldAlert, Clock, MapPin, Phone, Mail,
    Building, CheckCircle2, AlertTriangle, Lock, Eye, EyeOff,
    Settings, KeyRound, Bell, AlertCircle, Edit3, Save, X, Camera
} from 'lucide-react';
import { reportApiError, reportPasswordMismatchError, reportPasswordMinLengthError } from '../../lib/identityError';
import { VerificationForm } from './VerificationForm';

interface VerificationStatus {
    status: 'pending' | 'verified' | 'rejected' | 'none';
    submitted_at?: string;
    notes?: string;
}

type Tab = 'profile' | 'password' | 'settings';
const TAB_STORAGE_KEY = 'agri_profile_active_tab';
const isTab = (value: string): value is Tab => value === 'profile' || value === 'password' || value === 'settings';

export const ProfilePage: React.FC = () => {
    const { user, setAuth } = useAuthStore();

    const [verification, setVerification] = useState<VerificationStatus>({ status: 'none' });
    const [isLoading, setIsLoading] = useState(true);
    const [showVerificationForm, setShowVerificationForm] = useState(false);
    const [activeTab, setActiveTab] = useState<Tab>(() => {
        if (typeof window === 'undefined') return 'profile';
        const savedTab = window.localStorage.getItem(TAB_STORAGE_KEY);
        return savedTab && isTab(savedTab) ? savedTab : 'profile';
    });

    // Edit info state
    const [editing, setEditing] = useState(false);
    const [firstName, setFirstName] = useState(user?.first_name || '');
    const [lastName, setLastName] = useState(user?.last_name || '');
    const [phone, setPhone] = useState(user?.phone || '');
    const [saveLoading, setSaveLoading] = useState(false);
    const [saveSuccess, setSaveSuccess] = useState(false);

    // Password form
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [showCurrent, setShowCurrent] = useState(false);
    const [showNew, setShowNew] = useState(false);
    const [showConfirm, setShowConfirm] = useState(false);
    const [pwLoading, setPwLoading] = useState(false);
    const [pwSuccess, setPwSuccess] = useState(false);

    // Avatar state
    const [avatarUrl, setAvatarUrl] = useState<string | null>(null);
    const [snapFlash, setSnapFlash] = useState(false);
    const fileInputRef = React.useRef<HTMLInputElement>(null);

    const handleAvatarClick = () => fileInputRef.current?.click();

    const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        const url = URL.createObjectURL(file);
        setAvatarUrl(url);
        // Trigger snapshot flash
        setSnapFlash(true);
        setTimeout(() => setSnapFlash(false), 600);
        // TODO: upload file to server via api.patch or FormData
    };

    const [notifOrders, setNotifOrders] = useState(true);
    const [notifMessages, setNotifMessages] = useState(true);
    const [notifMarket, setNotifMarket] = useState(false);
    const [notifNewsletter, setNotifNewsletter] = useState(false);

    useEffect(() => {
        fetchVerification();
    }, []);

    useEffect(() => {
        if (typeof window === 'undefined') return;
        window.localStorage.setItem(TAB_STORAGE_KEY, activeTab);
    }, [activeTab]);

    useEffect(() => {
        if (typeof window === 'undefined') return;
        const syncTabSelection = (event: StorageEvent) => {
            if (event.key !== TAB_STORAGE_KEY || !event.newValue || !isTab(event.newValue)) return;
            setActiveTab(event.newValue);
        };

        window.addEventListener('storage', syncTabSelection);
        return () => window.removeEventListener('storage', syncTabSelection);
    }, []);

    const fetchVerification = async () => {
        setIsLoading(true);
        try {
            const response = await api.get('/verification/me/');
            const verificationData = response.data as VerificationStatus;
            setVerification(verificationData);

            if (verificationData.status === 'verified' && user && !user.is_verified) {
                const token = sessionStorage.getItem('access_token') || '';
                const refresh = sessionStorage.getItem('refresh_token') || '';
                if (token && refresh) {
                    setAuth({ ...user, is_verified: true }, token, refresh);
                }
            }
        } catch (err: unknown) {
            const statusCode = (err as { response?: { status?: number } })?.response?.status;
            if (statusCode === 404) {
                setVerification({ status: user?.is_verified ? 'verified' : 'none' });
            } else {
                reportApiError('Verification Status Load Failed', err);
            }
        } finally {
            setIsLoading(false);
        }
    };

    const startEditing = () => {
        setFirstName(user?.first_name || '');
        setLastName(user?.last_name || '');
        setPhone(user?.phone || '');
        setSaveSuccess(false);
        setEditing(true);
    };

    const cancelEditing = () => {
        setEditing(false);
    };

    const handleSaveProfile = async (e: React.FormEvent) => {
        e.preventDefault();
        setSaveLoading(true);
        setSaveSuccess(false);
        try {
            const response = await api.patch('/auth/me/', { first_name: firstName, last_name: lastName, phone });
            // Update auth store
            if (user) {
                const token = sessionStorage.getItem('access_token') || '';
                const refresh = sessionStorage.getItem('refresh_token') || '';
                setAuth({ ...user, first_name: firstName, last_name: lastName, phone }, token, refresh);
            }
            setSaveSuccess(true);
            setEditing(false);
            void response;
        } catch (err: unknown) {
            reportApiError('Profile Update Failed', err);
        } finally {
            setSaveLoading(false);
        }
    };

    const handlePasswordUpdate = async (e: React.FormEvent) => {
        e.preventDefault();
        setPwSuccess(false);
        if (newPassword !== confirmPassword) {
            reportPasswordMismatchError('Password Validation Error');
            return;
        }
        if (newPassword.length < 8) {
            reportPasswordMinLengthError('Password Validation Error', 8);
            return;
        }
        setPwLoading(true);
        try {
            await api.post('/auth/change-password/', { current_password: currentPassword, new_password: newPassword });
            setPwSuccess(true);
            setCurrentPassword(''); setNewPassword(''); setConfirmPassword('');
        } catch (err: unknown) {
            reportApiError('Password Update Failed', err);
        } finally {
            setPwLoading(false);
        }
    };

    const statusConfig = {
        verified: { color: 'var(--success)', bg: 'rgba(16,185,129,0.08)', border: 'rgba(16,185,129,0.25)', icon: <CheckCircle2 size={18} />, label: 'Verified' },
        pending: { color: '#f59e0b', bg: 'rgba(245,158,11,0.08)', border: 'rgba(245,158,11,0.25)', icon: <Clock size={18} />, label: 'Pending Review' },
        rejected: { color: 'var(--error)', bg: 'rgba(239,68,68,0.08)', border: 'rgba(239,68,68,0.25)', icon: <AlertTriangle size={18} />, label: 'Rejected' },
        none: { color: 'var(--text-muted)', bg: 'rgba(0,0,0,0.03)', border: 'rgba(0,0,0,0.08)', icon: <ShieldAlert size={18} />, label: 'Not Submitted' },
    };
    const resolvedVerification = user?.is_verified && verification.status !== 'verified'
        ? { ...verification, status: 'verified' as const }
        : verification;
    const verificationStatus = resolvedVerification.status;
    const st = statusConfig[verificationStatus] || statusConfig.none;
    const initials = [user?.first_name?.[0], user?.last_name?.[0]].filter(Boolean).join('') || 'U';
    const roleLabel = user?.role ? user.role.charAt(0).toUpperCase() + user.role.slice(1) : 'User';
    const verificationLocked = verificationStatus === 'verified' || verificationStatus === 'pending';
    const isVerified = verificationStatus === 'verified';
    const verificationButtonStyle: React.CSSProperties =
        verificationStatus === 'verified'
            ? { background: 'rgba(16,185,129,0.12)', color: 'var(--success)', border: '1px solid rgba(16,185,129,0.32)', cursor: 'not-allowed' }
            : verificationStatus === 'pending'
                ? { background: 'rgba(245,158,11,0.12)', color: '#b45309', border: '1px solid rgba(245,158,11,0.35)', cursor: 'not-allowed' }
                : verificationStatus === 'rejected'
                    ? { background: 'var(--accent-soft)', color: 'var(--primary)', border: '1px solid rgba(45,90,39,0.28)' }
                    : { background: 'var(--primary)', color: 'white', border: '1px solid var(--primary)' };

    useEffect(() => {
        if (verificationLocked) {
            setShowVerificationForm(false);
        }
    }, [verificationLocked]);

    const editInput = (label: string, value: string, onChange: (v: string) => void, icon: React.ReactNode, type = 'text', disabled = false) => (
        <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '8px' }}>{label}</label>
            <div style={{ position: 'relative' }}>
                <div style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: disabled ? '#d1d5db' : 'var(--primary)' }}>{icon}</div>
                <input
                    type={type}
                    value={value}
                    onChange={e => onChange(e.target.value)}
                    disabled={disabled}
                    style={{
                        width: '100%', boxSizing: 'border-box',
                        padding: '11px 14px 11px 42px',
                        border: `1.5px solid ${disabled ? '#f3f4f6' : editing ? '#d1d5db' : '#f3f4f6'}`,
                        borderRadius: '12px', fontSize: '0.925rem', outline: 'none',
                        background: disabled ? '#f9fafb' : editing ? 'white' : '#f9fafb',
                        color: disabled ? 'var(--text-muted)' : 'var(--text-dark)',
                        transition: 'border-color 0.2s, box-shadow 0.2s',
                    }}
                    onFocus={e => { if (!disabled) { e.target.style.borderColor = 'var(--primary)'; e.target.style.boxShadow = '0 0 0 3px rgba(16,185,129,0.1)'; } }}
                    onBlur={e => { e.target.style.borderColor = editing ? '#d1d5db' : '#f3f4f6'; e.target.style.boxShadow = 'none'; }}
                />
            </div>
        </div>
    );

    const pwInput = (label: string, value: string, onChange: (v: string) => void, show: boolean, toggle: () => void, autoComplete: string) => (
        <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '8px' }}>{label}</label>
            <div style={{ position: 'relative' }}>
                <div style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }}><Lock size={16} /></div>
                <input
                    type={show ? 'text' : 'password'}
                    value={value} onChange={e => onChange(e.target.value)}
                    autoComplete={autoComplete} required
                    style={{ width: '100%', boxSizing: 'border-box', padding: '11px 48px 11px 42px', border: '1.5px solid #e5e7eb', borderRadius: '12px', fontSize: '0.925rem', outline: 'none', background: '#fafafa', transition: 'border-color 0.2s, box-shadow 0.2s' }}
                    onFocus={e => { e.target.style.borderColor = 'var(--primary)'; e.target.style.boxShadow = '0 0 0 3px rgba(16,185,129,0.1)'; }}
                    onBlur={e => { e.target.style.borderColor = '#e5e7eb'; e.target.style.boxShadow = 'none'; }}
                />
                <button type="button" onClick={toggle} style={{ position: 'absolute', right: '14px', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}>
                    {show ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
            </div>
        </div>
    );

    const Toggle = ({ on, setOn }: { on: boolean; setOn: (v: boolean) => void }) => (
        <button onClick={() => setOn(!on)} style={{ width: 44, height: 24, borderRadius: 12, background: on ? 'var(--primary)' : '#d1d5db', border: 'none', cursor: 'pointer', position: 'relative', transition: 'background 0.2s', flexShrink: 0 }}>
            <div style={{ position: 'absolute', width: 18, height: 18, background: 'white', borderRadius: '50%', top: 3, left: on ? 23 : 3, transition: 'left 0.2s', boxShadow: '0 1px 4px rgba(0,0,0,0.2)' }} />
        </button>
    );

    if (isLoading) {
        return (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
                <div style={{ textAlign: 'center' }}>
                    <div style={{ width: 48, height: 48, border: '3px solid var(--accent-soft)', borderTopColor: 'var(--primary)', borderRadius: '50%', animation: 'spin 0.8s linear infinite', margin: '0 auto 16px' }} />
                    <p style={{ color: 'var(--text-muted)', fontWeight: 500 }}>Loading your profile...</p>
                    <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
                </div>
            </div>
        );
    }

    return (
        <div className="container" style={{ animation: 'fadeUp 0.55s cubic-bezier(0.16,1,0.3,1) forwards' }}>
            <style>{`
                @keyframes fadeUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
                @keyframes tabSwap { from { opacity: 0; transform: translateY(10px) scale(0.995); } to { opacity: 1; transform: translateY(0) scale(1); } }
                @keyframes cardFloatIn { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
                .tab-panel { animation: tabSwap 0.34s cubic-bezier(0.22,1,0.36,1) both; }
                .tab-panel .pcard { animation: cardFloatIn 0.45s cubic-bezier(0.22,1,0.36,1) both; }
                .tab-panel .pcard:nth-child(2) { animation-delay: 0.04s; }
                .tab-panel .pcard:nth-child(3) { animation-delay: 0.08s; }
                .pcard {
                    background: white;
                    border-radius: 20px;
                    border: 1px solid rgba(0,0,0,0.05);
                    box-shadow: 0 4px 22px rgba(15,23,42,0.06);
                    transition: transform 0.24s cubic-bezier(0.22,1,0.36,1), box-shadow 0.24s ease, border-color 0.24s ease;
                }
                .pcard:hover {
                    transform: translateY(-2px);
                    border-color: rgba(45,90,39,0.2);
                    box-shadow: 0 14px 32px rgba(15,23,42,0.1);
                }
                .tab-pill {
                    display: flex;
                    align-items: center;
                    gap: 7px;
                    padding: 9px 18px;
                    border-radius: 10px;
                    border: none;
                    font-size: 0.875rem;
                    font-weight: 600;
                    cursor: pointer;
                    transition: background 0.22s ease, color 0.22s ease, box-shadow 0.22s ease, transform 0.18s ease;
                    background: transparent;
                    color: var(--text-muted);
                    white-space: nowrap;
                }
                .tab-pill.active {
                    background: white;
                    color: var(--primary);
                    box-shadow: 0 6px 18px rgba(0,0,0,0.1);
                    transform: translateY(-1px);
                }
                .tab-pill:hover:not(.active) { background: rgba(0,0,0,0.05); color: var(--text-dark); transform: translateY(-1px); }
                .tab-pill:focus-visible { outline: 2px solid var(--primary-light); outline-offset: 2px; }
                .srow {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding: 16px 10px;
                    border-bottom: 1px solid rgba(0,0,0,0.05);
                    border-radius: 12px;
                    transition: background 0.2s ease, transform 0.2s ease;
                }
                .srow:hover { background: rgba(16,185,129,0.05); transform: translateX(2px); }
                .srow:last-child { border-bottom: none; }
                .avatar-wrap { position: relative; width: 125px; height: 125px; margin: 0 auto 20px; border-radius: 50%; }
                .camera-badge {
                    position: absolute;
                    bottom: 2px;
                    right: 2px;
                    width: 32px;
                    height: 32px;
                    border-radius: 50%;
                    background: var(--primary);
                    color: white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border: 3px solid white;
                    cursor: pointer;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.18);
                    transition: transform 0.18s ease, background 0.18s ease, box-shadow 0.18s ease;
                    z-index: 2;
                }
                .camera-badge:hover {
                    transform: scale(1.12);
                    background: var(--primary-dark);
                    box-shadow: 0 6px 16px rgba(0,0,0,0.24);
                }
                .verify-cta {
                    border-radius: 999px !important;
                    font-size: 0.82rem !important;
                    font-weight: 700 !important;
                    padding: 7px 14px !important;
                    letter-spacing: 0.02em;
                    transition: transform 0.18s ease, box-shadow 0.22s ease, filter 0.22s ease !important;
                }
                .verify-cta:hover:not(:disabled) {
                    transform: translateY(-1px);
                    box-shadow: 0 8px 18px rgba(45,90,39,0.26);
                    filter: brightness(1.03);
                }
                @keyframes snapShutter {
                    0%   { transform: scale(1); }
                    40%  { transform: scale(0.82); }
                    100% { transform: scale(1); }
                }
                .camera-badge.snap { animation: snapShutter 0.35s ease; }
                @keyframes snapFlash {
                    0%   { opacity: 0; }
                    15%  { opacity: 0.85; }
                    100% { opacity: 0; }
                }
                .snap-flash {
                    position: fixed; inset: 0; background: white;
                    pointer-events: none; z-index: 9999;
                    animation: snapFlash 0.55s ease-out forwards;
                }
                @media (prefers-reduced-motion: reduce) {
                    .tab-panel, .tab-panel .pcard, .camera-badge, .verify-cta, .tab-pill, .srow { animation: none !important; transition: none !important; }
                }
            `}</style>

            {/* Header Row */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '28px', flexWrap: 'wrap', gap: '12px' }}>
                <div>
                    <h1 style={{ fontSize: '2rem', fontWeight: 800, letterSpacing: '-0.5px', color: 'var(--text-dark)', marginBottom: '4px' }}>My Profile</h1>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>Manage your account information, password and preferences.</p>
                </div>
                {/* Tabs */}
                <div style={{ display: 'flex', gap: '4px', background: 'rgba(0,0,0,0.04)', padding: '4px', borderRadius: '14px' }}>
                    {([['profile', 'Profile', <User size={15} />], ['password', 'Password', <KeyRound size={15} />], ['settings', 'Settings', <Settings size={15} />]] as [Tab, string, React.ReactNode][]).map(([id, label, icon]) => (
                        <button
                            key={id}
                            type="button"
                            className={`tab-pill ${activeTab === id ? 'active' : ''}`}
                            aria-pressed={activeTab === id}
                            onClick={() => setActiveTab(id)}
                        >
                            {icon}{label}
                        </button>
                    ))}
                </div>
            </div>

            {/* â”€â”€ PROFILE TAB â”€â”€ */}
            {activeTab === 'profile' && (
                <div className="tab-panel" style={{ display: 'grid', gridTemplateColumns: '350px 1fr', gap: '24px', alignItems: 'start' }}>
                    {/* Left: Avatar + meta */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                        <div className="pcard" style={{ padding: '28px 24px 24px', textAlign: 'center' }}>
                            {/* Hidden file input */}
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept="image/*"
                                style={{ display: 'none' }}
                                onChange={handleAvatarChange}
                            />

                            {/* Snapshot flash overlay */}
                            {snapFlash && <div className="snap-flash" />}

                            {/* Avatar with camera badge */}
                            <div className="avatar-wrap">
                                {/* Avatar image or initials */}
                                {avatarUrl ? (
                                    <img
                                        src={avatarUrl}
                                        alt="Profile"
                                        style={{ width: 125, height: 125, borderRadius: '50%', objectFit: 'cover', boxShadow: '0 8px 24px rgba(16,185,129,0.25)', display: 'block' }}
                                    />
                                ) : (
                                    <div style={{
                                        width: 125, height: 125,
                                        background: 'linear-gradient(135deg, var(--primary), var(--primary-dark))',
                                        borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
                                        fontSize: '2.2rem', fontWeight: 800, color: 'white',
                                        boxShadow: '0 8px 24px rgba(16,185,129,0.25)'
                                    }}>
                                        {initials}
                                    </div>
                                )}

                                {/* Camera badge â€” attached outside avatar bottom-right */}
                                <button
                                    className={`camera-badge${snapFlash ? ' snap' : ''}`}
                                    onClick={handleAvatarClick}
                                    title="Change photo"
                                    type="button"
                                >
                                    <Camera size={14} />
                                </button>
                            </div>

                            <h2 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-dark)', marginBottom: '12px' }}>
                                {user?.first_name} {user?.last_name}
                            </h2>
                            <span style={{ background: 'var(--accent-soft)', color: 'var(--primary)', fontWeight: 800, fontSize: '0.7rem', letterSpacing: '0.08em', textTransform: 'uppercase', padding: '4px 10px', borderRadius: 'var(--radius-full)', display: 'block', width: 'fit-content', margin: '0 auto 6px' }}>
                                {roleLabel}
                            </span>
                            <span style={{ background: st.bg, color: st.color, border: `1px solid ${st.border}`, fontWeight: 600, fontSize: '0.7rem', letterSpacing: '0.08em', textTransform: 'uppercase', padding: '4px 10px', borderRadius: 'var(--radius-full)', display: 'flex', alignItems: 'center', gap: '4px', width: 'fit-content', margin: '0 auto' }}>
                                {st.icon} {st.label}
                            </span>
                        </div>

                        {/* Account meta */}
                        <div className="pcard" style={{ padding: '20px 20px 8px' }}>
                            <p style={{ fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--text-muted)', marginBottom: '14px', paddingBottom: '10px', borderBottom: '1px solid rgba(0,0,0,0.05)' }}>Account Info</p>
                            {[
                                [<Mail size={14} />, 'Email', user?.email],
                                [<Phone size={14} />, 'Phone', user?.phone || '-'],
                                [<User size={14} />, 'Role', roleLabel],
                                [isVerified ? <ShieldCheck size={14} /> : <ShieldAlert size={14} />, 'Verified', isVerified ? 'Yes' : 'No'],
                            ].map(([icon, label, val]) => (
                                <div key={String(label)} style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '10px 0', borderBottom: '1px solid rgba(0,0,0,0.04)' }}>
                                    <div style={{ width: 30, height: 30, borderRadius: '8px', background: 'var(--accent-soft)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--primary)', flexShrink: 0 }}>
                                        {icon}
                                    </div>
                                    <div style={{ flex: 1, minWidth: 0 }}>
                                        <div style={{ fontSize: '0.68rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '1px' }}>{label}</div>
                                        <div style={{ fontSize: '0.83rem', fontWeight: 600, color: 'var(--text-dark)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{val}</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Right column */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                        {/* Editable personal info */}
                        <div className="pcard" style={{ padding: '32px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                                <div>
                                    <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-dark)', marginBottom: '2px' }}>Personal Information</h3>
                                    <p style={{ fontSize: '0.83rem', color: 'var(--text-muted)' }}>Your name and contact details.</p>
                                </div>
                                {!editing ? (
                                    <button onClick={startEditing} style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 16px', borderRadius: '10px', border: '1.5px solid #e5e7eb', background: 'white', color: 'var(--text-dark)', fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer', transition: 'all 0.2s' }}>
                                        <Edit3 size={15} /> Edit
                                    </button>
                                ) : (
                                    <div style={{ display: 'flex', gap: '8px' }}>
                                        <button onClick={cancelEditing} style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 14px', borderRadius: '10px', border: '1.5px solid #e5e7eb', background: 'white', color: 'var(--text-muted)', fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer' }}>
                                            <X size={15} /> Cancel
                                        </button>
                                        <button form="profile-form" type="submit" disabled={saveLoading} style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 16px', borderRadius: '10px', border: 'none', background: 'var(--primary)', color: 'white', fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer' }}>
                                            <Save size={15} /> {saveLoading ? 'Savingâ€¦' : 'Save'}
                                        </button>
                                    </div>
                                )}
                            </div>

                            {saveSuccess && (
                                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: '12px', padding: '12px 16px', marginBottom: '20px', color: 'var(--success)', fontWeight: 600, fontSize: '0.875rem' }}>
                                    <CheckCircle2 size={17} /> Profile updated successfully!
                                </div>
                            )}

                            <form id="profile-form" onSubmit={handleSaveProfile}>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                                    {editInput('First Name', editing ? firstName : (user?.first_name || ''), setFirstName, <User size={16} />, 'text', !editing)}
                                    {editInput('Last Name', editing ? lastName : (user?.last_name || ''), setLastName, <User size={16} />, 'text', !editing)}
                                </div>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                                    {editInput('Email Address', user?.email || '', () => { }, <Mail size={16} />, 'email', true)}
                                    {editInput('Phone Number', editing ? phone : (user?.phone || ''), setPhone, <Phone size={16} />, 'tel', !editing)}
                                </div>
                            </form>
                        </div>

                        {/* Verification Card */}
                        <div className="pcard" style={{ padding: '32px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
                                <div>
                                    <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-dark)', marginBottom: '2px' }}>Identity Verification</h3>
                                    <p style={{ fontSize: '0.83rem', color: 'var(--text-muted)' }}>KYC compliance required for full marketplace access.</p>
                                </div>
                                <div style={{ background: st.bg, color: st.color, padding: '6px 12px', borderRadius: 'var(--radius-full)', fontSize: '0.78rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '6px', whiteSpace: 'nowrap' }}>
                                    {st.icon} {st.label}
                                </div>
                            </div>
                            <div style={{ background: 'rgba(0,0,0,0.025)', borderRadius: '14px', padding: '16px', marginBottom: '20px' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', ...(resolvedVerification.submitted_at ? { marginBottom: '10px' } : {}) }}>
                                    <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-muted)' }}>Status</span>
                                    <span style={{ fontWeight: 700, color: st.color, textTransform: 'capitalize' }}>
                                        {verificationStatus === 'none' ? 'Not Submitted' : verificationStatus}
                                    </span>
                                </div>
                                {resolvedVerification.submitted_at && (
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-muted)' }}>Submitted</span>
                                        <span style={{ fontWeight: 500, color: 'var(--text-dark)', fontSize: '0.875rem' }}>
                                            {new Date(resolvedVerification.submitted_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
                                        </span>
                                    </div>
                                )}
                                {resolvedVerification.notes && (
                                    <div style={{ marginTop: '12px', padding: '12px', background: 'rgba(239,68,68,0.07)', borderRadius: '10px', fontSize: '0.85rem', color: 'var(--error)' }}>
                                        <strong>Note:</strong> {resolvedVerification.notes}
                                    </div>
                                )}
                            </div>
                            {verificationStatus === 'pending' && (
                                <p style={{ fontSize: '0.84rem', color: 'var(--text-muted)', lineHeight: 1.6, marginBottom: '16px', padding: '10px 14px', background: 'rgba(245,158,11,0.07)', borderRadius: '10px', border: '1px solid rgba(245,158,11,0.2)' }}>
                                    Your documents are under review. We will notify you once complete.
                                </p>
                            )}
                            {verificationStatus === 'verified' && (
                                <p style={{ fontSize: '0.84rem', color: 'var(--text-muted)', lineHeight: 1.6, marginBottom: '16px', padding: '10px 14px', background: 'rgba(16,185,129,0.06)', borderRadius: '10px', border: '1px solid rgba(16,185,129,0.18)' }}>
                                    Your account is fully verified for all marketplace operations.
                                </p>
                            )}
                            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                                <Button
                                    className="verify-cta"
                                    size="sm"
                                    disabled={verificationLocked}
                                    style={verificationButtonStyle}
                                    onClick={() => {
                                        if (!verificationLocked) {
                                            setShowVerificationForm(true);
                                        }
                                    }}
                                >
                                    {verificationStatus === 'verified' && <CheckCircle2 size={14} />}
                                    {verificationStatus === 'pending' && <Clock size={14} />}
                                    {verificationStatus === 'rejected' && <AlertTriangle size={14} />}
                                    {verificationStatus === 'none' && <ShieldCheck size={14} />}
                                    {verificationStatus === 'verified'
                                        ? 'Verified'
                                        : verificationStatus === 'pending'
                                            ? 'Under Review'
                                            : verificationStatus === 'rejected'
                                                ? 'Re-submit Verification'
                                                : 'Submit Verification'}
                                </Button>
                            </div>

                            {showVerificationForm && !verificationLocked && (
                                <div style={{ marginTop: '20px', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '14px', padding: '20px', background: 'rgba(255,255,255,0.85)' }}>
                                    <VerificationForm
                                        title={verificationStatus === 'rejected' ? 'Re-submit Verification' : 'Identity Verification'}
                                        description="Upload your document details below so our team can verify your account."
                                        submitLabel={verificationStatus === 'rejected' ? 'Re-submit Verification' : 'Submit Verification'}
                                        onSubmitted={() => {
                                            setShowVerificationForm(false);
                                            void fetchVerification();
                                        }}
                                    />
                                </div>
                            )}
                        </div>

                        {/* Business Details (non-buyer) */}
                        {user?.role !== 'buyer' && (
                            <div className="pcard" style={{ padding: '32px' }}>
                                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-dark)', marginBottom: '20px' }}>Business Details</h3>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                                    {editInput('Entity / Business Name', '', () => { }, <Building size={16} />, 'text', true)}
                                    {editInput('Location', '', () => { }, <MapPin size={16} />, 'text', true)}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* â”€â”€ PASSWORD TAB â”€â”€ */}
            {activeTab === 'password' && (
                <div className="tab-panel" style={{ maxWidth: '560px' }}>
                    <div className="pcard" style={{ padding: '36px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '8px' }}>
                            <div style={{ width: 44, height: 44, background: 'var(--accent-soft)', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--primary)' }}>
                                <KeyRound size={22} />
                            </div>
                            <div>
                                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-dark)' }}>Update Password</h3>
                                <p style={{ fontSize: '0.83rem', color: 'var(--text-muted)' }}>Use a strong, unique password of at least 8 characters.</p>
                            </div>
                        </div>
                        <div style={{ height: 1, background: 'rgba(0,0,0,0.06)', margin: '24px 0' }} />

                        {pwSuccess && (
                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: '12px', padding: '13px 16px', marginBottom: '20px', color: 'var(--success)', fontWeight: 600, fontSize: '0.9rem' }}>
                                <CheckCircle2 size={18} /> Password updated successfully!
                            </div>
                        )}

                        <form onSubmit={handlePasswordUpdate} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                            {pwInput('Current Password', currentPassword, setCurrentPassword, showCurrent, () => setShowCurrent(p => !p), 'current-password')}
                            {pwInput('New Password', newPassword, setNewPassword, showNew, () => setShowNew(p => !p), 'new-password')}
                            {pwInput('Confirm New Password', confirmPassword, setConfirmPassword, showConfirm, () => setShowConfirm(p => !p), 'new-password')}

                            {newPassword.length > 0 && (
                                <div>
                                    <div style={{ display: 'flex', gap: '4px', marginBottom: '6px' }}>
                                        {[1, 2, 3, 4].map(i => {
                                            const str = Math.min(4, Math.floor(newPassword.length / 3));
                                            const colors = ['#ef4444', '#f97316', '#eab308', 'var(--success)'];
                                            return <div key={i} style={{ flex: 1, height: 4, borderRadius: 4, background: i <= str ? colors[str - 1] : '#e5e7eb', transition: 'background 0.3s' }} />;
                                        })}
                                    </div>
                                    <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                                        {newPassword.length < 4 ? 'Too weak' : newPassword.length < 7 ? 'Fair' : newPassword.length < 10 ? 'Good' : 'Strong'}
                                    </span>
                                </div>
                            )}
                            <Button type="submit" fullWidth size="lg" isLoading={pwLoading} style={{ marginTop: '4px' }}>
                                Update Password
                            </Button>
                        </form>
                    </div>
                </div>
            )}

            {/* â”€â”€ SETTINGS TAB â”€â”€ */}
            {activeTab === 'settings' && (
                <div className="tab-panel" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', alignItems: 'start' }}>
                    {/* Notifications */}
                    <div className="pcard" style={{ padding: '32px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
                            <div style={{ width: 42, height: 42, background: 'var(--accent-soft)', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--primary)' }}>
                                <Bell size={20} />
                            </div>
                            <div>
                                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-dark)' }}>Notifications</h3>
                                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Choose when you'll be notified.</p>
                            </div>
                        </div>
                        {([
                            ['Order Updates', 'Status changes and confirmations', notifOrders, setNotifOrders],
                            ['New Messages', 'Chat and support messages', notifMessages, setNotifMessages],
                            ['Marketplace', 'New products matching your interests', notifMarket, setNotifMarket],
                            ['Newsletter', 'Tips, guides and market news', notifNewsletter, setNotifNewsletter],
                        ] as [string, string, boolean, React.Dispatch<React.SetStateAction<boolean>>][]).map(([label, desc, on, setOn]) => (
                            <div key={label} className="srow">
                                <div>
                                    <div style={{ fontWeight: 600, color: 'var(--text-dark)', fontSize: '0.9rem' }}>{label}</div>
                                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '2px' }}>{desc}</div>
                                </div>
                                <Toggle on={on} setOn={setOn} />
                            </div>
                        ))}
                    </div>

                    {/* Danger Zone */}
                    <div className="pcard" style={{ padding: '32px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
                            <div style={{ width: 42, height: 42, background: 'rgba(239,68,68,0.08)', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--error)' }}>
                                <AlertCircle size={20} />
                            </div>
                            <div>
                                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-dark)' }}>Danger Zone</h3>
                                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Irreversible account actions.</p>
                            </div>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px', background: 'rgba(239,68,68,0.04)', borderRadius: '12px', border: '1px solid rgba(239,68,68,0.12)', gap: '16px' }}>
                            <div>
                                <div style={{ fontWeight: 600, color: 'var(--text-dark)', fontSize: '0.9rem' }}>Delete Account</div>
                                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '2px' }}>Permanently remove your account and all data.</div>
                            </div>
                            <button
                                style={{ padding: '8px 16px', borderRadius: '10px', border: '1.5px solid var(--error)', background: 'transparent', color: 'var(--error)', fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer', whiteSpace: 'nowrap', transition: 'all 0.2s', flexShrink: 0 }}
                                onMouseEnter={e => { const b = e.target as HTMLButtonElement; b.style.background = 'var(--error)'; b.style.color = 'white'; }}
                                onMouseLeave={e => { const b = e.target as HTMLButtonElement; b.style.background = 'transparent'; b.style.color = 'var(--error)'; }}>
                                Delete Account
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
