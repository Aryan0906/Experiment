import React from 'react';
import { API_URL } from '../types';

export const CSVDownload: React.FC<{ sellerId: number }> = ({ sellerId }) => {
    const handleDownload = async () => {
        const res = await fetch(`${API_URL}/api/products/csv?seller_id=${sellerId}`);
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `catalog_${Date.now()}.csv`;
        a.click();
    };

    return (
        <button onClick={handleDownload} className="px-4 py-2 bg-green-600 text-white rounded-md">
            Download CSV
        </button>
    );
};
