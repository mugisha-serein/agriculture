export const SYSTEM_ERROR_EVENT = 'agri:system-error';
let currentSystemError: SystemErrorPayload | null = null;

export interface SystemErrorPayload {
    title?: string;
    message: string;
    source: 'api' | 'runtime';
    status?: number;
    code?: string;
    timestamp: string;
}

export const emitSystemError = (payload: Omit<SystemErrorPayload, 'timestamp'>): void => {
    const enrichedPayload: SystemErrorPayload = {
        ...payload,
        timestamp: new Date().toISOString()
    };

    currentSystemError = enrichedPayload;
    window.dispatchEvent(new CustomEvent<SystemErrorPayload>(SYSTEM_ERROR_EVENT, { detail: enrichedPayload }));
};

export const readSystemError = (): SystemErrorPayload | null => {
    return currentSystemError;
};

export const clearSystemError = (): void => {
    currentSystemError = null;
};
