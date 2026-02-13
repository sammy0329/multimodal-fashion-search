"use client";

import Image from "next/image";
import type { SearchResult } from "@/types";

interface ProductCardProps {
  product: SearchResult;
  showSelect?: boolean;
  isSelected?: boolean;
  onToggle?: (id: string) => void;
}

export default function ProductCard({
  product,
  showSelect = false,
  isSelected = false,
  onToggle,
}: ProductCardProps) {
  return (
    <div className="group cursor-pointer">
      <div className="relative aspect-[3/4] bg-gray-100 rounded-lg overflow-hidden mb-3">
        <Image
          src={product.image_url}
          alt={product.name_ko ?? product.name}
          fill
          sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 20vw"
          className="object-cover group-hover:scale-105 transition-transform duration-300"
        />

        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors" />

        {showSelect && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onToggle?.(product.product_id);
            }}
            className={`
              absolute top-3 right-3 w-7 h-7 rounded-full border-2
              flex items-center justify-center transition-all
              ${
                isSelected
                  ? "bg-indigo-600 border-indigo-600 text-white"
                  : "bg-white/90 border-gray-300 hover:border-indigo-400"
              }
            `}
          >
            {isSelected && "✓"}
          </button>
        )}

        {product.score >= 0.9 && (
          <span className="absolute top-3 left-3 px-2 py-1 bg-red-500 text-white text-xs font-medium rounded">
            BEST
          </span>
        )}
      </div>

      <div>
        {product.brand && (
          <p className="text-xs text-gray-500 mb-1">{product.brand}</p>
        )}
        <p className="text-sm text-gray-900 mb-1 line-clamp-2">
          {product.name_ko ?? product.name}
        </p>
        <p className="text-sm font-bold text-gray-900">
          ₩{product.price.toLocaleString()}
        </p>
      </div>
    </div>
  );
}
