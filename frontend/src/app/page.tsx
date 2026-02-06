import Footer from "@/components/layout/Footer";
import Navbar from "@/components/layout/Navbar";
import SearchBar from "@/components/SearchBar";

const POPULAR_STYLES = [
  "캐주얼",
  "미니멀",
  "스트릿",
  "레트로",
  "페미닌",
  "모던",
  "빈티지",
];

export default function HomePage() {
  return (
    <main className="min-h-screen bg-white">
      <Navbar />

      <section className="relative bg-gradient-to-r from-indigo-500 to-purple-600 text-white">
        <div className="max-w-7xl mx-auto px-4 py-20 text-center">
          <h2 className="text-4xl font-bold mb-4">
            AI가 찾아주는 나만의 스타일
          </h2>
          <p className="text-lg text-indigo-100 mb-8">
            이미지와 텍스트로 원하는 스타일을 검색하세요
          </p>
          <SearchBar />
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 py-12">
        <h3 className="text-lg font-bold text-gray-900 mb-6">
          인기 스타일
        </h3>
        <div className="flex gap-3 overflow-x-auto pb-4">
          {POPULAR_STYLES.map((style) => (
            <a
              key={style}
              href={`/results?q=${encodeURIComponent(style)}`}
              className="flex-shrink-0 px-6 py-3 bg-gray-100 rounded-full text-gray-700 hover:bg-indigo-100 hover:text-indigo-700 transition-colors"
            >
              {style}
            </a>
          ))}
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-bold text-gray-900">검색 가이드</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-6 bg-gray-50 rounded-xl">
            <div className="text-3xl mb-3">💬</div>
            <h4 className="font-semibold text-gray-900 mb-2">텍스트 검색</h4>
            <p className="text-sm text-gray-600">
              &quot;힙한 오버핏 셔츠&quot;처럼 원하는 스타일을 자연스럽게 설명해보세요
            </p>
          </div>
          <div className="p-6 bg-gray-50 rounded-xl">
            <div className="text-3xl mb-3">📷</div>
            <h4 className="font-semibold text-gray-900 mb-2">이미지 검색</h4>
            <p className="text-sm text-gray-600">
              마음에 드는 옷 사진을 업로드하면 비슷한 스타일을 찾아드려요
            </p>
          </div>
          <div className="p-6 bg-gray-50 rounded-xl">
            <div className="text-3xl mb-3">✨</div>
            <h4 className="font-semibold text-gray-900 mb-2">AI 추천</h4>
            <p className="text-sm text-gray-600">
              선택한 상품을 기반으로 AI 스타일리스트가 코디를 추천해드려요
            </p>
          </div>
        </div>
      </section>

      <Footer />
    </main>
  );
}
