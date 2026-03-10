import React, { useEffect, useMemo, useState } from 'react';
import { api } from '../../api/client';
import { Button, Input, Badge } from '../../components/ui';
import { useAuthStore } from '../../store/authStore';
import { Plus, Edit2, Trash2, X, Check, Lock, Sparkles } from 'lucide-react';
import { reportApiError, reportRuntimeError } from '../../lib/identityError';

interface Crop {
    id: number;
    name: string;
    slug: string;
    description: string;
}

interface RoleContent {
    title: string;
    subtitle: string;
    panelTitle: string;
    panelDescription: string;
    emptyTitle: string;
    emptyDescription: string;
}

const getRoleContent = (role?: string): RoleContent => {
    if (role === 'seller') {
        return {
            title: 'Manage Crop Categories',
            subtitle: 'Add and organize categories used for marketplace listings.',
            panelTitle: 'Add / Edit Category',
            panelDescription: 'Create a new category or update an existing one.',
            emptyTitle: 'No crop categories yet',
            emptyDescription: 'Create your first category to organize marketplace products.'
        };
    }

    if (role === 'transporter') {
        return {
            title: 'Crop Categories',
            subtitle: 'Reference crop categories for shipment and routing context.',
            panelTitle: 'Read-Only Access',
            panelDescription: 'Only seller accounts can create, edit, or deactivate categories.',
            emptyTitle: 'No crop categories available',
            emptyDescription: 'Categories will appear here once sellers publish them.'
        };
    }

    if (role === 'buyer') {
        return {
            title: 'Crop Categories',
            subtitle: 'Browse available crop categories across marketplace listings.',
            panelTitle: 'Read-Only Access',
            panelDescription: 'Only seller accounts can create, edit, or deactivate categories.',
            emptyTitle: 'No crop categories available',
            emptyDescription: 'Categories will appear here once sellers publish them.'
        };
    }

    return {
        title: 'Crop Categories',
        subtitle: 'Review crop categories available in the marketplace.',
        panelTitle: 'Read-Only Access',
        panelDescription: 'Only seller accounts can create, edit, or deactivate categories.',
        emptyTitle: 'No crop categories available',
        emptyDescription: 'Categories will appear here when they are created.'
    };
};

