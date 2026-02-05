"use client";

import { useState } from "react";
import type { SearchFilters, SearchResponse } from "@/types";
import { apiFetch } from "@/lib/api";

interface UseSearchParams {
  query?: string;
  image?: string;
  filters?: SearchFilters;
  limit?: number;
}

interface UseSearchReturn {
  data: SearchResponse | null;
  isLoading: boolean;
  error: string | null;
  search: (params: UseSearchParams) => Promise<void>;
  reset: () => void;
}

export function useSearch(): UseSearchReturn {
  const [data, setData] = useState<SearchResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const search = async (params: UseSearchParams): Promise<void> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiFetch<SearchResponse>("/api/v1/search", {
        method: "POST",
        body: {
          query: params.query,
          image: params.image,
          ...params.filters,
          limit: params.limit ?? 20,
        },
      });
      setData(response);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "검색 중 오류가 발생했습니다";
      setError(message);
      setData(null);
    } finally {
      setIsLoading(false);
    }
  };

  const reset = () => {
    setData(null);
    setError(null);
    setIsLoading(false);
  };

  return { data, isLoading, error, search, reset };
}
