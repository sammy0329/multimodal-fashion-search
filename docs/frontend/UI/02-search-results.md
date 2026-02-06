# 검색 결과 화면 (쇼핑몰 스타일)

## 와이어프레임

```
┌─────────────────────────────────────────────────────────────────┐
│  STYLE MATCHER     [상의] [하의] [아우터]          🔍   👤      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 🔍 오버핏 캐주얼 셔츠                           [검색]  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  "오버핏 캐주얼 셔츠" 검색결과 48개                             │
│                                                                 │
├──────────────┬──────────────────────────────────────────────────┤
│              │                                                  │
│   필터       │  [최신순 ▼]                                     │
│              │                                                  │
│  ☐ 상의     │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐           │
│  ☐ 하의     │  │ ☑️   │ │      │ │ ☑️   │ │      │           │
│  ☐ 아우터   │  │      │ │      │ │      │ │      │           │
│              │  │ img  │ │ img  │ │ img  │ │ img  │           │
│  ─────────   │  │      │ │      │ │      │ │      │           │
│              │  │브랜드│ │브랜드│ │브랜드│ │브랜드│           │
│  가격        │  │상품명│ │상품명│ │상품명│ │상품명│           │
│  ○ 전체     │  │45,000│ │38,000│ │52,000│ │41,000│           │
│  ○ ~3만원   │  └──────┘ └──────┘ └──────┘ └──────┘           │
│  ○ 3~5만원  │                                                  │
│  ○ 5~10만원 │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐           │
│  ○ 10만원~  │  │      │ │      │ │      │ │      │           │
│              │  │ img  │ │ img  │ │ img  │ │ img  │           │
│  ─────────   │  │ ...  │ │ ...  │ │ ...  │ │ ...  │           │
│              │  └──────┘ └──────┘ └──────┘ └──────┘           │
│  색상        │                                                  │
│  ⚪⚫🔵🔴    │                                                  │
│              │                                                  │
├──────────────┴──────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────┐ ┌─────┐                                               │
│  │ img │ │ img │  2개 선택됨           [ ✨ AI 코디 추천 ]     │
│  │  ×  │ │  ×  │                                               │
│  └─────┘ └─────┘                                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tailwind 구현

```tsx
// app/results/page.tsx
export default function ResultsPage() {
  return (
    <main className="min-h-screen bg-white">
      {/* 네비게이션 (메인과 동일) */}
      <nav className="sticky top-0 z-50 bg-white border-b border-gray-200">
        {/* ... */}
      </nav>

      {/* 검색 바 */}
      <div className="border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex gap-2 max-w-2xl">
            <input
              type="text"
              defaultValue="오버핏 캐주얼 셔츠"
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <button className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">
              검색
            </button>
          </div>
        </div>
      </div>

      {/* 검색 결과 헤더 */}
      <div className="max-w-7xl mx-auto px-4 py-4">
        <p className="text-gray-600">
          "<span className="font-medium text-gray-900">오버핏 캐주얼 셔츠</span>"
          검색결과 <span className="font-medium text-gray-900">48</span>개
        </p>
      </div>

      {/* 메인 콘텐츠 */}
      <div className="max-w-7xl mx-auto px-4 pb-32">
        <div className="flex gap-8">
          {/* 사이드바 필터 */}
          <aside className="hidden lg:block w-56 flex-shrink-0">
            <div className="sticky top-24 space-y-8">
              {/* 카테고리 */}
              <div>
                <h4 className="font-medium text-gray-900 mb-4">카테고리</h4>
                <div className="space-y-2">
                  {['상의', '하의', '아우터', '원피스'].map((cat) => (
                    <label key={cat} className="flex items-center gap-2 cursor-pointer">
                      <input type="checkbox" className="rounded text-indigo-600" />
                      <span className="text-gray-600">{cat}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* 가격 */}
              <div>
                <h4 className="font-medium text-gray-900 mb-4">가격</h4>
                <div className="space-y-2">
                  {['전체', '~3만원', '3~5만원', '5~10만원', '10만원~'].map((price) => (
                    <label key={price} className="flex items-center gap-2 cursor-pointer">
                      <input type="radio" name="price" className="text-indigo-600" />
                      <span className="text-gray-600">{price}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* 색상 */}
              <div>
                <h4 className="font-medium text-gray-900 mb-4">색상</h4>
                <div className="flex flex-wrap gap-2">
                  {[
                    { name: '화이트', color: 'bg-white border' },
                    { name: '블랙', color: 'bg-black' },
                    { name: '네이비', color: 'bg-blue-900' },
                    { name: '베이지', color: 'bg-amber-100' },
                    { name: '그레이', color: 'bg-gray-400' },
                  ].map(({ name, color }) => (
                    <button
                      key={name}
                      title={name}
                      className={`w-8 h-8 rounded-full ${color} hover:ring-2 hover:ring-indigo-400 hover:ring-offset-2`}
                    />
                  ))}
                </div>
              </div>
            </div>
          </aside>

          {/* 상품 그리드 */}
          <div className="flex-1">
            {/* 정렬 */}
            <div className="flex justify-end mb-4">
              <select className="px-3 py-2 border border-gray-300 rounded-lg bg-white text-sm">
                <option>최신순</option>
                <option>인기순</option>
                <option>가격 낮은순</option>
                <option>가격 높은순</option>
              </select>
            </div>

            {/* 그리드 */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
              {products.map((product) => (
                <ProductCard
                  key={product.product_id}
                  product={product}
                  showSelect={true}
                  isSelected={selectedIds.includes(product.product_id)}
                  onToggle={toggleProduct}
                />
              ))}
            </div>

            {/* 페이지네이션 */}
            <div className="flex justify-center mt-12 gap-2">
              {[1, 2, 3, 4, 5].map((page) => (
                <button
                  key={page}
                  className={`w-10 h-10 rounded-lg ${
                    page === 1
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {page}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 선택된 상품 바 (하단 고정) */}
      {selectedIds.length > 0 && (
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-[0_-4px_20px_rgba(0,0,0,0.1)]">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                {/* 선택된 상품 썸네일 */}
                <div className="flex items-center gap-2">
                  {selectedProducts.map((product) => (
                    <div key={product.product_id} className="relative">
                      <img
                        src={product.image_url}
                        alt={product.name}
                        className="w-14 h-14 object-cover rounded-lg border border-gray-200"
                      />
                      <button
                        onClick={() => removeProduct(product.product_id)}
                        className="absolute -top-2 -right-2 w-5 h-5 bg-gray-800 text-white rounded-full text-xs flex items-center justify-center hover:bg-gray-700"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
                <span className="text-sm text-gray-600">
                  {selectedIds.length}개 선택됨
                </span>
              </div>

              {/* AI 추천 버튼 */}
              <button
                onClick={openRecommendModal}
                className="px-8 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-semibold rounded-xl hover:from-indigo-700 hover:to-purple-700 transition-all shadow-lg"
              >
                ✨ AI 코디 추천
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
```

---

## 모바일 필터 (드로어)

```tsx
// components/search/MobileFilter.tsx
export function MobileFilter({ isOpen, onClose }) {
  return (
    <div className={`
      fixed inset-0 z-50 lg:hidden
      ${isOpen ? 'visible' : 'invisible'}
    `}>
      {/* 백드롭 */}
      <div
        className={`absolute inset-0 bg-black/50 transition-opacity ${isOpen ? 'opacity-100' : 'opacity-0'}`}
        onClick={onClose}
      />

      {/* 드로어 */}
      <div className={`
        absolute left-0 top-0 bottom-0 w-80 bg-white
        transform transition-transform
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="p-4 border-b border-gray-200 flex justify-between items-center">
          <h3 className="font-bold text-gray-900">필터</h3>
          <button onClick={onClose} className="text-gray-500">×</button>
        </div>

        <div className="p-4 overflow-y-auto">
          {/* 필터 내용 (사이드바와 동일) */}
        </div>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t bg-white">
          <button className="w-full py-3 bg-indigo-600 text-white rounded-lg">
            필터 적용
          </button>
        </div>
      </div>
    </div>
  );
}
```

---

## 반응형 레이아웃

| 화면 | 사이드바 | 상품 그리드 |
|------|---------|-----------|
| Mobile | 숨김 (필터 버튼) | 2열 |
| Tablet | 숨김 (필터 버튼) | 3열 |
| Desktop | 표시 (w-56) | 4열 |
