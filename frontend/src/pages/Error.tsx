import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { AlertTriangle, Home, RefreshCcw, X } from 'lucide-react';

import { clearSystemError, readSystemError, SYSTEM_ERROR_EVENT } from '../lib/systemError';
import type { SystemErrorPayload } from '../lib/systemError';

interface ErrorPageProps {
    boundaryFallback?: boolean;
}

interface ErrorLocationState {
    error?: SystemErrorPayload;
}

interface SystemInlineErrorProps {
    marginBottom?: string;
}

export const SystemInlineError: React.FC<SystemInlineErrorProps> = ({ marginBottom = '10px' }) => {
    const [errorPayload, setErrorPayload] = React.useState<SystemErrorPayload | null>(() => readSystemError());

    React.useEffect(() => {
        const handleSystemError = (event: Event) => {
            const customEvent = event as CustomEvent<SystemErrorPayload>;
            setErrorPayload(customEvent.detail || readSystemError());
        };

        window.addEventListener(SYSTEM_ERROR_EVENT, handleSystemError as EventListener);
        return () => window.removeEventListener(SYSTEM_ERROR_EVENT, handleSystemError as EventListener);
    }, []);

    if (!errorPayload) {
        return null;
    }

    return (
        <div style={{ marginBottom }}>
            <div className="system-inline-error">
                <div className="system-inline-error-main">
                    <div className="system-inline-error-icon">
                        <AlertTriangle size={15} />
                    </div>
                    <div className="system-inline-error-content">
                        <p>
                            {errorPayload.title ? `${errorPayload.title}: ` : ''}
                            {errorPayload.message}
                        </p>
                    </div>
                </div>
                <button
                    type="button"
                    aria-label="Dismiss error"
                    className="system-inline-error-dismiss"
                    onClick={() => {
                        clearSystemError();
                        setErrorPayload(null);
                    }}
                >
                    <X size={14} />
                </button>
            </div>

            <style>{`
                .system-inline-error {
                    background: linear-gradient(135deg, rgba(255, 255, 255, 0.42), rgba(255, 205, 205, 0.36));
                    border: 1px solid rgba(239, 68, 68, 0.45);
                    backdrop-filter: blur(14px) saturate(145%);
                    -webkit-backdrop-filter: blur(14px) saturate(145%);
                    border-radius: 12px;
                    padding: 10px 12px;
                    display: flex;
                    align-items: flex-start;
                    justify-content: space-between;
                    gap: 12px;
                    animation: inlineErrorFadeIn 0.25s ease-out forwards;
                }

                .system-inline-error-main {
                    display: flex;
                    align-items: flex-start;
                    gap: 10px;
                    min-width: 0;
                }

                .system-inline-error-icon {
                    width: 26px;
                    height: 26px;
                    border-radius: 8px;
                    background: rgba(239, 68, 68, 0.14);
                    border: 1px solid rgba(239, 68, 68, 0.28);
                    color: #b91c1c;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    flex-shrink: 0;
                }

                .system-inline-error-content p {
                    margin: 0;
                    color: #7f1d1d;
                    font-size: 0.96rem;
                    line-height: 1.45;
                    font-weight: 700;
                }

                .system-inline-error-dismiss {
                    border: none;
                    background: rgba(255, 255, 255, 0.22);
                    color: #b91c1c;
                    cursor: pointer;
                    padding: 4px;
                    border-radius: 6px;
                    flex-shrink: 0;
                    transition: transform 0.2s ease, background 0.2s ease;
                }

                .system-inline-error-dismiss:hover {
                    background: rgba(239, 68, 68, 0.18);
                    transform: translateY(-1px);
                }

                @keyframes inlineErrorFadeIn {
                    from {
                        opacity: 0;
                        transform: translateY(-8px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }
            `}</style>
        </div>
    );
};

