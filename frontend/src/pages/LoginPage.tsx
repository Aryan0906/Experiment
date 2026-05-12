/**
 * Login Page with Google OAuth
 */
import React from 'react';
import { useGoogleLogin } from '@react-oauth/google';
import { useAuth } from '../hooks/useAuth';
import { useNavigate } from 'react-router-dom';

export const LoginPage: React.FC = () => {
    const { login: oauthLogin, isAuthenticated, isLoading } = useAuth();
    const navigate = useNavigate();

    // Redirect if already authenticated
    React.useEffect(() => {
        if (isAuthenticated && !isLoading) {
            navigate('/dashboard');
        }
    }, [isAuthenticated, isLoading, navigate]);

    const handleGoogleSuccess = async (credentialResponse: any) => {
        try {
            const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/auth/google`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    credential: credentialResponse.credential,
                }),
            });

            if (!response.ok) {
                throw new Error('Login failed');
            }

            const data = await response.json();
            localStorage.setItem('jwt_token', data.access_token);
            navigate('/dashboard');
        } catch (error) {
            console.error('Google login failed:', error);
            alert('Login failed. Please try again.');
        }
    };

    const handleGoogleFailure = () => {
        console.error('Google login failed');
        alert('Google login failed. Please try again.');
    };

    const { login } = useGoogleLogin({
        onSuccess: handleGoogleSuccess,
        onError: handleGoogleFailure,
    });

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
                <div className="text-center">
                    <svg className="animate-spin h-12 w-12 text-blue-600 mx-auto" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    <p className="mt-4 text-gray-600">Loading...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
            <div className="p-8 bg-white shadow-xl rounded-2xl text-center max-w-md w-full">
                <div className="mb-6">
                    <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
                        <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                        </svg>
                    </div>
                    <h1 className="text-3xl font-bold text-gray-800 mb-2">Catalog AI Suite</h1>
                    <p className="text-gray-600">
                        AI-powered product attribute extraction and anomaly detection for Shopify stores
                    </p>
                </div>

                <div className="space-y-4">
                    <button
                        onClick={login}
                        className="w-full flex items-center justify-center px-4 py-3 border border-gray-300 rounded-lg shadow-sm bg-white text-gray-700 hover:bg-gray-50 transition-colors font-medium"
                    >
                        <svg className="w-5 h-5 mr-3" viewBox="0 0 24 24">
                            <path
                                fill="#4285F4"
                                d="M23.766 12.2764c0-.9157-.0764-1.7928-.2292-2.6364H12v4.9357h6.6223c-.2864 1.5378-1.1543 2.8321-2.4579 3.6943v3.0598h3.9394c2.3045-2.1196 3.6619-5.2425 3.6619-9.0534z"
                            />
                            <path
                                fill="#34A853"
                                d="M12 24.2005c3.2993 0 6.0596-1.094 8.0994-2.9726l-3.9394-3.0598c-1.1029.7407-2.5128 1.1786-4.16 1.1786-3.1886 0-5.8929-2.1507-6.8579-5.043H1.0991v3.1614C3.1303 21.5005 7.2922 24.2005 12 24.2005z"
                            />
                            <path
                                fill="#FBBC05"
                                d="M5.1423 14.3037c-.2443-.7314-.3834-1.5143-.3834-2.3037s.1391-1.5723.3834-2.3037V6.535H1.0991C.3991 7.9266 0 9.5023 0 11.2c0 1.6977.3991 3.2734 1.0991 4.665l4.0432-3.1613z"
                            />
                            <path
                                fill="#EA4335"
                                d="M12 4.8537c1.7943 0 3.4086.6171 4.6857 1.6286l3.5143-3.5143C18.0714 1.094 15.3114 0 12 0 7.2922 0 3.1303 2.6999 1.0991 6.535l4.0432 3.1613c.965-2.8923 3.6693-5.043 6.8579-5.043z"
                            />
                        </svg>
                        Sign in with Google
                    </button>
                </div>

                <div className="mt-8 pt-6 border-t border-gray-200">
                    <p className="text-xs text-gray-500">
                        By signing in, you agree to our Terms of Service and Privacy Policy.
                    </p>
                </div>
            </div>
        </div>
    );
};

export default LoginPage;
