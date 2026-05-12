export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export interface User {
    id: number;
    email: string;
    name: string | null;
    avatar_url: string | null;
    is_admin: boolean;
}

export interface Product {
    id: number;
    user_id: number;
    image_url: string;
    status: 'queued' | 'extracting_attributes' | 'detecting_anomalies' | 'done' | 'error';
    attributes: Record<string, any> | null;
    corrected_attributes: Record<string, any> | null;
    anomaly_result: AnomalyResult | null;
    error_message: string | null;
    created_at: string;
    updated_at: string;
}

export interface AnomalyResult {
    is_blurry: boolean;
    blur_score: number;
    is_wrong_background: boolean;
    background_score: number;
    is_counterfeit: boolean;
    counterfeit_score: number;
    anomaly_score: number;
}

export interface ExtractedAttribute {
    brand?: string;
    size?: string;
    color?: string;
    material?: string;
    category?: string;
    confidence?: number;
}

export interface AttributeKey {
    key: string;
    label: string;
}

export const ATTRIBUTE_KEYS: AttributeKey[] = [
    { key: 'brand', label: 'Brand' },
    { key: 'color', label: 'Color' },
    { key: 'material', label: 'Material' },
    { key: 'size', label: 'Size' },
    { key: 'category', label: 'Category' },
];
