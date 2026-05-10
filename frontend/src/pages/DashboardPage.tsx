import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { ProductTable } from '../components/ProductTable';
import { ExtractButton } from '../components/ExtractButton';
import { CSVDownload } from '../components/CSVDownload';
import type { Product, ExtractedAttribute } from '../types';
import { API_URL } from '../types';

export const DashboardPage: React.FC = () => {
    const [searchParams] = useSearchParams();
    const shop = searchParams.get('shop') || '';
    
    const [products, setProducts] = useState<Product[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [sellerId, setSellerId] = useState<number | null>(null);
    const [extracted, setExtracted] = useState<Record<string, { attributes: ExtractedAttribute, confidence: number }>>({});

    // Fetch seller ID from backend using shop domain
    useEffect(() => {
        if (!shop) return;
        
        fetch(`${API_URL}/auth/seller?shop=${encodeURIComponent(shop)}`)
            .then(res => res.json())
            .then(data => {
                if (data.seller_id) {
                    setSellerId(data.seller_id);
                } else {
                    console.error('Seller not found');
                }
            })
            .catch(err => console.error('Failed to fetch seller', err));
    }, [shop]);

    const fetchProducts = async () => {
        if (!sellerId) return;
        
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

    useEffect(() => { 
        if (!sellerId) return;
        
        Promise.resolve()
            .then(() => fetchProducts())
            .then(() => fetchExtractedAttributes()); 
    }, [sellerId]);

    const fetchExtractedAttributes = async () => {
        try {
            const res = await fetch(`${API_URL}/api/extracted?seller_id=${sellerId}`);
            if (res.ok) {
                const data = await res.json();
                setExtracted(data.extracted || {});
            }
        } catch (e) {
            console.error("Failed to fetch extracted attributes", e);
            setExtracted({});
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 p-8">
            <div className="max-w-6xl mx-auto">
                <div className="flex justify-between items-center mb-6">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-800">Product Dashboard</h1>
                        {shop && <p className="text-sm text-gray-500 mt-1">Connected to: {shop}</p>}
                    </div>
                    <div className="flex space-x-4">
                        {!sellerId ? (
                            <button disabled className="px-4 py-2 bg-gray-400 text-white rounded-md cursor-not-allowed">
                                Loading...
                            </button>
                        ) : (
                            <>
                                <ExtractButton sellerId={sellerId} onComplete={() => { fetchProducts(); fetchExtractedAttributes(); }} />
                                <CSVDownload sellerId={sellerId} />
                            </>
                        )}
                    </div>
                </div>
                {loading ? <div className="text-center py-10">Loading products...</div> : <ProductTable products={products} extracted={extracted} />}
            </div>
        </div>
    );
};
