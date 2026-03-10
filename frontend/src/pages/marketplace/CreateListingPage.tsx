import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../api/client';
import { Button, Input } from '../../components/ui';
import { ArrowRight, X, Leaf, Calendar, Package, Tag } from 'lucide-react';
import { reportApiError, reportRuntimeError } from '../../lib/identityError';
import { SystemInlineError } from '../Error';

interface Crop {
    id: string;
    name: string;
}

export const CreateListingPage: React.FC = () => {
    const [crops, setCrops] = useState<Crop[]>([]);
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        crop_id: '',
        price_per_unit: '',
        unit: 'kg',
        quantity_available: '',
        minimum_order_quantity: '1',
        location_name: '',
        expires_at: '',
    });
    const [isLoading, setIsLoading] = useState(false);

    const navigate = useNavigate();

    useEffect(() => {
        fetchCrops();

        const date = new Date();
        date.setDate(date.getDate() + 30);
        setFormData(prev => ({ ...prev, expires_at: date.toISOString().split('T')[0] }));
    }, []);

    const fetchCrops = async () => {
        try {
            const response = await api.get('/marketplace/crops/');
            setCrops(response.data.results || response.data || []);
        } catch (err: unknown) {
            reportApiError('Crop Categories Load Failed', err);
        }
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleClose = () => {
        navigate('/products/me');
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);

        try {
            if (!formData.crop_id) {
                reportRuntimeError('Validation Error', 'Crop category is required.');
                return;
            }

            const submissionData = {
                ...formData,
                crop_id: parseInt(formData.crop_id),
                price_per_unit: parseFloat(formData.price_per_unit),
                quantity_available: parseFloat(formData.quantity_available),
                minimum_order_quantity: parseFloat(formData.minimum_order_quantity),
                expires_at: new Date(formData.expires_at).toISOString(),
            };

            await api.post('/marketplace/products/', submissionData);
            navigate('/products/me');
        } catch (err: unknown) {
            reportApiError('Listing Create Failed', err);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="listing-modal-shell">
            <div className="listing-modal-backdrop" onClick={handleClose} />
            <div className="listing-modal" role="dialog" aria-modal="true">
                <header className="listing-modal-header">
                    <div>
                        <div className="listing-kicker">
                            <Leaf size={14} /> New Listing
                        </div>
                        <h1>Create New Listing</h1>
                        <p>Share your high-quality produce with verified buyers.</p>
                    </div>
                    <button className="listing-close" type="button" onClick={handleClose} aria-label="Close">
                        <X size={18} />
                    </button>
                </header>

                <SystemInlineError marginBottom="16px" />

                <form onSubmit={handleSubmit} className="listing-form">
                    <section className="listing-section">
                        <div className="listing-section-title">
                            <Tag size={16} />
                            Product Details
                        </div>
                        <div className="listing-grid">
                            <Input
                                label="Listing Title"
                                name="title"
                                placeholder="e.g. Premium Organic Wheat"
                                value={formData.title}
                                onChange={handleChange}
                                required
                            />
                            <div className="listing-field">
                                <label>Crop Category</label>
                                <select
                                    name="crop_id"
                                    value={formData.crop_id}
                                    onChange={handleChange}
                                    required
                                >
                                    <option value="">Select a crop...</option>
                                    {crops.map((crop) => (
                                        <option key={crop.id} value={crop.id}>{crop.name}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                        <div className="listing-field">
                            <label>Detailed Description</label>
                            <textarea
                                name="description"
                                placeholder="Tell buyers about your produce, quality standards, and harvest date..."
                                value={formData.description}
                                onChange={handleChange}
                                required
                                rows={3}
                            />
                        </div>
                    </section>

                    <section className="listing-section">
                        <div className="listing-section-title">
                            <Package size={16} />
                            Pricing & Inventory
                        </div>
                        <div className="listing-grid three">
                            <Input
                                label="Price per Unit ($)"
                                type="number"
                                name="price_per_unit"
                                placeholder="0.00"
                                step="0.01"
                                value={formData.price_per_unit}
                                onChange={handleChange}
                                required
                            />
                            <div className="listing-field">
                                <label>Unit</label>
                                <select
                                    name="unit"
                                    value={formData.unit}
                                    onChange={handleChange}
                                    required
                                >
                                    <option value="kg">Kilogram (kg)</option>
                                    <option value="ton">Ton</option>
                                    <option value="bag">Bag</option>
                                    <option value="crate">Crate</option>
                                </select>
                            </div>
                            <Input
                                label="Total Quantity"
                                type="number"
                                name="quantity_available"
                                placeholder="1000"
                                value={formData.quantity_available}
                                onChange={handleChange}
                                required
                            />
                        </div>
                        <div className="listing-grid three">
                            <Input
                                label="Min. Order Qty"
                                type="number"
                                name="minimum_order_quantity"
                                value={formData.minimum_order_quantity}
                                onChange={handleChange}
                                required
                            />
                            <Input
                                label="Location"
                                name="location_name"
                                placeholder="City, Region"
                                value={formData.location_name}
                                onChange={handleChange}
                                required
                            />
                            <div className="listing-field">
                                <label>Expires On</label>
                                <div className="listing-date">
                                    <Calendar size={16} />
                                    <input
                                        type="date"
                                        name="expires_at"
                                        value={formData.expires_at}
                                        onChange={handleChange}
                                        required
                                    />
                                </div>
                            </div>
                        </div>
                    </section>

                    <div className="listing-actions">
                        <Button type="submit" size="lg" isLoading={isLoading} fullWidth>
                            Publish Listing <ArrowRight size={20} />
                        </Button>
                        <Button type="button" variant="outline" onClick={handleClose} fullWidth>
                            Cancel
                        </Button>
                    </div>
                </form>
            </div>

            <style>{`
                .listing-modal-shell {
                    position: relative;
                    min-height: calc(100vh - 140px);
                    display: grid;
                    place-items: center;
                    padding: 28px 20px 32px;
                }

                .listing-modal-backdrop {
                    position: fixed;
                    inset: 0;
                    background: rgba(10, 16, 20, 0.55);
                    backdrop-filter: blur(6px);
                    z-index: 1;
                }

                .listing-modal {
                    position: relative;
                    z-index: 2;
                    width: min(820px, 100%);
                    background: #fff;
                    border-radius: 22px;
                    border: 1px solid rgba(0,0,0,0.08);
                    box-shadow: 0 28px 60px rgba(15,23,42,0.25);
                    padding: 28px;
                    max-height: 82vh;
                    overflow: hidden;
                    animation: listingModalIn 0.35s cubic-bezier(0.16, 1, 0.3, 1) both;
                }

                .listing-modal-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                    gap: 16px;
                    margin-bottom: 18px;
                }

                .listing-modal-header h1 {
                    margin: 8px 0 6px;
                    font-size: 1.7rem;
                    color: var(--text-dark);
                }

                .listing-modal-header p {
                    margin: 0;
                    color: var(--text-muted);
                }

                .listing-kicker {
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

                .listing-close {
                    border: none;
                    background: rgba(15,23,42,0.08);
                    color: var(--text-dark);
                    width: 36px;
                    height: 36px;
                    border-radius: 12px;
                    display: grid;
                    place-items: center;
                    cursor: pointer;
                    transition: transform 0.2s ease, background 0.2s ease;
                }

                .listing-close:hover {
                    background: rgba(15,23,42,0.15);
                    transform: translateY(-1px);
                }

                .listing-form {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 18px;
                }

                .listing-section {
                    background: rgba(15,23,42,0.02);
                    border: 1px solid rgba(15,23,42,0.06);
                    border-radius: 18px;
                    padding: 18px;
                    display: flex;
                    flex-direction: column;
                    gap: 16px;
                }

                .listing-section-title {
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    font-weight: 700;
                    color: var(--text-dark);
                }

                .listing-grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 16px;
                }

                .listing-grid.three {
                    grid-template-columns: repeat(3, minmax(0, 1fr));
                }

                .listing-field {
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                }

                .listing-field label {
                    font-size: 0.85rem;
                    font-weight: 600;
                    color: var(--text-muted);
                }

                .listing-field select,
                .listing-field textarea,
                .listing-date input {
                    padding: 12px 14px;
                    border-radius: 12px;
                    border: 1px solid #e5e7eb;
                    background: #fff;
                    font-size: 0.95rem;
                    outline: none;
                    font-family: inherit;
                }

                .listing-field textarea {
                    min-height: 90px;
                    resize: vertical;
                }

                .listing-date {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    border: 1px solid #e5e7eb;
                    border-radius: 12px;
                    padding: 8px 12px;
                    background: #fff;
                }

                .listing-date input {
                    border: none;
                    padding: 0;
                    width: 100%;
                    background: transparent;
                }

                .listing-actions {
                    grid-column: 1 / -1;
                    display: flex;
                    flex-direction: column;
                    gap: 10px;
                    padding-top: 4px;
                }

                @keyframes listingModalIn {
                    from { opacity: 0; transform: translateY(18px) scale(0.98); }
                    to { opacity: 1; transform: translateY(0) scale(1); }
                }

                @media (max-width: 960px) {
                    .listing-modal {
                        max-height: 90vh;
                    }

                    .listing-grid.three {
                        grid-template-columns: 1fr;
                    }
                }

                @media (max-width: 720px) {
                    .listing-modal {
                        border-radius: 16px;
                        padding: 20px;
                        max-height: none;
                        height: 100vh;
                    }

                    .listing-modal-shell {
                        padding: 0;
                    }

                    .listing-form {
                        grid-template-columns: 1fr;
                    }

                    .listing-actions {
                        flex-direction: column-reverse;
                        align-items: stretch;
                    }
                }

                @media (prefers-reduced-motion: reduce) {
                    .listing-modal {
                        animation: none !important;
                    }
                }
            `}</style>
        </div>
    );
};
