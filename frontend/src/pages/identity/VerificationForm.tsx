import React, { useState } from 'react';
import { ArrowRight, FileText, Upload } from 'lucide-react';

import { api } from '../../api/client';
import { Button } from '../../components/ui';
import { reportApiError, reportRequiredFieldsError } from '../../lib/identityError';
import { SystemInlineError } from '../Error';

interface VerificationFormProps {
    title?: string;
    description?: string;
    activationToken?: string;
    submitLabel?: string;
    onSubmitted?: () => void;
}

interface VerificationFiles {
    front: File | null;
    back: File | null;
    selfie: File | null;
}

export const VerificationForm: React.FC<VerificationFormProps> = ({
    title = 'Identity Verification',
    description,
    activationToken,
    submitLabel = 'Submit for Review',
    onSubmitted
}) => {
    const [documentType, setDocumentType] = useState('national_id');
    const [documentNumber, setDocumentNumber] = useState('');
    const [files, setFiles] = useState<VerificationFiles>({
        front: null,
        back: null,
        selfie: null
    });
    const [isLoading, setIsLoading] = useState(false);

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>, type: keyof VerificationFiles) => {
        const selectedFile = event.target.files?.[0];
        if (!selectedFile) {
            return;
        }

        setFiles((currentFiles) => ({ ...currentFiles, [type]: selectedFile }));
    };

    const handleSubmit = async (event: React.FormEvent) => {
        event.preventDefault();

        if (!files.front || !documentNumber) {
            reportRequiredFieldsError('Verification Validation Error', ['Document number', 'Front image']);
            return;
        }

        setIsLoading(true);
        try {
            const formData = new FormData();
            formData.append('document_type', documentType);
            formData.append('document_number', documentNumber);
            if (files.front) formData.append('document_front', files.front);
            if (files.back) formData.append('document_back', files.back);
            if (files.selfie) formData.append('selfie', files.selfie);
            if (activationToken) formData.append('activation_token', activationToken);

            await api.post('/verification/submit/', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            onSubmitted?.();
        } catch (err: unknown) {
            reportApiError('Verification Submission Failed', err);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div>
            <h2 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '8px', color: 'var(--text-dark)' }}>{title}</h2>
            {description && (
                <p style={{ color: 'var(--text-muted)', fontSize: '1rem', marginBottom: '32px' }}>
                    {description}
                </p>
            )}
            <SystemInlineError marginBottom="24px" />

            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        <label style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-muted)' }}>Document Type</label>
                        <select
                            value={documentType}
                            onChange={(event) => setDocumentType(event.target.value)}
                            style={{ padding: '0 16px', height: '48px', borderRadius: 'var(--radius-md)', border: '1px solid #e5e7eb', outline: 'none', fontSize: '1rem', background: 'white' }}
                        >
                            <option value="national_id">National ID Card</option>
                            <option value="passport">International Passport</option>
                            <option value="driver_license">Driver's License</option>
                            <option value="business_registration">Business License</option>
                        </select>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        <label style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-muted)' }}>Document Number</label>
                        <input
                            value={documentNumber}
                            onChange={(event) => setDocumentNumber(event.target.value)}
                            placeholder="ID number"
                            required
                            style={{ width: '100%', height: '48px', padding: '10px 16px', borderRadius: 'var(--radius-md)', border: '1px solid #e5e7eb', fontSize: '0.95rem', outline: 'none' }}
                        />
                    </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                    <FileUploadBox
                        label="Front of Document"
                        file={files.front}
                        onChange={(event) => handleFileChange(event, 'front')}
                        required
                    />
                    <FileUploadBox
                        label="Back of Document (Optional)"
                        file={files.back}
                        onChange={(event) => handleFileChange(event, 'back')}
                    />
                </div>

                <FileUploadBox
                    label="Selfie with Document"
                    desc="Hold your document next to your face so we can verify it is you."
                    file={files.selfie}
                    onChange={(event) => handleFileChange(event, 'selfie')}
                />

                <Button type="submit" size="lg" isLoading={isLoading} fullWidth style={{ height: '56px', fontSize: '1.05rem', marginTop: '8px' }}>
                    {submitLabel} <ArrowRight size={20} />
                </Button>
            </form>
        </div>
    );
};

const FileUploadBox = ({
    label,
    desc,
    file,
    onChange,
    required = false
}: {
    label: string;
    desc?: string;
    file: File | null;
    onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
    required?: boolean;
}) => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <label style={{ fontWeight: 600, fontSize: '0.9rem' }}>{label} {required && '*'}</label>
        {desc && <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '4px' }}>{desc}</p>}
        <div style={{
            position: 'relative',
            height: '140px',
            border: '2px dashed #e5e7eb',
            borderRadius: 'var(--radius-md)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            background: file ? '#f0fdf4' : '#f9fafb',
            borderColor: file ? 'var(--success)' : '#e5e7eb',
            transition: 'var(--transition-normal)',
            cursor: 'pointer'
        }}>
            {file ? (
                <>
                    <FileText size={32} color="var(--success)" />
                    <p style={{ fontSize: '0.8rem', marginTop: '8px', fontWeight: 600, color: 'var(--text-success)' }}>{file.name}</p>
                </>
            ) : (
                <>
                    <Upload size={32} color="#9ca3af" />
                    <p style={{ fontSize: '0.8rem', marginTop: '8px', color: '#9ca3af' }}>Click to upload image</p>
                </>
            )}
            <input
                type="file"
                accept="image/*"
                onChange={onChange}
                required={required}
                style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', opacity: 0, cursor: 'pointer' }}
            />
        </div>
    </div>
);
