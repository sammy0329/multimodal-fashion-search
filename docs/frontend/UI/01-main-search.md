# 메인 화면 (쇼핑몰 스타일)

## 와이어프레임

```
┌─────────────────────────────────────────────────────────────────┐
│  STYLE MATCHER     [상의] [하의] [아우터]          🔍   👤      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                                                         │   │
│  │                    히어로 배너                          │   │
│  │         "AI가 찾아주는 나만의 스타일"                   │   │
│  │                                                         │   │
│  │     ┌─────────────────────────────────────────┐        │   │
│  │     │ 🔍 원하는 스타일을 검색하세요...        │        │   │
│  │     └─────────────────────────────────────────┘        │   │
│  │               📷 이미지로 검색하기                      │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  🔥 인기 스타일                                                 │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐       │
│  │ 캐주얼 │ │ 미니멀 │ │ 스트릿 │ │ 레트로 │ │ 페미닌 │       │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘       │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  ✨ 추천 상품                                        더보기 →  │
│                                                                 │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐       │
│  │  img   │ │  img   │ │  img   │ │  img   │ │  img   │       │
│  │ 상품명 │ │ 상품명 │ │ 상품명 │ │ 상품명 │ │ 상품명 │       │
│  │₩45,000 │ │₩38,000 │ │₩52,000 │ │₩41,000 │ │₩35,000 │       │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘       │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  👕 상의 베스트                                      더보기 →  │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐                  │
│  │  ...   │ │  ...   │ │  ...   │ │  ...   │                  │
│  └────────┘ └────────┘ └────────┘ └────────┘                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tailwind 구현

```tsx
// app/page.tsx
export default function HomePage() {
  return (
    <main className="min-h-screen bg-white">
      {/* 네비게이션 */}
      <nav className="sticky top-0 z-50 bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            {/* 로고 */}
            <h1 className="text-xl font-bold text-gray-900">
              STYLE MATCHER
            </h1>

            {/* 카테고리 */}
            <div className="hidden md:flex items-center gap-8">
              <a href="#" className="text-gray-600 hover:text-gray-900">상의</a>
              <a href="#" className="text-gray-600 hover:text-gray-900">하의</a>
              <a href="#" className="text-gray-600 hover:text-gray-900">아우터</a>
              <a href="#" className="text-gray-600 hover:text-gray-900">원피스</a>
            </div>

            {/* 아이콘 */}
            <div className="flex items-center gap-4">
              <button className="p-2 hover:bg-gray-100 rounded-full">
                🔍
              </button>
              <button className="p-2 hover:bg-gray-100 rounded-full">
                👤
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* 히어로 배너 */}
      <section className="relative bg-gradient-to-r from-indigo-500 to-purple-600 text-white">
        <div className="max-w-7xl mx-auto px-4 py-20 text-center">
          <h2 className="text-4xl font-bold mb-4">
            AI가 찾아주는 나만의 스타일
          </h2>
          <p className="text-lg text-indigo-100 mb-8">
            이미지와 텍스트로 원하는 스타일을 검색하세요
          </p>

          {/* 검색 바 */}
          <div className="max-w-2xl mx-auto">
            <div className="flex bg-white rounded-full overflow-hidden shadow-lg">
              <input
                type="text"
                placeholder="원하는 스타일을 검색하세요..."
                className="flex-1 px-6 py-4 text-gray-900 focus:outline-none"
              />
              <button className="px-6 py-4 bg-indigo-600 text-white font-medium hover:bg-indigo-700">
                검색
              </button>
            </div>
            <button className="mt-4 text-indigo-100 hover:text-white underline">
              📷 이미지로 검색하기
            </button>
          </div>
        </div>
      </section>

      {/* 인기 스타일 */}
      <section className="max-w-7xl mx-auto px-4 py-12">
        <h3 className="text-lg font-bold text-gray-900 mb-6">
          🔥 인기 스타일
        </h3>
        <div className="flex gap-3 overflow-x-auto pb-4">
          {['캐주얼', '미니멀', '스트릿', '레트로', '페미닌', '모던', '빈티지'].map((style) => (
            <button
              key={style}
              className="flex-shrink-0 px-6 py-3 bg-gray-100 rounded-full text-gray-700 hover:bg-indigo-100 hover:text-indigo-700 transition-colors"
            >
              {style}
            </button>
          ))}
        </div>
      </section>

      {/* 추천 상품 */}
      <section className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-bold text-gray-900">✨ 추천 상품</h3>
          <a href="#" className="text-sm text-gray-500 hover:text-gray-900">
            더보기 →
          </a>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {products.slice(0, 5).map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      </section>

      {/* 카테고리별 베스트 */}
      <section className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-bold text-gray-900">👕 상의 베스트</h3>
          <a href="#" className="text-sm text-gray-500 hover:text-gray-900">
            더보기 →
          </a>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {tops.slice(0, 4).map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      </section>

      {/* 푸터 */}
      <footer className="bg-gray-100 mt-16">
        <div className="max-w-7xl mx-auto px-4 py-12">
          <div className="text-center text-gray-500 text-sm">
            © 2025 Style Matcher. AI 기반 패션 검색 서비스
          </div>
        </div>
      </footer>
    </main>
  );
}
```

---

## 상품 카드 (쇼핑몰 스타일)

```tsx
// components/product/ProductCard.tsx
interface ProductCardProps {
  product: ProductResult;
  showSelect?: boolean;
  isSelected?: boolean;
  onToggle?: (id: string) => void;
}

export function ProductCard({
  product,
  showSelect = false,
  isSelected = false,
  onToggle
}: ProductCardProps) {
  return (
    <div className="group cursor-pointer">
      {/* 이미지 */}
      <div className="relative aspect-[3/4] bg-gray-100 rounded-lg overflow-hidden mb-3">
        <img
          src={product.image_url}
          alt={product.name}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
        />

        {/* 호버 오버레이 */}
        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors" />

        {/* 선택 체크박스 (검색 결과 페이지) */}
        {showSelect && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onToggle?.(product.product_id);
            }}
            className={`
              absolute top-3 right-3 w-7 h-7 rounded-full border-2
              flex items-center justify-center transition-all
              ${isSelected
                ? 'bg-indigo-600 border-indigo-600 text-white'
                : 'bg-white/90 border-gray-300 hover:border-indigo-400'
              }
            `}
          >
            {isSelected && '✓'}
          </button>
        )}

        {/* 뱃지 (선택적) */}
        {product.score >= 0.9 && (
          <span className="absolute top-3 left-3 px-2 py-1 bg-red-500 text-white text-xs font-medium rounded">
            BEST
          </span>
        )}
      </div>

      {/* 정보 */}
      <div>
        <p className="text-xs text-gray-500 mb-1">{product.brand}</p>
        <p className="text-sm text-gray-900 mb-1 line-clamp-2">
          {product.name_ko || product.name}
        </p>
        <p className="text-sm font-bold text-gray-900">
          ₩{product.price.toLocaleString()}
        </p>
      </div>
    </div>
  );
}
```

---

## 색상 팔레트

```css
/* 메인 컬러 */
--primary: #4F46E5;     /* indigo-600 */
--primary-hover: #4338CA; /* indigo-700 */

/* 배경 */
--bg-primary: #FFFFFF;
--bg-secondary: #F9FAFB; /* gray-50 */

/* 텍스트 */
--text-primary: #111827;  /* gray-900 */
--text-secondary: #6B7280; /* gray-500 */

/* 보더 */
--border: #E5E7EB; /* gray-200 */
```

---

## 반응형 브레이크포인트

| 화면 | 상품 그리드 | 네비게이션 |
|------|-----------|-----------|
| Mobile (<640px) | 2열 | 햄버거 메뉴 |
| Tablet (640-1024px) | 3~4열 | 축소된 카테고리 |
| Desktop (>1024px) | 5열 | 전체 카테고리 |
