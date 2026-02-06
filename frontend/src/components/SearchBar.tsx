"use client";

import { useRouter } from "next/navigation";
import { useCallback, useRef, useState } from "react";

interface SearchBarProps {
  defaultValue?: string;
  onSearch?: (query: string, imageBase64?: string) => void;
  variant?: "hero" | "compact";
}

const MAX_IMAGE_SIZE = 10 * 1024 * 1024; // 10MB

export default function SearchBar({
  defaultValue = "",
  onSearch,
  variant = "hero",
}: SearchBarProps) {
  const router = useRouter();
  const [query, setQuery] = useState(defaultValue);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [imageBase64, setImageBase64] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const processImage = useCallback((file: File) => {
    setError(null);

    if (!file.type.startsWith("image/")) {
      setError("이미지 파일만 업로드 가능합니다");
      return;
    }

    if (file.size > MAX_IMAGE_SIZE) {
      setError("이미지 크기는 10MB 이하여야 합니다");
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const result = e.target?.result as string;
      setImagePreview(result);
      const base64Data = result.split(",")[1];
      setImageBase64(base64Data);
    };
    reader.readAsDataURL(file);
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      processImage(file);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) {
      processImage(file);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!query.trim() && !imageBase64) {
      setError("검색어 또는 이미지를 입력해주세요");
      return;
    }

    if (onSearch) {
      onSearch(query, imageBase64 ?? undefined);
    } else {
      const params = new URLSearchParams();
      if (query.trim()) {
        params.set("q", query.trim());
      }
      if (imageBase64) {
        sessionStorage.setItem("searchImage", imageBase64);
        params.set("hasImage", "true");
      }
      router.push(`/results?${params.toString()}`);
    }
  };

  const removeImage = () => {
    setImagePreview(null);
    setImageBase64(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  if (variant === "compact") {
    return (
      <form onSubmit={handleSubmit} className="flex gap-2 max-w-2xl">
        <div className="flex-1 relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="원하는 스타일을 검색하세요..."
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          {imageBase64 && (
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs bg-indigo-100 text-indigo-700 px-2 py-1 rounded">
              이미지 포함
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          title="이미지 업로드"
        >
          <svg
            className="w-5 h-5 text-gray-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
        </button>
        <button
          type="submit"
          className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
        >
          검색
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileChange}
          className="hidden"
        />
      </form>
    );
  }

  return (
    <div className="max-w-2xl mx-auto w-full">
      <form onSubmit={handleSubmit}>
        <div className="flex bg-white rounded-full overflow-hidden shadow-lg">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="원하는 스타일을 검색하세요..."
            className="flex-1 px-6 py-4 text-gray-900 focus:outline-none"
          />
          <button
            type="submit"
            className="px-6 py-4 bg-indigo-600 text-white font-medium hover:bg-indigo-700 transition-colors"
          >
            검색
          </button>
        </div>
      </form>

      <button
        type="button"
        onClick={() => fileInputRef.current?.click()}
        className="mt-4 text-indigo-100 hover:text-white underline transition-colors"
      >
        <svg
          className="w-4 h-4 inline mr-1"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"
          />
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"
          />
        </svg>
        이미지로 검색하기
      </button>

      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        className="hidden"
      />

      {(imagePreview || isDragging) && (
        <div
          className={`mt-4 p-4 rounded-xl border-2 border-dashed transition-colors ${
            isDragging
              ? "border-white bg-white/20"
              : "border-white/50 bg-white/10"
          }`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
        >
          {imagePreview ? (
            <div className="relative inline-block">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={imagePreview}
                alt="업로드된 이미지"
                className="max-h-32 rounded-lg"
              />
              <button
                type="button"
                onClick={removeImage}
                className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 transition-colors"
              >
                ×
              </button>
            </div>
          ) : (
            <p className="text-white/80 text-sm">
              이미지를 여기에 드래그하세요
            </p>
          )}
        </div>
      )}

      {error && (
        <p className="mt-2 text-red-300 text-sm text-center">{error}</p>
      )}
    </div>
  );
}
