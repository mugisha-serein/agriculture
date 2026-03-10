import React, { useState, useEffect } from 'react';
import { api } from '../../api/client';
import { useAuthStore } from '../../store/authStore';
import { Button, Badge } from '../../components/ui';
import { CreditCard, Calendar, ArrowRight, Receipt, ShieldCheck } from 'lucide-react';

interface Payment {
    id: number;
    payment_reference: string;
    amount: string;
    currency: string;
    status: string;
    initiated_at: string;
    buyer_first_name?: string;
    buyer_last_name?: string;
    buyer_email?: string;
    order_number: string;
}

export const TransactionsPage: React.FC = () => {
    const [payments, setPayments] = useState<Payment[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const { user } = useAuthStore();

    useEffect(() => {
        fetchTransactions();
    }, []);

    const fetchTransactions = async () => {
        setIsLoading(true);
        try {
            const response = await api.get('/payments/list/');
            setPayments(response.data.results || response.data || []);
        } catch (err) {
            console.error('Failed to fetch transactions', err);
        } finally {
            setIsLoading(false);
        }
    };

    const getStatusBadge = (status: string) => {
        const variants: Record<string, any> = {
            'initiated': { variant: 'neutral', label: 'Initiated' },
            'escrow_held': { variant: 'warning', label: 'Escrow Held' },
            'released': { variant: 'success', label: 'Released' },
            'refunded': { variant: 'error', label: 'Refunded' },
            'failed': { variant: 'error', label: 'Failed' },
        };
        const config = variants[status] || { variant: 'neutral', label: status };
        return <Badge variant={config.variant}>{config.label}</Badge>;
    };

    return (
        <div className="container">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '48px' }}>
                <div>
                    <h1 style={{ fontSize: '2.5rem', marginBottom: '12px' }}>Financial Transactions</h1>
                    <p style={{ color: 'var(--text-muted)' }}>Secure payment history and escrow ledger.</p>
                </div>
                <div style={{ padding: '8px 16px', background: 'var(--accent-soft)', borderRadius: 'var(--radius-full)', color: 'var(--primary)', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <ShieldCheck size={20} /> Escrow Protected
                </div>
            </div>

            <div className="glass" style={{ padding: '0', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                    <thead style={{ background: 'rgba(0,0,0,0.02)', borderBottom: '1px solid #f0f0f0' }}>
                        <tr>
                            <th style={{ padding: '20px 24px', fontWeight: 600 }}>Reference</th>
                            <th style={{ padding: '20px 24px', fontWeight: 600 }}>Date</th>
                            <th style={{ padding: '20px 24px', fontWeight: 600 }}>Order</th>
                            <th style={{ padding: '20px 24px', fontWeight: 600 }}>{user?.role === 'seller' ? 'Buyer' : 'Type'}</th>
                            <th style={{ padding: '20px 24px', fontWeight: 600, textAlign: 'right' }}>Amount</th>
                            <th style={{ padding: '20px 24px', fontWeight: 600 }}>Status</th>
                            <th style={{ padding: '20px 24px', fontWeight: 600, textAlign: 'right' }}>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {isLoading ? (
                            Array.from({ length: 5 }).map((_, i) => (
                                <tr key={i} style={{ borderBottom: '1px solid #f0f0f0' }}>
                                    <td colSpan={7} style={{ padding: '24px' }}>
                                        <div style={{ height: '20px', background: 'rgba(0,0,0,0.05)', borderRadius: '4px', animation: 'pulse 2s infinite' }} />
                                    </td>
                                </tr>
                            ))
                        ) : payments.length > 0 ? (
                            payments.map((payment) => (
                                <tr key={payment.id} style={{ borderBottom: '1px solid #f0f0f0', transition: 'background 0.2s hover' }}>
                                    <td style={{ padding: '20px 24px' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                            <div style={{ width: '32px', height: '32px', background: 'var(--primary-soft)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--primary)' }}>
                                                <Receipt size={16} />
                                            </div>
                                            <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>{payment.payment_reference}</span>
                                        </div>
                                    </td>
                                    <td style={{ padding: '20px 24px', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                            <Calendar size={14} />
                                            {new Date(payment.initiated_at).toLocaleDateString()}
                                        </div>
                                    </td>
                                    <td style={{ padding: '20px 24px' }}>
                                        <span style={{ fontSize: '0.875rem', fontWeight: 600 }}>#{payment.order_number || 'N/A'}</span>
                                    </td>
                                    <td style={{ padding: '20px 24px', fontSize: '0.875rem' }}>
                                        {user?.role === 'seller' ? (
                                            <div style={{ display: 'flex', flexDirection: 'column' }}>
                                                <span style={{ fontWeight: 600 }}>{payment.buyer_first_name} {payment.buyer_last_name}</span>
                                                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{payment.buyer_email}</span>
                                            </div>
                                        ) : (
                                            <span style={{ color: 'var(--primary)', fontWeight: 600 }}>Purchase</span>
                                        )}
                                    </td>
                                    <td style={{ padding: '20px 24px', textAlign: 'right', fontWeight: 800 }}>
                                        {payment.currency} {payment.amount}
                                    </td>
                                    <td style={{ padding: '20px 24px' }}>
                                        {getStatusBadge(payment.status)}
                                    </td>
                                    <td style={{ padding: '20px 24px', textAlign: 'right' }}>
                                        <Button variant="ghost" size="sm" style={{ color: 'var(--text-muted)' }}>
                                            Details <ArrowRight size={14} style={{ marginLeft: '4px' }} />
                                        </Button>
                                    </td>
                                </tr>
                            ))
                        ) : (
                            <tr>
                                <td colSpan={7} style={{ padding: '100px 24px', textAlign: 'center' }}>
                                    <CreditCard size={48} style={{ margin: '0 auto 16px', color: 'rgba(0,0,0,0.1)' }} />
                                    <p style={{ color: 'var(--text-muted)' }}>No transactions found yet.</p>
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            <style>{`
                @keyframes pulse {
                    0% { opacity: 0.6; }
                    50% { opacity: 0.3; }
                    100% { opacity: 0.6; }
                }
                tr:hover {
                    background: rgba(var(--primary-rgb), 0.01);
                }
            `}</style>
        </div>
    );
};
