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
    const sellerId = 1;

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

    useEffect(() => { 
        Promise.resolve()
            .then(() => fetchProducts())
            .then(() => fetchExtractedAttributes()); 
    }, []);

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
                    <h1 className="text-2xl font-bold text-gray-800">Product Dashboard</h1>
                    <div className="flex space-x-4">
                        <ExtractButton sellerId={sellerId} onComplete={() => { fetchProducts(); fetchExtractedAttributes(); }} />
                        <CSVDownload sellerId={sellerId} />
                    </div>
                </div>
                {loading ? <div className="text-center py-10">Loading products...</div> : <ProductTable products={products} extracted={extracted} />}
            </div>
        </div>
    );
};
