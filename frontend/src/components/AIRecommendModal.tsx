"use client";

import Image from "next/image";
import { useEffect } from "react";
import { useRecommend } from "@/hooks/useRecommend";
import type { SearchResult } from "@/types";

interface AIRecommendModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedProducts: SearchResult[];
  userQuery?: string;
}

export default function AIRecommendModal({
  isOpen,
  onClose,
  selectedProducts,
  userQuery,
}: AIRecommendModalProps) {
  const { comment, isStreaming, error, recommend, reset } = useRecommend();

  useEffect(() => {
    if (isOpen && selectedProducts.length > 0) {
      recommend(
        selectedProducts.map((p) => p.product_id),
        userQuery
      );
    }
    return () => reset();
  }, [isOpen, selectedProducts, userQuery, recommend, reset]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      <div className="relative w-full max-w-2xl max-h-[85vh] bg-white rounded-2xl shadow-2xl overflow-hidden animate-fadeIn">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h2 className="text-lg font-bold text-gray-900">
            AI 스타일리스트 추천
          </h2>
          <button
            onClick={onClose}
            className="w-10 h-10 flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition-colors"
          >
            <span className="text-xl">×</span>
          </button>
        </div>

        <div className="overflow-y-auto max-h-[calc(85vh-140px)] p-6">
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-500 mb-3">
              선택하신 아이템
            </h3>
            <div className="flex gap-4 overflow-x-auto pb-2">
              {selectedProducts.map((product) => (
                <div key={product.product_id} className="flex-shrink-0 w-28">
                  <div className="relative aspect-[3/4] rounded-lg overflow-hidden bg-gray-100 mb-2">
                    <Image
                      src={product.image_url}
                      alt={product.name_ko ?? product.name}
                      fill
                      sizes="112px"
                      className="object-cover"
                    />
                  </div>
                  <p className="text-xs text-gray-500">{product.brand}</p>
                  <p className="text-sm text-gray-900 truncate">
                    {product.name_ko ?? product.name}
                  </p>
                  <p className="text-sm font-bold text-gray-900">
                    ₩{product.price.toLocaleString()}
                  </p>
                </div>
              ))}
            </div>
          </div>

          <hr className="border-gray-100 mb-6" />

          <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl p-5">
            <div className="flex gap-3">
              <span className="text-2xl flex-shrink-0">💬</span>
              <div className="flex-1 min-w-0">
                {error ? (
                  <p className="text-red-600">{error}</p>
                ) : isStreaming && !comment ? (
                  <div className="flex items-center gap-2 text-gray-500">
                    <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" />
                    <div
                      className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce"
                      style={{ animationDelay: "0.1s" }}
                    />
                    <div
                      className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce"
                      style={{ animationDelay: "0.2s" }}
                    />
                    <span className="ml-2">분석 중...</span>
                  </div>
                ) : (
                  <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                    {comment}
                    {isStreaming && (
                      <span className="inline-block w-0.5 h-5 bg-indigo-600 ml-0.5 animate-pulse" />
                    )}
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="px-6 py-4 border-t border-gray-100 bg-gray-50 flex gap-3">
          <button
            onClick={() =>
              recommend(
                selectedProducts.map((p) => p.product_id),
                userQuery
              )
            }
            disabled={isStreaming}
            className="flex-1 py-3 border border-gray-300 rounded-xl text-gray-700 font-medium hover:bg-white disabled:opacity-50 transition-colors"
          >
            다른 추천
          </button>
          <button
            onClick={onClose}
            className="flex-1 py-3 bg-indigo-600 text-white font-medium rounded-xl hover:bg-indigo-700 transition-colors"
          >
            쇼핑 계속하기
          </button>
        </div>
      </div>
    </div>
  );
}