export const ManageCropsPage: React.FC = () => {
    const { user } = useAuthStore();
    const canManage = user?.role === 'seller';
    const roleContent = useMemo(() => getRoleContent(user?.role), [user?.role]);

    const [crops, setCrops] = useState<Crop[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [editingId, setEditingId] = useState<number | null>(null);
    const [formData, setFormData] = useState({ name: '', description: '' });

    useEffect(() => {
        void fetchCrops();
    }, [user?.role]);

    const fetchCrops = async () => {
        setIsLoading(true);
        try {
            const response = await api.get('/marketplace/crops/');
            const data = Array.isArray(response.data) ? response.data : response.data.results || [];
            setCrops(data);
        } catch (err: unknown) {
            reportApiError('Crop Categories Load Failed', err);
        } finally {
            setIsLoading(false);
        }
    };

    const ensureManageAccess = () => {
        if (canManage) return true;
        reportRuntimeError('Access Restricted', 'Only seller accounts can manage crop categories.');
        return false;
    };

    const resetForm = () => {
        setEditingId(null);
        setFormData({ name: '', description: '' });
    };

    const handleFormChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setFormData((prev) => ({ ...prev, [event.target.name]: event.target.value }));
    };

    const handleCreate = async (event: React.FormEvent) => {
        event.preventDefault();
        if (!ensureManageAccess()) return;
        if (!formData.name.trim()) {
            reportRuntimeError('Validation Error', 'Category name is required.');
            return;
        }

        setIsSaving(true);
        try {
            const response = await api.post('/marketplace/crops/', {
                name: formData.name.trim(),
                description: formData.description.trim()
            });
            setCrops((prev) => [...prev, response.data]);
            resetForm();
        } catch (err: unknown) {
            reportApiError('Crop Category Create Failed', err);
        } finally {
            setIsSaving(false);
        }
    };

    const handleUpdate = async (event: React.FormEvent) => {
        event.preventDefault();
        if (!ensureManageAccess() || editingId === null) return;
        if (!formData.name.trim()) {
            reportRuntimeError('Validation Error', 'Category name is required.');
            return;
        }

        setIsSaving(true);
        try {
            const response = await api.patch(`/marketplace/crops/${editingId}/`, {
                name: formData.name.trim(),
                description: formData.description.trim()
            });
            setCrops((prev) => prev.map((crop) => (crop.id === editingId ? response.data : crop)));
            resetForm();
        } catch (err: unknown) {
            reportApiError('Crop Category Update Failed', err);
        } finally {
            setIsSaving(false);
        }
    };

    const handleDelete = async (id: number) => {
        if (!ensureManageAccess()) return;
        if (!window.confirm('Are you sure you want to deactivate this crop category?')) return;

        try {
            await api.delete(`/marketplace/crops/${id}/`);
            setCrops((prev) => prev.filter((crop) => crop.id !== id));
            if (editingId === id) resetForm();
        } catch (err: unknown) {
            reportApiError('Crop Category Deactivate Failed', err);
        }
    };

    const startEditing = (crop: Crop) => {
        if (!ensureManageAccess()) return;
        setEditingId(crop.id);
        setFormData({ name: crop.name, description: crop.description || '' });
    };

    return (
        <div className="container crops-page">
            <header className="crops-hero">
                <div>
                    <h1 className="crops-title">{roleContent.title}</h1>
                    <p className="crops-subtitle">{roleContent.subtitle}</p>
                </div>
            </header>

            <div className="crops-layout">
                <section className="crops-panel crops-editor-panel">
                    <div className="crops-panel-head">
                        <h3>{roleContent.panelTitle}</h3>
                        {canManage && editingId !== null && (
                            <Badge variant="neutral">Editing #{editingId}</Badge>
                        )}
                    </div>
                    <p className="crops-panel-copy">{roleContent.panelDescription}</p>

                    {canManage ? (
                        <form onSubmit={editingId === null ? handleCreate : handleUpdate} className="crops-form">
                            <Input
                                label="Category Name"
                                name="name"
                                value={formData.name}
                                onChange={handleFormChange}
                                placeholder="e.g. Grains"
                                required
                            />
                            <Input
                                label="Description (Optional)"
                                name="description"
                                value={formData.description}
                                onChange={handleFormChange}
                                placeholder="Short description..."
                            />
                            <div className="crops-form-actions">
                                <Button type="submit" isLoading={isSaving} style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                                    {editingId === null ? <Plus size={16} /> : <Check size={16} />}
                                    {editingId === null ? 'Create Category' : 'Save Changes'}
                                </Button>
                                {editingId !== null && (
                                    <Button type="button" variant="outline" onClick={resetForm}>
                                        <X size={16} /> Cancel
                                    </Button>
                                )}
                            </div>
                        </form>
                    ) : (
                        <div className="crops-readonly-box">
                            <Lock size={16} />
                            <span>Read-only mode for your current role.</span>
                        </div>
                    )}
                </section>

                <section className="crops-panel crops-table-panel">
                    <div className="crops-panel-head">
                        <h3>All Categories</h3>
                        <Badge variant="neutral">{crops.length} total</Badge>
                    </div>

                    <div className="crops-table-wrap">
                        <table className="crops-table">
                            <thead>
                                <tr>
                                    <th>Category</th>
                                    <th>Slug</th>
                                    <th>Description</th>
                                    <th>Status</th>
                                    <th style={{ textAlign: 'right' }}>{canManage ? 'Actions' : 'Access'}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {isLoading ? (
                                    Array.from({ length: 6 }).map((_, index) => (
                                        <tr key={index} className="crops-row">
                                            <td colSpan={5}>
                                                <div className="crops-loading-bar" />
                                            </td>
                                        </tr>
                                    ))
                                ) : crops.length > 0 ? (
                                    crops.map((crop) => (
                                        <tr key={crop.id} className="crops-row">
                                            <td style={{ fontWeight: 650 }}>{crop.name}</td>
                                            <td><code>{crop.slug}</code></td>
                                            <td className="crops-description-cell">
                                                {crop.description || <span style={{ opacity: 0.6, fontStyle: 'italic' }}>No description</span>}
                                            </td>
                                            <td>
                                                <Badge variant="success">Active</Badge>
                                            </td>
                                            <td style={{ textAlign: 'right' }}>
                                                {canManage ? (
                                                    <div className="crops-action-row">
                                                        <Button variant="ghost" size="sm" onClick={() => startEditing(crop)} title="Edit category">
                                                            <Edit2 size={16} />
                                                        </Button>
                                                        <Button variant="ghost" size="sm" onClick={() => handleDelete(crop.id)} title="Deactivate category" style={{ color: 'var(--error)' }}>
                                                            <Trash2 size={16} />
                                                        </Button>
                                                    </div>
                                                ) : (
                                                    <Badge variant="neutral">View only</Badge>
                                                )}
                                            </td>
                                        </tr>
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan={5}>
                                            <div className="crops-empty">
                                                <Sparkles size={32} />
                                                <h4>{roleContent.emptyTitle}</h4>
                                                <p>{roleContent.emptyDescription}</p>
                                            </div>
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </section>
            </div>

            <style>{`
                .crops-page {
                    animation: cropsPageIn 0.45s cubic-bezier(0.16, 1, 0.3, 1) both;
                }

                .crops-hero {
                    display: flex;
                    align-items: flex-end;
                    justify-content: space-between;
                    gap: 14px;
                    margin-bottom: 18px;
                    flex-wrap: wrap;
                }

                .crops-title {
                    margin: 0 0 6px;
                    font-size: 2rem;
                    font-weight: 800;
                    color: var(--text-dark);
                    letter-spacing: -0.4px;
                }

                .crops-subtitle {
                    margin: 0;
                    font-size: 0.94rem;
                    color: var(--text-muted);
                }

                .crops-role-pill {
                    background: rgba(45, 90, 39, 0.1);
                    color: var(--primary);
                    border: 1px solid rgba(45, 90, 39, 0.22);
                    border-radius: 999px;
                    padding: 6px 12px;
                    font-size: 0.76rem;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 0.04em;
                }

                .crops-layout {
                    display: grid;
                    grid-template-columns: minmax(280px, 340px) minmax(0, 1fr);
                    gap: 14px;
                    align-items: start;
                }

                .crops-panel {
                    background: #fff;
                    border-radius: 18px;
                    padding: 18px;
                    border: 1px solid rgba(0,0,0,0.05);
                    box-shadow: 0 2px 6px rgba(15,23,42,0.06);
                    transition: transform 0.24s cubic-bezier(0.22,1,0.36,1), 0.24s ease, border-color 0.24s ease;
                }

                .crops-editor-panel {
                    padding: 18px;
                    position: sticky;
                    top: 94px;
                }

                .crops-table-panel {
                    overflow: hidden;
                }

                .crops-panel-head {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    gap: 8px;
                    margin-bottom: 18px;
                }

                .crops-panel-head h3 {
                    margin: 0;
                    font-size: 1.02rem;
                    font-weight: 700;
                    color: var(--text-dark);
                }

                .crops-panel-copy {
                    margin: 0 0 14px;
                    color: var(--text-muted);
                    font-size: 0.84rem;
                    line-height: 1.45;
                }

                .crops-form {
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                }

                .crops-form-actions {
                    display: flex;
                    gap: 8px;
                    flex-wrap: wrap;
                }

                .crops-readonly-box {
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    background: rgba(15,23,42,0.05);
                    color: var(--text-muted);
                    border: 1px solid rgba(15,23,42,0.1);
                    border-radius: 999px;
                    padding: 8px 12px;
                    font-size: 0.8rem;
                    font-weight: 600;
                }

                .crops-table-wrap {
                    overflow-x: auto;
                }

                .crops-table {
                    width: 100%;
                    border-collapse: collapse;
                    text-align: left;
                }

                .crops-table thead {
                    background: rgba(0,0,0,0.02);
                    border-bottom: 1px solid #edf0ee;
                }

                .crops-table th,
                .crops-table td {
                    padding: 14px 16px;
                    vertical-align: middle;
                }

                .crops-table th {
                    font-size: 0.86rem;
                    font-weight: 700;
                    color: var(--text-dark);
                }

                .crops-row {
                    border-bottom: 1px solid #f0f2f1;
                    transition: background 0.2s ease;
                }

                .crops-row:hover {
                    background: rgba(45,90,39,0.03);
                }

                .crops-description-cell {
                    color: var(--text-muted);
                    max-width: 420px;
                    white-space: normal;
                    line-height: 1.45;
                }

                .crops-action-row {
                    display: inline-flex;
                    align-items: center;
                    gap: 6px;
                }

                .crops-loading-bar {
                    height: 20px;
                    border-radius: 8px;
                    background: linear-gradient(110deg, rgba(0,0,0,0.04) 20%, rgba(0,0,0,0.08) 35%, rgba(0,0,0,0.04) 50%);
                    background-size: 220% 100%;
                    animation: cropsShimmer 1.2s linear infinite;
                }

                .crops-empty {
                    padding: 42px 18px;
                    text-align: center;
                    color: var(--text-muted);
                }

                .crops-empty svg {
                    color: rgba(45,90,39,0.3);
                    margin-bottom: 8px;
                }

                .crops-empty h4 {
                    margin: 0 0 8px;
                    color: var(--text-dark);
                    font-size: 1rem;
                }

                .crops-empty p {
                    margin: 0;
                    font-size: 0.88rem;
                }

                code {
                    background: rgba(0,0,0,0.05);
                    padding: 2px 6px;
                    border-radius: 6px;
                    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
                    font-size: 0.78rem;
                }

                @keyframes cropsPageIn {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }

                @keyframes cropsShimmer {
                    to { background-position-x: -220%; }
                }

                @media (max-width: 980px) {
                    .crops-layout {
                        grid-template-columns: 1fr;
                    }

                    .crops-editor-panel {
                        position: static;
                    }
                }

                @media (max-width: 640px) {
                    .crops-title {
                        font-size: 1.7rem;
                    }

                    .crops-table th,
                    .crops-table td {
                        padding: 12px 10px;
                        font-size: 0.84rem;
                    }
                }

                @media (prefers-reduced-motion: reduce) {
                    .crops-page,
                    .crops-panel,
                    .crops-row,
                    .crops-loading-bar {
                        animation: none !important;
                        transition: none !important;
                    }
                }
            `}</style>
        </div>
    );
};
