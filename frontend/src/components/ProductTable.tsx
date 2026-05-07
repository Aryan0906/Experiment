import React from 'react';
import type { Product, ExtractedAttribute } from '../types';

interface ProductTableProps {
    products: Product[];
    extracted: Record<string, { attributes: ExtractedAttribute, confidence: number }>;
}

export const ProductTable: React.FC<ProductTableProps> = ({ products, extracted }) => {
    return (
        <div className="overflow-x-auto shadow-md sm:rounded-lg mt-6 bg-white p-4">
            <table className="w-full text-sm text-left text-gray-500">
                <thead className="text-xs text-gray-700 uppercase bg-gray-50">
                    <tr><th>Image</th><th>Title</th><th>Extracted Attributes</th><th>Confidence</th></tr>
                </thead>
                <tbody>
                    {products.map(p => {
                        const data = extracted[p.id];
                        return (
                            <tr key={p.id} className="border-b hover:bg-gray-50">
                                <td><img src={p.image_url} alt={p.title} className="w-16 h-16 object-cover" /></td>
                                <td className="font-medium text-gray-900">{p.title}</td>
                                <td>{data ? <pre className="text-xs bg-gray-100 p-2 rounded">{JSON.stringify(data.attributes, null, 2)}</pre> : <i>Not extracted yet</i>}</td>
                                <td>{data ? `${(data.confidence * 100).toFixed(0)}%` : "-"}</td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
};
