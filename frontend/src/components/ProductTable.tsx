import React from 'react';
import type { Product, ExtractedAttribute } from '../types';

interface ProductTableProps {
    products: Product[];
    extracted: Record<string, { attributes: ExtractedAttribute, confidence: number }>;
}

function confidenceColor(confidence: number): string {
    if (confidence >= 0.85) return 'text-emerald-400 bg-emerald-400/10 border-emerald-400/30';
    if (confidence >= 0.70) return 'text-amber-400 bg-amber-400/10 border-amber-400/30';
    return 'text-red-400 bg-red-400/10 border-red-400/30';
}

function confidenceBadge(confidence: number): string {
    if (confidence >= 0.85) return 'High';
    if (confidence >= 0.70) return 'Medium';
    return 'Low';
}

export const ProductTable: React.FC<ProductTableProps> = ({ products, extracted }) => {
    return (
        <div className="bg-slate-800/60 rounded-xl border border-slate-700/50 overflow-hidden">
            <table className="w-full text-sm text-left">
                <thead>
                    <tr className="border-b border-slate-700/50">
                        <th className="px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Image</th>
                        <th className="px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Product</th>
                        <th className="px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Price</th>
                        <th className="px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Extracted Attributes</th>
                        <th className="px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider text-center">Confidence</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-slate-700/30">
                    {products.map(p => {
                        const data = extracted[p.id];
                        return (
                            <tr key={p.id} className="hover:bg-slate-700/20 transition-colors">
                                {/* Image */}
                                <td className="px-4 py-3">
                                    <div className="w-14 h-14 rounded-lg overflow-hidden bg-slate-700 flex-shrink-0">
                                        {p.image_url ? (
                                            <img
                                                src={p.image_url}
                                                alt={p.title}
                                                className="w-full h-full object-cover"
                                                onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                                            />
                                        ) : (
                                            <div className="w-full h-full flex items-center justify-center text-slate-500 text-xs">N/A</div>
                                        )}
                                    </div>
                                </td>

                                {/* Title + SKU */}
                                <td className="px-4 py-3">
                                    <p className="font-medium text-white text-sm leading-tight">{p.title}</p>
                                    {p.sku && <p className="text-xs text-slate-500 mt-0.5">SKU: {p.sku}</p>}
                                </td>

                                {/* Price */}
                                <td className="px-4 py-3">
                                    <span className="text-slate-300 font-mono text-sm">
                                        {p.price ? `₹${parseFloat(p.price).toLocaleString('en-IN')}` : '—'}
                                    </span>
                                </td>

                                {/* Attributes */}
                                <td className="px-4 py-3">
                                    {data ? (
                                        <div className="flex flex-wrap gap-1.5">
                                            {Object.entries(data.attributes).map(([key, value]) =>
                                                value ? (
                                                    <span
                                                        key={key}
                                                        className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-slate-700/60 text-slate-300 border border-slate-600/50"
                                                    >
                                                        <span className="text-slate-500 mr-1">{key}:</span>
                                                        {String(value)}
                                                    </span>
                                                ) : null
                                            )}
                                        </div>
                                    ) : (
                                        <span className="text-slate-500 text-xs italic">Not extracted yet</span>
                                    )}
                                </td>

                                {/* Confidence */}
                                <td className="px-4 py-3 text-center">
                                    {data ? (
                                        <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold border ${confidenceColor(data.confidence)}`}>
                                            {(data.confidence * 100).toFixed(0)}% {confidenceBadge(data.confidence)}
                                        </span>
                                    ) : (
                                        <span className="text-slate-600">—</span>
                                    )}
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
};
