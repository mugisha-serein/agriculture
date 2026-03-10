import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
    size?: 'sm' | 'md' | 'lg';
    fullWidth?: boolean;
    isLoading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
    variant = 'primary',
    size = 'md',
    fullWidth = false,
    isLoading = false,
    children,
    style,
    disabled,
    ...props
}) => {
    const getStyles = () => {
        let baseStyle: React.CSSProperties = {
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: 'var(--radius-md)',
            fontWeight: '600',
            transition: 'var(--transition-fast)',
            gap: '8px',
            width: fullWidth ? '100%' : 'auto',
            opacity: (disabled || isLoading) ? 0.6 : 1,
            pointerEvents: (disabled || isLoading) ? 'none' : 'auto',
        };

        const sizeStyles = {
            sm: { padding: '6px 16px', fontSize: '0.875rem' },
            md: { padding: '10px 24px', fontSize: '1rem' },
            lg: { padding: '14px 32px', fontSize: '1.125rem' },
        };

        const variantStyles = {
            primary: { background: 'var(--primary)', color: 'white' },
            secondary: { background: 'var(--secondary)', color: 'white' },
            outline: { background: 'transparent', border: '2px solid var(--primary)', color: 'var(--primary)' },
            ghost: { background: 'transparent', color: 'var(--primary)' },
            danger: { background: 'var(--error)', color: 'white' },
        };

        return { ...baseStyle, ...sizeStyles[size], ...variantStyles[variant], ...style };
    };

    return (
        <button style={getStyles()} disabled={disabled || isLoading} {...props}>
            {isLoading ? 'Loading...' : children}
        </button>
    );
};

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
    label?: string;
    error?: string;
}

export const Input: React.FC<InputProps> = ({ label, error, style, ...props }) => {
    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', width: '100%' }}>
            {label && <label style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-muted)' }}>{label}</label>}
            <input
                style={{
                    padding: '12px 16px',
                    borderRadius: 'var(--radius-md)',
                    border: `1px solid ${error ? 'var(--error)' : '#e5e7eb'}`,
                    background: 'white',
                    fontSize: '1rem',
                    outline: 'none',
                    transition: 'var(--transition-fast)',
                    width: '100%',
                    ...style,
                }}
                {...props}
            />
            {error && <span style={{ fontSize: '0.75rem', color: 'var(--error)' }}>{error}</span>}
        </div>
    );
};

interface BadgeProps {
    variant?: 'primary' | 'success' | 'warning' | 'error' | 'neutral';
    children: React.ReactNode;
}

export const Badge: React.FC<BadgeProps> = ({ variant = 'neutral', children }) => {
    const variants = {
        primary: { background: 'var(--accent-soft)', color: 'var(--primary)' },
        success: { background: '#ecfdf5', color: '#059669' },
        warning: { background: '#fffbeb', color: '#d97706' },
        error: { background: '#fef2f2', color: '#dc2626' },
        neutral: { background: '#f3f4f6', color: '#4b5563' },
    };

    return (
        <span style={{
            display: 'inline-flex',
            alignItems: 'center',
            padding: '2px 10px',
            borderRadius: 'var(--radius-full)',
            fontSize: '0.75rem',
            fontWeight: 700,
            textTransform: 'uppercase',
            ...variants[variant]
        }}>
            {children}
        </span>
    );
};
