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
        window.URL.revokeObjectURL(url);
    };

    return (
        <button
            onClick={handleDownload}
            className="px-5 py-2.5 rounded-lg text-sm font-semibold transition-all duration-200
                       bg-emerald-600 text-white hover:bg-emerald-500
                       shadow-lg hover:shadow-emerald-500/20
                       flex items-center gap-2 active:scale-95"
        >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Download CSV
        </button>
    );
};
