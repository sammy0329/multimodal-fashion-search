export interface Product {
  product_id: string;
  name: string;
  name_ko: string | null;
  price: number;
  brand: string | null;
  category: string | null;
  sub_category: string | null;
  style_tags: string[];
  color: string | null;
  image_url: string;
  description: string | null;
  material: string | null;
  season: string | null;
  is_soldout: boolean;
}

export interface SearchResult {
  product_id: string;
  name: string;
  name_ko: string | null;
  price: number;
  brand: string | null;
  category: string | null;
  sub_category: string | null;
  style_tags: string[];
  color: string | null;
  image_url: string;
  score: number;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  query_type: "text" | "image" | "hybrid";
}

export interface SearchFilters {
  category?: string;
  sub_category?: string;
  brand?: string;
  min_price?: number;
  max_price?: number;
  color?: string;
  season?: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  meta?: {
    total: number;
    page: number;
    limit: number;
  };
}
