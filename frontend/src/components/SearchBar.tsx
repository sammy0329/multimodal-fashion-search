"use client";

export default function SearchBar() {
  return (
    <div className="w-full flex flex-col gap-4">
      <div className="flex gap-2">
        <input
          type="text"
          placeholder="원하는 스타일을 설명해주세요 (예: 힙한 오버핏 셔츠)"
          className="flex-1 rounded-lg border border-gray-300 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-black"
          disabled
        />
        <button
          className="rounded-lg bg-black px-6 py-3 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50"
          disabled
        >
          검색
        </button>
      </div>
      <p className="text-xs text-gray-400 text-center">
        M5에서 이미지 업로드 및 텍스트 검색 기능이 추가됩니다
      </p>
    </div>
  );
}
