"use client";

import Image from "next/image";
import { Suspense, useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import AIRecommendModal from "@/components/AIRecommendModal";
import FilterPanel from "@/components/FilterPanel";
import Footer from "@/components/layout/Footer";
import Navbar from "@/components/layout/Navbar";
import ProductCard from "@/components/ProductCard";
import SearchBar from "@/components/SearchBar";
import { useSearch } from "@/hooks/useSearch";
import type { SearchFilters } from "@/types";

function ResultsContent() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get("q") ?? "";
  const hasImage = searchParams.get("hasImage") === "true";
  const categoryParam = searchParams.get("category");

  const { data, isLoading, error, search } = useSearch();

  const [filters, setFilters] = useState<SearchFilters>({
    category: categoryParam ?? undefined,
  });
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentQuery, setCurrentQuery] = useState(initialQuery);

  const selectedProducts =
    data?.results.filter((p) => selectedIds.includes(p.product_id)) ?? [];

  const handleSearch = useCallback(
    (query: string, imageBase64?: string) => {
      setCurrentQuery(query);
      search({
        query: query || undefined,
        image: imageBase64,
        filters,
      });
    },
    [search, filters]
  );

  useEffect(() => {
    const imageBase64 = hasImage
      ? sessionStorage.getItem("searchImage") ?? undefined
      : undefined;

    if (initialQuery || imageBase64 || categoryParam) {
      search({
        query: initialQuery || undefined,
        image: imageBase64,
        filters: { ...filters, category: categoryParam ?? filters.category },
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (currentQuery || hasImage) {
      const imageBase64 = hasImage
        ? sessionStorage.getItem("searchImage") ?? undefined
        : undefined;
      search({
        query: currentQuery || undefined,
        image: imageBase64,
        filters,
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters]);

  const toggleProduct = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const removeProduct = (id: string) => {
    setSelectedIds((prev) => prev.filter((i) => i !== id));
  };

  return (
    <main className="min-h-screen bg-white">
      <Navbar />

      <div className="border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <SearchBar
            defaultValue={currentQuery}
            onSearch={handleSearch}
            variant="compact"
          />
        </div>
      </div>

      {(currentQuery || data) && (
        <div className="max-w-7xl mx-auto px-4 py-4">
          <p className="text-gray-600">
            {currentQuery && (
              <>
                &quot;
                <span className="font-medium text-gray-900">{currentQuery}</span>
                &quot;{" "}
              </>
            )}
            검색결과{" "}
            <span className="font-medium text-gray-900">
              {data?.total ?? 0}
            </span>
            개
          </p>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 pb-32">
        <div className="flex gap-8">
          <div className="hidden lg:block w-56 flex-shrink-0">
            <div className="sticky top-24">
              <FilterPanel filters={filters} onChange={setFilters} />
            </div>
          </div>

          <div className="flex-1">
            {isLoading ? (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                {Array.from({ length: 8 }).map((_, i) => (
                  <div key={i} className="animate-pulse">
                    <div className="aspect-[3/4] bg-gray-200 rounded-lg mb-3" />
                    <div className="h-3 bg-gray-200 rounded w-1/3 mb-2" />
                    <div className="h-4 bg-gray-200 rounded w-2/3 mb-2" />
                    <div className="h-4 bg-gray-200 rounded w-1/2" />
                  </div>
                ))}
              </div>
            ) : error ? (
              <div className="text-center py-12">
                <p className="text-red-500 mb-4">{error}</p>
                <button
                  onClick={() => handleSearch(currentQuery)}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                >
                  다시 시도
                </button>
              </div>
            ) : data?.results.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-500 mb-2">검색 결과가 없습니다</p>
                <p className="text-sm text-gray-400">
                  다른 검색어나 필터를 시도해보세요
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                {data?.results.map((product) => (
                  <ProductCard
                    key={product.product_id}
                    product={product}
                    showSelect
                    isSelected={selectedIds.includes(product.product_id)}
                    onToggle={toggleProduct}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {selectedIds.length > 0 && (
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-[0_-4px_20px_rgba(0,0,0,0.1)]">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  {selectedProducts.slice(0, 5).map((product) => (
                    <div key={product.product_id} className="relative">
                      <div className="relative w-14 h-14 rounded-lg overflow-hidden border border-gray-200">
                        <Image
                          src={product.image_url}
                          alt={product.name_ko ?? product.name}
                          fill
                          sizes="56px"
                          className="object-cover"
                        />
                      </div>
                      <button
                        onClick={() => removeProduct(product.product_id)}
                        className="absolute -top-2 -right-2 w-5 h-5 bg-gray-800 text-white rounded-full text-xs flex items-center justify-center hover:bg-gray-700"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                  {selectedIds.length > 5 && (
                    <span className="text-sm text-gray-500">
                      +{selectedIds.length - 5}
                    </span>
                  )}
                </div>
                <span className="text-sm text-gray-600">
                  {selectedIds.length}개 선택됨
                </span>
              </div>

              <button
                onClick={() => setIsModalOpen(true)}
                className="px-8 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-semibold rounded-xl hover:from-indigo-700 hover:to-purple-700 transition-all shadow-lg"
              >
                AI 코디 추천
              </button>
            </div>
          </div>
        </div>
      )}

      <AIRecommendModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        selectedProducts={selectedProducts}
        userQuery={currentQuery}
      />

      <Footer />
    </main>
  );
}

export default function ResultsPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center">
          <div className="animate-spin w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full" />
        </div>
      }
    >
      <ResultsContent />
    </Suspense>
  );
}
