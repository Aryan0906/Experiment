/**
 * CSVDownload Component
 * Downloads product attributes as CSV file
 */
import React from 'react';
import { API_URL } from '../types';

interface CSVDownloadProps {
    productId: number;
}

export const CSVDownload: React.FC<CSVDownloadProps> = ({ productId }) => {
    const handleDownload = async () => {
        try {
            const response = await fetch(`${API_URL}/products/${productId}/csv`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`,
                },
            });
            
            if (!response.ok) {
                throw new Error('Failed to download CSV');
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `product_${productId}_attributes.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('CSV download failed:', error);
            alert('Failed to download CSV. Please try again.');
        }
    };

    return (
        <button 
            onClick={handleDownload} 
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors flex items-center space-x-2"
        >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span>Download CSV</span>
        </button>
    );
};

export default CSVDownload;
