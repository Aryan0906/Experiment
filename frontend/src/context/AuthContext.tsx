/**
 * Authentication Context for Google OAuth
 * Provides user authentication state and token management
 */
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useGoogleLogin, googleLogout } from '@react-oauth/google';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface User {
    id: number;
    email: string;
    name: string | null;
    avatar_url: string | null;
    is_admin: boolean;
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    login: () => void;
    logout: () => void;
    error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(localStorage.getItem('jwt_token'));
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Axios instance with interceptor
    const api = axios.create({
        baseURL: API_URL,
        headers: {
            'Content-Type': 'application/json',
        },
    });

    // Add token to requests and handle 401 errors
    api.interceptors.request.use(
        (config) => {
            const currentToken = localStorage.getItem('jwt_token');
            if (currentToken) {
                config.headers.Authorization = `Bearer ${currentToken}`;
            }
            return config;
        },
        (error) => Promise.reject(error)
    );

    api.interceptors.response.use(
        (response) => response,
        (error) => {
            if (error.response?.status === 401) {
                // Token expired or invalid
                localStorage.removeItem('jwt_token');
                setToken(null);
                setUser(null);
                window.location.href = '/login';
            }
            return Promise.reject(error);
        }
    );

    // Check for existing token on mount
    useEffect(() => {
        const checkAuth = async () => {
            const storedToken = localStorage.getItem('jwt_token');
            if (storedToken) {
                try {
                    const response = await api.get('/auth/me');
                    setUser(response.data);
                    setToken(storedToken);
                } catch (err) {
                    console.error('Token validation failed:', err);
                    localStorage.removeItem('jwt_token');
                    setToken(null);
                    setUser(null);
                }
            }
            setIsLoading(false);
        };

        checkAuth();
    }, []);

    // Google Login handler
    const handleGoogleSuccess = useCallback(async (credentialResponse: any) => {
        try {
            setError(null);
            const response = await api.post('/auth/google', {
                credential: credentialResponse.credential,
            });

            const { access_token, ...userData } = response.data;

            // Store token and user data
            localStorage.setItem('jwt_token', access_token);
            setToken(access_token);
            setUser(userData as User);

            // Redirect to dashboard
            window.location.href = '/dashboard';
        } catch (err: any) {
            console.error('Google login failed:', err);
            setError(err.response?.data?.detail || 'Login failed. Please try again.');
        }
    }, []);

    const handleGoogleFailure = useCallback((error: any) => {
        console.error('Google login error:', error);
        setError('Google login failed. Please try again.');
    }, []);

    const { login } = useGoogleLogin({
        onSuccess: handleGoogleSuccess,
        onError: handleGoogleFailure,
    });

    const logout = useCallback(() => {
        googleLogout();
        localStorage.removeItem('jwt_token');
        setToken(null);
        setUser(null);
        window.location.href = '/login';
    }, []);

    const value: AuthContextType = {
        user,
        token,
        isAuthenticated: !!user && !!token,
        isLoading,
        login,
        logout,
        error,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

export default AuthContext;
