"use client";

import type { SearchResult } from "@/types";

interface ProductCardProps {
  product: SearchResult;
}

export default function ProductCard({ product }: ProductCardProps) {
  return (
    <div className="rounded-lg border border-gray-200 overflow-hidden hover:shadow-md transition-shadow">
      <div className="aspect-square bg-gray-100 flex items-center justify-center">
        <span className="text-gray-400 text-sm">이미지</span>
      </div>
      <div className="p-4">
        <p className="text-sm font-medium truncate">
          {product.name_ko ?? product.name}
        </p>
        {product.brand && (
          <p className="text-xs text-gray-500 mt-1">{product.brand}</p>
        )}
        <p className="text-sm font-bold mt-2">
          {product.price.toLocaleString()}원
        </p>
      </div>
    </div>
  );
}
