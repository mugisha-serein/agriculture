import axios, { AxiosError } from 'axios';

import { emitSystemError } from '../lib/systemError';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

type RetriableConfig = NonNullable<AxiosError['config']> & { _retry?: boolean };

const extractErrorMessage = (error: AxiosError): string => {
    const responseData = error.response?.data;
    if (responseData && typeof responseData === 'object') {
        const detail = (responseData as Record<string, unknown>).detail;
        if (typeof detail === 'string' && detail.trim()) {
            return detail;
        }
    }

    if (error.message && error.message.trim()) {
        return error.message;
    }

    return 'A system error occurred. Please try again.';
};

// Request interceptor to add JWT token
api.interceptors.request.use(
    (config) => {
        const token = sessionStorage.getItem('access_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor for token refresh (Simplified)
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const axiosError = error as AxiosError;
        const originalRequest = axiosError.config as RetriableConfig | undefined;

        if (axiosError.response?.status === 401 && originalRequest && !originalRequest._retry) {
            originalRequest._retry = true;
            const refreshToken = sessionStorage.getItem('refresh_token');

            if (refreshToken) {
                try {
                    const response = await axios.post(`${API_URL}/identity/refresh/`, {
                        refresh_token: refreshToken,
                    });

                    const { access_token } = response.data;
                    sessionStorage.setItem('access_token', access_token);

                    originalRequest.headers.Authorization = `Bearer ${access_token}`;
                    return api(originalRequest);
                } catch (refreshError) {
                    // Refresh failed, logout user
                    sessionStorage.removeItem('access_token');
                    sessionStorage.removeItem('refresh_token');
                    sessionStorage.removeItem('user');
                    window.location.href = '/login';
                }
            }
        }

        const statusCode = axiosError.response?.status;
        const isNetworkError = !axiosError.response;
        const isServerError = typeof statusCode === 'number' && statusCode >= 500;

        if (isNetworkError || isServerError) {
            emitSystemError({
                source: 'api',
                title: isNetworkError ? 'Network Error' : 'Server Error',
                message: extractErrorMessage(axiosError),
                status: statusCode,
                code: axiosError.code
            });
        }

        return Promise.reject(error);
    }
);
