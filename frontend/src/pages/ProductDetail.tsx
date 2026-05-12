/**
 * ProductDetail Page
 * Displays product details with status tracker, attribute editor, and anomaly warnings
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import type { Product, AnomalyResult } from '../types';
import { API_URL } from '../types';
import StatusTracker from '../components/StatusTracker';
import AttributeEditor from '../components/AttributeEditor';
import AnomalyWarning from '../components/AnomalyWarning';
import CSVDownload from '../components/CSVDownload';

const ProductDetail: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const { isAuthenticated, isLoading } = useAuth();
    const navigate = useNavigate();
    const [product, setProduct] = useState<Product | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isSaving, setIsSaving] = useState(false);

    // Redirect if not authenticated
    useEffect(() => {
        if (!isLoading && !isAuthenticated) {
            navigate('/login');
        }
    }, [isAuthenticated, isLoading, navigate]);

    // Fetch product data
    const fetchProduct = async () => {
        if (!id) return;

        try {
            const response = await fetch(`${API_URL}/products/${id}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`,
                },
            });

            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error('Product not found');
                }
                throw new Error('Failed to fetch product');
            }

            const data = await response.json();
            setProduct(data);
            setError(null);
        } catch (err: any) {
            console.error('Failed to fetch product:', err);
            setError(err.message || 'Failed to load product details');
        } finally {
            setLoading(false);
        }
    };

    // Poll for status updates when processing
    useEffect(() => {
        if (!product || product.status === 'done' || product.status === 'error') {
            return;
        }

        const interval = setInterval(() => {
            fetchProduct();
        }, 2000); // Poll every 2 seconds

        return () => clearInterval(interval);
    }, [product?.status, id]);

    // Initial fetch
    useEffect(() => {
        if (isAuthenticated && id) {
            fetchProduct();
        }
    }, [id, isAuthenticated]);

    // Handle attribute update
    const handleAttributeUpdate = async (attributes: Record<string, any>) => {
        if (!id || !product) return;

        setIsSaving(true);
        try {
            const response = await fetch(`${API_URL}/products/${id}/attributes`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`,
                },
                body: JSON.stringify(attributes),
            });

            if (!response.ok) {
                throw new Error('Failed to save attributes');
            }

            // Update local state with the response
            const updatedProduct = await response.json();
            setProduct(updatedProduct);
        } catch (err: any) {
            console.error('Failed to save attributes:', err);
            alert('Failed to save changes. Please try again.');
        } finally {
            setIsSaving(false);
        }
    };

    if (isLoading) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <svg className="animate-spin h-12 w-12 text-blue-600" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg className="w-10 h-10 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                    <h2 className="text-xl font-semibold text-gray-800 mb-2">Error</h2>
                    <p className="text-gray-600 mb-4">{error}</p>
                    <button
                        onClick={() => navigate('/dashboard')}
                        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                        Back to Dashboard
                    </button>
                </div>
            </div>
        );
    }

    if (!product) {
        return null;
    }

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                            <button
                                onClick={() => navigate('/dashboard')}
                                className="text-gray-600 hover:text-gray-800"
                            >
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                                </svg>
                            </button>
                            <h1 className="text-xl font-bold text-gray-800">Product Details</h1>
                        </div>
                        {product.status === 'done' && (
                            <CSVDownload productId={product.id} />
                        )}
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Left Column - Image and Status */}
                    <div className="space-y-6">
                        {/* Product Image */}
                        <div className="bg-white rounded-2xl shadow-sm overflow-hidden">
                            <img
                                src={product.image_url}
                                alt="Product"
                                className="w-full h-96 object-contain bg-gray-100"
                            />
                        </div>

                        {/* Status Tracker */}
                        <StatusTracker status={product.status} errorMessage={product.error_message} />
                    </div>

                    {/* Right Column - Attributes and Anomalies */}
                    <div className="space-y-6">
                        {/* Attribute Editor */}
                        <div>
                            <h2 className="text-lg font-semibold text-gray-800 mb-4">Extracted Attributes</h2>
                            {product.status === 'done' ? (
                                <AttributeEditor product={product} onUpdate={handleAttributeUpdate} />
                            ) : (
                                <div className="bg-white border border-gray-200 rounded-lg p-8 text-center">
                                    <svg className="animate-spin h-10 w-10 text-blue-600 mx-auto mb-4" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                    </svg>
                                    <p className="text-gray-600">Waiting for attribute extraction...</p>
                                </div>
                            )}
                        </div>

                        {/* Anomaly Warnings */}
                        {product.status === 'done' && product.anomaly_result && (
                            <div>
                                <h2 className="text-lg font-semibold text-gray-800 mb-4">Quality Check Results</h2>
                                <AnomalyWarning anomalyResult={product.anomaly_result as AnomalyResult} />
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
};

export default ProductDetail;