export const ErrorPage: React.FC<ErrorPageProps> = ({ boundaryFallback = false }) => {
    const navigate = useNavigate();
    const location = useLocation();
    const locationState = location.state as ErrorLocationState | null;

    const [errorPayload] = React.useState<SystemErrorPayload | null>(() => {
        if (locationState?.error) {
            return locationState.error;
        }
        return readSystemError();
    });

    const errorTitle = errorPayload?.title || 'System Error';
    const errorMessage = errorPayload?.message || 'Something went wrong in the application.';
    const errorMeta = [
        errorPayload?.status ? `Status ${errorPayload.status}` : null,
        errorPayload?.code ? `Code ${errorPayload.code}` : null
    ].filter(Boolean).join(' | ');

    const handleGoHome = () => {
        clearSystemError();
        navigate('/');
    };

    const handleRetry = () => {
        clearSystemError();
        window.location.reload();
    };

    return (
        <div className="error-page-shell">
            <div className="error-card">
                <div className="error-badge">
                    <AlertTriangle size={20} />
                    <span>Global Error Handler</span>
                </div>

                <h1>{errorTitle}</h1>
                <p>{errorMessage}</p>

                {errorMeta && (
                    <div className="error-meta">{errorMeta}</div>
                )}

                {errorPayload?.timestamp && (
                    <div className="error-meta">{new Date(errorPayload.timestamp).toLocaleString()}</div>
                )}

                <div className="error-actions">
                    <button onClick={handleRetry} className="error-btn error-btn-primary">
                        <RefreshCcw size={16} />
                        Retry
                    </button>
                    {boundaryFallback ? (
                        <button onClick={handleGoHome} className="error-btn error-btn-secondary">
                            <Home size={16} />
                            Back to Home
                        </button>
                    ) : (
                        <Link to="/" onClick={clearSystemError} className="error-btn error-btn-secondary">
                            <Home size={16} />
                            Back to Home
                        </Link>
                    )}
                </div>
            </div>

            <style>{`
                .error-page-shell {
                    min-height: calc(100vh - 200px);
                    display: grid;
                    place-items: center;
                    padding: 20px;
                    background:
                        radial-gradient(circle at 20% 15%, rgba(248, 113, 113, 0.12), transparent 45%),
                        radial-gradient(circle at 85% 85%, rgba(239, 68, 68, 0.08), transparent 50%);
                }

                .error-card {
                    width: min(560px, 100%);
                    border-radius: 20px;
                    border: 1px solid rgba(248, 113, 113, 0.35);
                    background: linear-gradient(145deg, rgba(255, 255, 255, 0.64), rgba(255, 239, 239, 0.46));
                    box-shadow: 0 18px 36px rgba(15, 23, 42, 0.12);
                    backdrop-filter: blur(18px) saturate(140%);
                    -webkit-backdrop-filter: blur(18px) saturate(140%);
                    padding: 30px;
                    display: flex;
                    flex-direction: column;
                    gap: 14px;
                    animation: errorSlideIn 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
                    opacity: 0;
                }

                .error-badge {
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    padding: 6px 10px;
                    border-radius: 999px;
                    width: fit-content;
                    background: rgba(254, 226, 226, 0.74);
                    color: #991b1b;
                    border: 1px solid rgba(248, 113, 113, 0.45);
                    font-size: 0.82rem;
                    font-weight: 700;
                }

                .error-card h1 {
                    color: #991b1b;
                    margin: 0;
                    font-size: 1.65rem;
                }

                .error-card p {
                    color: #3f3f46;
                    margin: 0;
                    line-height: 1.55;
                }

                .error-meta {
                    color: #71717a;
                    font-size: 0.86rem;
                }

                .error-actions {
                    margin-top: 10px;
                    display: flex;
                    gap: 10px;
                    flex-wrap: wrap;
                }

                .error-btn {
                    border-radius: 10px;
                    padding: 10px 14px;
                    font-size: 0.9rem;
                    font-weight: 700;
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    text-decoration: none;
                    border: 1px solid transparent;
                    cursor: pointer;
                    transition: transform 0.14s ease, box-shadow 0.14s ease;
                }

                .error-btn:hover {
                    transform: translateY(-1px);
                }

                .error-btn-primary {
                    background: linear-gradient(135deg, #c2410c, #b91c1c);
                    color: #fff;
                    box-shadow: 0 8px 16px rgba(185, 28, 28, 0.24);
                }

                .error-btn-secondary {
                    background: rgba(255, 255, 255, 0.62);
                    color: #111827;
                    border-color: rgba(209, 213, 219, 0.8);
                }

                @keyframes errorSlideIn {
                    from { transform: translateY(24px); opacity: 0; }
                    to { transform: translateY(0); opacity: 1; }
                }
            `}</style>
        </div>
    );
};
