"use client";

import { useCallback, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface SSEEvent {
  event: "delta" | "done" | "error";
  data: string;
}

interface UseRecommendReturn {
  comment: string;
  isStreaming: boolean;
  error: string | null;
  recommend: (productIds: string[], userQuery?: string) => Promise<void>;
  reset: () => void;
}

export function useRecommend(): UseRecommendReturn {
  const [comment, setComment] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const recommend = useCallback(
    async (productIds: string[], userQuery?: string) => {
      setIsStreaming(true);
      setComment("");
      setError(null);

      try {
        const response = await fetch(
          `${API_URL}/api/v1/recommend?stream=true`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              product_ids: productIds,
              user_query: userQuery,
            }),
          }
        );

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail ?? `HTTP ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error("스트림을 읽을 수 없습니다");
        }

        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() ?? "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;

            try {
              const event: SSEEvent = JSON.parse(line.slice(6));

              switch (event.event) {
                case "delta":
                  setComment((prev) => prev + event.data);
                  break;
                case "done":
                  setIsStreaming(false);
                  break;
                case "error":
                  setError(event.data);
                  setIsStreaming(false);
                  break;
              }
            } catch {
              // JSON 파싱 실패 시 무시
            }
          }
        }
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "추천을 가져오는 중 오류 발생";
        setError(message);
        setIsStreaming(false);
      }
    },
    []
  );

  const reset = useCallback(() => {
    setComment("");
    setError(null);
    setIsStreaming(false);
  }, []);

  return { comment, isStreaming, error, recommend, reset };
}
