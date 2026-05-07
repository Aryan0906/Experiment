import React, { useState, useEffect } from 'react';
import { ProductTable } from '../components/ProductTable';
import { ExtractButton } from '../components/ExtractButton';
import { CSVDownload } from '../components/CSVDownload';
import type { Product, ExtractedAttribute } from '../types';
import { API_URL } from '../types';

export const DashboardPage: React.FC = () => {
    const [products, setProducts] = useState<Product[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [extracted, setExtracted] = useState<Record<string, { attributes: ExtractedAttribute, confidence: number }>>({});

    // Get seller_id from URL params or default to demo (id=2 for seeded data)
    const params = new URLSearchParams(window.location.search);
    const sellerId = parseInt(params.get('seller_id') || '2', 10);
    const shopName = params.get('shop') || 'demo-store.myshopify.com';

    const fetchProducts = async () => {
        try {
            setLoading(true);
            const res = await fetch(`${API_URL}/api/products?seller_id=${sellerId}`);
            if (res.ok) {
                const data = await res.json();
                setProducts(data.products || []);
            }
        } catch (e) {
            console.error("Failed to fetch products", e);
        } finally {
            setLoading(false);
        }
    };

    const fetchExtractedAttributes = async () => {
        try {
            const res = await fetch(`${API_URL}/api/extracted?seller_id=${sellerId}`);
            if (res.ok) {
                const data = await res.json();
                setExtracted(data.extracted || {});
            }
        } catch (e) {
            console.error("Failed to fetch extracted attributes", e);
        }
    };

    useEffect(() => {
        fetchProducts().then(() => fetchExtractedAttributes());
    }, []);

    const productCount = products.length;
    const extractedCount = Object.keys(extracted).length;

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
            {/* Header */}
            <header className="border-b border-slate-700/50 backdrop-blur-sm bg-slate-900/50">
                <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
                    <div>
                        <h1 className="text-2xl font-bold text-white tracking-tight">Catalog Sync</h1>
                        <p className="text-sm text-slate-400 mt-0.5">
                            Connected: <span className="text-emerald-400 font-medium">{shopName}</span>
                        </p>
                    </div>
                    <div className="flex items-center gap-3">
                        <ExtractButton
                            sellerId={sellerId}
                            onComplete={() => { fetchProducts(); fetchExtractedAttributes(); }}
                            disabled={productCount === 0}
                        />
                        <CSVDownload sellerId={sellerId} />
                    </div>
                </div>
            </header>

            {/* Stats bar */}
            <div className="max-w-7xl mx-auto px-6 py-5">
                <div className="grid grid-cols-3 gap-4 mb-6">
                    <div className="bg-slate-800/60 rounded-xl p-4 border border-slate-700/50">
                        <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Products</p>
                        <p className="text-2xl font-bold text-white mt-1">{productCount}</p>
                    </div>
                    <div className="bg-slate-800/60 rounded-xl p-4 border border-slate-700/50">
                        <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Extracted</p>
                        <p className="text-2xl font-bold text-emerald-400 mt-1">{extractedCount}</p>
                    </div>
                    <div className="bg-slate-800/60 rounded-xl p-4 border border-slate-700/50">
                        <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Coverage</p>
                        <p className="text-2xl font-bold text-amber-400 mt-1">
                            {productCount > 0 ? `${Math.round((extractedCount / productCount) * 100)}%` : '—'}
                        </p>
                    </div>
                </div>

                {/* Main content */}
                {loading ? (
                    <div className="flex items-center justify-center py-20">
                        <div className="animate-spin rounded-full h-8 w-8 border-2 border-emerald-500 border-t-transparent"></div>
                        <span className="ml-3 text-slate-400">Loading products...</span>
                    </div>
                ) : productCount === 0 ? (
                    <div className="text-center py-20">
                        <div className="text-4xl mb-3">📦</div>
                        <h2 className="text-xl font-semibold text-white mb-2">No products yet</h2>
                        <p className="text-slate-400">
                            Sync your Shopify store or run <code className="text-emerald-400 bg-slate-800 px-2 py-0.5 rounded text-sm">python -m app.seed</code> to add sample data.
                        </p>
                    </div>
                ) : (
                    <ProductTable products={products} extracted={extracted} />
                )}
            </div>
        </div>
    );
};
