"use client";

import type { SearchFilters } from "@/types";

interface FilterPanelProps {
  filters: SearchFilters;
  onChange: (filters: SearchFilters) => void;
}

const CATEGORIES = ["상의", "하의", "아우터", "원피스"];
const PRICE_RANGES = [
  { label: "전체", min: undefined, max: undefined },
  { label: "~3만원", min: 0, max: 30000 },
  { label: "3~5만원", min: 30000, max: 50000 },
  { label: "5~10만원", min: 50000, max: 100000 },
  { label: "10만원~", min: 100000, max: undefined },
];
const COLORS = [
  { name: "화이트", value: "화이트", color: "bg-white border" },
  { name: "블랙", value: "블랙", color: "bg-black" },
  { name: "네이비", value: "네이비", color: "bg-blue-900" },
  { name: "베이지", value: "베이지", color: "bg-amber-100" },
  { name: "그레이", value: "그레이", color: "bg-gray-400" },
];

export default function FilterPanel({ filters, onChange }: FilterPanelProps) {
  const handleCategoryChange = (category: string) => {
    onChange({
      ...filters,
      category: filters.category === category ? undefined : category,
    });
  };

  const handlePriceChange = (min?: number, max?: number) => {
    onChange({
      ...filters,
      min_price: min,
      max_price: max,
    });
  };

  const handleColorChange = (color: string) => {
    onChange({
      ...filters,
      color: filters.color === color ? undefined : color,
    });
  };

  return (
    <aside className="w-full space-y-8">
      <div>
        <h4 className="font-medium text-gray-900 mb-4">카테고리</h4>
        <div className="space-y-2">
          {CATEGORIES.map((cat) => (
            <label
              key={cat}
              className="flex items-center gap-2 cursor-pointer"
            >
              <input
                type="checkbox"
                checked={filters.category === cat}
                onChange={() => handleCategoryChange(cat)}
                className="rounded text-indigo-600 focus:ring-indigo-500"
              />
              <span className="text-gray-600">{cat}</span>
            </label>
          ))}
        </div>
      </div>

      <div>
        <h4 className="font-medium text-gray-900 mb-4">가격</h4>
        <div className="space-y-2">
          {PRICE_RANGES.map((range) => (
            <label
              key={range.label}
              className="flex items-center gap-2 cursor-pointer"
            >
              <input
                type="radio"
                name="price"
                checked={
                  filters.min_price === range.min &&
                  filters.max_price === range.max
                }
                onChange={() => handlePriceChange(range.min, range.max)}
                className="text-indigo-600 focus:ring-indigo-500"
              />
              <span className="text-gray-600">{range.label}</span>
            </label>
          ))}
        </div>
      </div>

      <div>
        <h4 className="font-medium text-gray-900 mb-4">색상</h4>
        <div className="flex flex-wrap gap-2">
          {COLORS.map(({ name, value, color }) => (
            <button
              key={name}
              title={name}
              onClick={() => handleColorChange(value)}
              className={`w-8 h-8 rounded-full ${color} transition-all ${
                filters.color === value
                  ? "ring-2 ring-indigo-500 ring-offset-2"
                  : "hover:ring-2 hover:ring-indigo-400 hover:ring-offset-2"
              }`}
            />
          ))}
        </div>
      </div>

      {(filters.category || filters.min_price || filters.color) && (
        <button
          onClick={() =>
            onChange({
              category: undefined,
              min_price: undefined,
              max_price: undefined,
              color: undefined,
            })
          }
          className="text-sm text-indigo-600 hover:text-indigo-700"
        >
          필터 초기화
        </button>
      )}
    </aside>
  );
}
