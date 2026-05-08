import React from 'react';
import { API_URL } from '../types';

export const LoginPage: React.FC = () => {
    const [shop, setShop] = React.useState('');

    const handleAuth = () => {
        const domain = shop.trim() || 'myshop.myshopify.com';
        window.location.href = `${API_URL}/auth/shopify/authorize?shop=${encodeURIComponent(domain)}`;
    };

    return (
        <div className="flex items-center justify-center min-h-screen bg-gray-100">
            <div className="p-8 bg-white shadow-lg rounded-lg text-center max-w-sm w-full">
                <h1 className="text-2xl font-bold mb-4 text-gray-800">Catalog Sync</h1>
                <p className="text-gray-600 mb-6">Automate your Shopify product attribute extraction.</p>
                <input
                    type="text"
                    placeholder="your-store.myshopify.com"
                    value={shop}
                    onChange={(e) => setShop(e.target.value)}
                    className="w-full px-4 py-2 mb-4 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                />
                <button onClick={handleAuth} className="w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors">
                    Connect Shopify Store
                </button>
            </div>
        </div>
    );
};
