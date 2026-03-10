import axios, { AxiosError } from 'axios';

import { emitSystemError } from './systemError';

interface DynamicErrorInfo {
    message: string;
    status?: number;
    code?: string;
}

const extractFromObject = (value: Record<string, unknown>): string | null => {
    if (typeof value.detail === 'string' && value.detail.trim()) {
        return value.detail;
    }

    if (typeof value.message === 'string' && value.message.trim()) {
        return value.message;
    }

    if (typeof value.error === 'string' && value.error.trim()) {
        return value.error;
    }

    for (const [key, raw] of Object.entries(value)) {
        if (Array.isArray(raw) && raw.length > 0) {
            const first = raw[0];
            if (typeof first === 'string' && first.trim()) {
                return `${key}: ${first}`;
            }
        }

        if (typeof raw === 'string' && raw.trim()) {
            return `${key}: ${raw}`;
        }
    }

    return null;
};

export const extractDynamicErrorInfo = (error: unknown): DynamicErrorInfo => {
    if (axios.isAxiosError(error)) {
        const axiosError = error as AxiosError;
        const status = axiosError.response?.status;
        const code = axiosError.code;
        const data = axiosError.response?.data;

        if (data && typeof data === 'object') {
            const parsed = extractFromObject(data as Record<string, unknown>);
            if (parsed) {
                return { message: parsed, status, code };
            }
        }

        if (typeof data === 'string' && data.trim()) {
            return { message: data, status, code };
        }

        if (axiosError.message?.trim()) {
            return { message: axiosError.message, status, code };
        }

        if (typeof status === 'number') {
            return { message: `Request failed with status ${status}.`, status, code };
        }
    }

    if (error instanceof Error && error.message.trim()) {
        return { message: error.message };
    }

    return { message: 'Unexpected error.' };
};

export const reportApiError = (title: string, error: unknown): void => {
    const details = extractDynamicErrorInfo(error);
    emitSystemError({
        source: 'api',
        title,
        message: details.message,
        status: details.status,
        code: details.code
    });
};

export const reportRuntimeError = (title: string, message: string): void => {
    emitSystemError({
        source: 'runtime',
        title,
        message
    });
};

export const reportRequiredFieldsError = (title: string, fields: string[]): void => {
    const normalized = fields
        .map((field) => field.trim())
        .filter(Boolean);

    const fieldLabel = normalized.join(', ');
    const verb = normalized.length > 1 ? 'are' : 'is';
    reportRuntimeError(title, `${fieldLabel} ${verb} required.`);
};

export const reportPasswordMismatchError = (title: string): void => {
    reportRuntimeError(title, 'New password and confirm password do not match.');
};

export const reportPasswordMinLengthError = (title: string, minLength: number): void => {
    reportRuntimeError(title, `Password must be at least ${minLength} characters.`);
};
