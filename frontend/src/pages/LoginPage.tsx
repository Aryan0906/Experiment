import React, { useState } from 'react';
import { API_URL } from '../types';

export const LoginPage: React.FC = () => {
    const [shopDomain, setShopDomain] = useState<string>('');

    const handleAuth = () => {
        if (!shopDomain) {
            alert('Please enter your Shopify store domain.');
            return;
        }

        // Clean up domain if user enters 'https://'
        let cleanDomain = shopDomain.trim().replace(/^https?:\/\//, '');
        if (!cleanDomain.endsWith('.myshopify.com')) {
            if (!cleanDomain.includes('.')) {
                cleanDomain = `${cleanDomain}.myshopify.com`;
            }
        }

        // Dynamically pass 'shop' property to backend
        window.location.href = `${API_URL}/auth/shopify/authorize?shop=${encodeURIComponent(cleanDomain)}`;
    };

    const handleDemo = () => {
        // Go directly to dashboard with the seeded demo data (seller_id=2)
        window.location.href = '/dashboard?seller_id=2&shop=demo-store.myshopify.com';
    };

    return (
        <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
            <div className="w-full max-w-md px-6">
                {/* Logo / Brand */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-emerald-500 mb-4 shadow-lg shadow-indigo-500/20">
                        <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                    </div>
                    <h1 className="text-3xl font-bold text-white tracking-tight">Catalog Sync</h1>
                    <p className="text-slate-400 mt-2">Extract product attributes automatically with AI</p>
                </div>

                {/* Login Card */}
                <div className="bg-slate-800/60 backdrop-blur-sm rounded-2xl p-8 border border-slate-700/50 shadow-2xl">
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                        Shopify Store Domain
                    </label>
                    <input
                        type="text"
                        value={shopDomain}
                        onChange={(e) => setShopDomain(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleAuth()}
                        placeholder="your-store.myshopify.com"
                        className="w-full px-4 py-3 bg-slate-900/50 border border-slate-600/50 rounded-xl
                                   text-white placeholder-slate-500
                                   focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent
                                   transition-all duration-200"
                    />

                    <button
                        onClick={handleAuth}
                        className="w-full mt-4 px-4 py-3 bg-gradient-to-r from-indigo-600 to-indigo-500
                                   text-white font-semibold rounded-xl
                                   hover:from-indigo-500 hover:to-indigo-400
                                   focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-slate-800
                                   transition-all duration-200 shadow-lg shadow-indigo-500/20
                                   active:scale-[0.98]"
                    >
                        Connect Shopify Store
                    </button>

                    {/* Divider */}
                    <div className="flex items-center my-5">
                        <div className="flex-1 h-px bg-slate-700"></div>
                        <span className="px-3 text-xs text-slate-500 uppercase tracking-wider">or</span>
                        <div className="flex-1 h-px bg-slate-700"></div>
                    </div>

                    {/* Demo Mode */}
                    <button
                        onClick={handleDemo}
                        className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600/50
                                   text-slate-300 font-medium rounded-xl
                                   hover:bg-slate-700 hover:text-white
                                   focus:outline-none focus:ring-2 focus:ring-slate-500
                                   transition-all duration-200
                                   active:scale-[0.98]"
                    >
                        Try Demo Mode
                    </button>
                    <p className="text-center text-xs text-slate-500 mt-2">
                        Explore with sample product data — no login required
                    </p>
                </div>

                {/* Footer */}
                <p className="text-center text-xs text-slate-600 mt-6">
                    Powered by VLM attribute extraction
                </p>
            </div>
        </div>
    );
};
