import FilterPanel from "@/components/FilterPanel";

export default function ResultsPage() {
  return (
    <div className="min-h-screen p-8">
      <header className="max-w-6xl mx-auto mb-8">
        <h1 className="text-2xl font-bold">검색 결과</h1>
      </header>
      <div className="max-w-6xl mx-auto flex gap-8">
        <div className="w-64 shrink-0">
          <FilterPanel />
        </div>
        <main className="flex-1">
          <p className="text-gray-400 text-sm">
            M5에서 검색 결과가 여기에 표시됩니다
          </p>
        </main>
      </div>
    </div>
  );
}
