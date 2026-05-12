/**
 * AttributeEditor Component
 * Displays editable attribute fields with inline editing support
 */
import React, { useState, useCallback } from 'react';
import type { Product, AttributeKey } from '../types';
import { ATTRIBUTE_KEYS } from '../types';

interface AttributeEditorProps {
    product: Product;
    onUpdate: (attributes: Record<string, any>) => Promise<void>;
}

export const AttributeEditor: React.FC<AttributeEditorProps> = ({ product, onUpdate }) => {
    const attributes = product.corrected_attributes || product.attributes || {};
    const [editingKey, setEditingKey] = useState<string | null>(null);
    const [editValue, setEditValue] = useState<string>('');
    const [isSaving, setIsSaving] = useState(false);

    const handleEdit = useCallback((key: string, currentValue: string) => {
        setEditingKey(key);
        setEditValue(currentValue || '');
    }, []);

    const handleSave = useCallback(async () => {
        if (!editingKey) return;

        setIsSaving(true);
        try {
            const updatedAttributes = {
                ...attributes,
                [editingKey]: editValue.trim() || null,
            };
            await onUpdate(updatedAttributes);
        } catch (error) {
            console.error('Failed to save attribute:', error);
        } finally {
            setIsSaving(false);
            setEditingKey(null);
            setEditValue('');
        }
    }, [editingKey, editValue, attributes, onUpdate]);

    const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            handleSave();
        } else if (e.key === 'Escape') {
            setEditingKey(null);
            setEditValue('');
        }
    }, [handleSave]);

    const getValue = (key: string) => {
        const value = attributes[key];
        return typeof value === 'string' ? value : (value?.toString() || '');
    };

    return (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            <table className="w-full">
                <thead className="bg-gray-50">
                    <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Attribute
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Value
                        </th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                    {ATTRIBUTE_KEYS.map((attr) => {
                        const isEditing = editingKey === attr.key;
                        const value = getValue(attr.key);

                        return (
                            <tr key={attr.key} className="hover:bg-gray-50">
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                    {attr.label}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm">
                                    {isEditing ? (
                                        <div className="flex items-center space-x-2">
                                            <input
                                                type="text"
                                                value={editValue}
                                                onChange={(e) => setEditValue(e.target.value)}
                                                onKeyDown={handleKeyDown}
                                                onBlur={handleSave}
                                                autoFocus
                                                disabled={isSaving}
                                                className="flex-1 px-3 py-1 border border-blue-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                                                placeholder={`Enter ${attr.label.toLowerCase()}`}
                                            />
                                            {isSaving && (
                                                <svg className="animate-spin h-4 w-4 text-blue-500" fill="none" viewBox="0 0 24 24">
                                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                                </svg>
                                            )}
                                        </div>
                                    ) : (
                                        <button
                                            onClick={() => handleEdit(attr.key, value)}
                                            className="w-full text-left px-3 py-1 rounded-md hover:bg-gray-100 transition-colors text-gray-700"
                                            title="Click to edit"
                                        >
                                            {value || <span className="text-gray-400 italic">Not set</span>}
                                        </button>
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

export default AttributeEditor;
