export const API_URL = import.meta.env.VITE_API_URL || "";

export interface Product {
    id: string; title: string; image_url: string; description: string; price: string; sku: string;
}

export interface ExtractedAttribute {
    brand?: string; size?: string; color?: string; material?: string; category?: string; confidence?: number;
}
