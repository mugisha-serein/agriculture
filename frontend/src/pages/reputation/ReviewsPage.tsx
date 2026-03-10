import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../../api/client';
// import { Button, Input } from '../../components/ui';
import { Star, MessageSquare, User, Quote } from 'lucide-react';

interface Review {
    id: string;
    reviewer_name: string;
    rating: number;
    comment: string;
    created_at: string;
}

interface ReputationSummary {
    average_rating: number;
    total_reviews: number;
}

export const ReviewsPage: React.FC = () => {
    const { userId } = useParams();
    const [reviews, setReviews] = useState<Review[]>([]);
    const [summary, setSummary] = useState<ReputationSummary | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        fetchReputation();
    }, [userId]);

    const fetchReputation = async () => {
        setIsLoading(true);
        try {
            const [reviewsRes, summaryRes] = await Promise.all([
                api.get(`/reputation/users/${userId}/reviews/`),
                api.get(`/reputation/users/${userId}/summary/`)
            ]);
            setReviews(reviewsRes.data.results || reviewsRes.data || []);
            setSummary(summaryRes.data);
        } catch (err) {
            console.error('Failed to fetch reputation data', err);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="container" style={{ maxWidth: '800px' }}>
            <div style={{ marginBottom: '48px', textAlign: 'center' }}>
                <h1 style={{ fontSize: '2.5rem', marginBottom: '16px' }}>Participant Reputation</h1>
                <p style={{ color: 'var(--text-muted)' }}>Transparent reviews from the agriculture community.</p>
            </div>

            {summary && (
                <div className="glass" style={{ padding: '40px', borderRadius: 'var(--radius-lg)', textAlign: 'center', marginBottom: '40px', background: 'var(--primary-dark)', color: 'white' }}>
                    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '16px', marginBottom: '16px' }}>
                        <div style={{ fontSize: '4rem', fontWeight: 800 }}>{summary.average_rating.toFixed(1)}</div>
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
                            <div style={{ display: 'flex', color: 'var(--accent)' }}>
                                {Array.from({ length: 5 }).map((_, i) => (
                                    <Star key={i} size={24} fill={i < Math.round(summary.average_rating) ? 'var(--accent)' : 'transparent'} />
                                ))}
                            </div>
                            <div style={{ opacity: 0.7, fontWeight: 600 }}>Based on {summary.total_reviews} reviews</div>
                        </div>
                    </div>
                    <p style={{ maxWidth: '500px', margin: '0 auto', opacity: 0.8, fontSize: '0.9rem' }}>
                        Reputation is calculated using a Bayesian average to ensure fairness and reliability for all participants.
                    </p>
                </div>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                {isLoading ? (
                    Array.from({ length: 3 }).map((_, i) => (
                        <div key={i} className="glass" style={{ height: '150px', borderRadius: 'var(--radius-md)', animation: 'pulse 2s infinite' }} />
                    ))
                ) : reviews.length > 0 ? (
                    reviews.map((review) => (
                        <div key={review.id} className="glass" style={{ padding: '32px', borderRadius: 'var(--radius-lg)', position: 'relative' }}>
                            <Quote size={40} style={{ position: 'absolute', right: '32px', top: '32px', opacity: 0.05, color: 'var(--primary)' }} />
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                    <div style={{ width: '40px', height: '40px', background: 'var(--accent-soft)', color: 'var(--primary)', borderRadius: 'var(--radius-full)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                        <User size={20} />
                                    </div>
                                    <div>
                                        <div style={{ fontWeight: 700 }}>{review.reviewer_name}</div>
                                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{new Date(review.created_at).toLocaleDateString()}</div>
                                    </div>
                                </div>
                                <div style={{ display: 'flex', gap: '2px', color: 'var(--accent)' }}>
                                    {Array.from({ length: 5 }).map((_, i) => (
                                        <Star key={i} size={16} fill={i < review.rating ? 'var(--accent)' : 'transparent'} />
                                    ))}
                                </div>
                            </div>
                            <p style={{ color: 'var(--text)', lineHeight: '1.6', fontSize: '1.05rem', fontStyle: 'italic' }}>
                                "{review.comment}"
                            </p>
                        </div>
                    ))
                ) : (
                    <div style={{ textAlign: 'center', padding: '60px 0' }}>
                        <MessageSquare size={48} style={{ margin: '0 auto 16px', opacity: 0.2 }} />
                        <p style={{ color: 'var(--text-muted)' }}>No reviews yet for this participant.</p>
                    </div>
                )}
            </div>

            <style>{`
        @keyframes pulse {
          0% { opacity: 0.6; }
          50% { opacity: 0.3; }
          100% { opacity: 0.6; }
        }
      `}</style>
        </div>
    );
};
