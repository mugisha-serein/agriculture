import { create } from 'zustand';

interface User {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
    phone: string;
    role: 'buyer' | 'seller' | 'transporter' | 'admin';
    is_verified: boolean;
}

interface AuthState {
    user: User | null;
    isAuthenticated: boolean;
    setAuth: (user: User, accessToken: string, refreshToken: string) => void;
    logout: () => void;
    checkAuth: () => void;
}

const getInitialUser = (): User | null => {
    const userJson = sessionStorage.getItem('user');
    try {
        return userJson ? JSON.parse(userJson) : null;
    } catch (e) {
        return null;
    }
};

export const useAuthStore = create<AuthState>((set) => ({
    user: getInitialUser(),
    isAuthenticated: !!sessionStorage.getItem('access_token'),

    setAuth: (user, accessToken, refreshToken) => {
        sessionStorage.setItem('access_token', accessToken);
        sessionStorage.setItem('refresh_token', refreshToken);
        sessionStorage.setItem('user', JSON.stringify(user));
        set({ user, isAuthenticated: true });
    },

    logout: () => {
        sessionStorage.removeItem('access_token');
        sessionStorage.removeItem('refresh_token');
        sessionStorage.removeItem('user');
        set({ user: null, isAuthenticated: false });
    },

    checkAuth: () => {
        const token = sessionStorage.getItem('access_token');
        const userJson = sessionStorage.getItem('user');

        if (!token || !userJson) {
            sessionStorage.removeItem('access_token');
            sessionStorage.removeItem('refresh_token');
            sessionStorage.removeItem('user');
            set({ user: null, isAuthenticated: false });
            return;
        }

        try {
            const user = JSON.parse(userJson);
            set({ user, isAuthenticated: true });
        } catch (e) {
            sessionStorage.clear();
            set({ user: null, isAuthenticated: false });
        }
    },
}));
