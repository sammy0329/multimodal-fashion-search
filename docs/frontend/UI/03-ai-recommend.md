# AI 코디 추천 모달 (쇼핑몰 스타일)

## 와이어프레임

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                                                    [×]   │   │
│  │                                                          │   │
│  │  ✨ AI 스타일리스트 추천                                 │   │
│  │                                                          │   │
│  │  ───────────────────────────────────────────────────────│   │
│  │                                                          │   │
│  │  선택하신 아이템                                         │   │
│  │  ┌──────────┐ ┌──────────┐                              │   │
│  │  │          │ │          │                              │   │
│  │  │   img    │ │   img    │                              │   │
│  │  │          │ │          │                              │   │
│  │  │ 브랜드A  │ │ 브랜드B  │                              │   │
│  │  │ 셔츠명   │ │ 셔츠명   │                              │   │
│  │  │ ₩45,000  │ │ ₩38,000  │                              │   │
│  │  └──────────┘ └──────────┘                              │   │
│  │                                                          │   │
│  │  ───────────────────────────────────────────────────────│   │
│  │                                                          │   │
│  │  ┌────────────────────────────────────────────────────┐ │   │
│  │  │ 💬                                                 │ │   │
│  │  │                                                    │ │   │
│  │  │ 화이트 오버핏 셔츠를 선택하셨네요!                 │ │   │
│  │  │                                                    │ │   │
│  │  │ 이런 스타일은 편안하면서도 트렌디한 무드를         │ │   │
│  │  │ 연출할 수 있어요. 와이드 데님이나 슬랙스와         │ │   │
│  │  │ 매치하면 완벽한 캐주얼룩 완성!▌                    │ │   │
│  │  │                                                    │ │   │
│  │  └────────────────────────────────────────────────────┘ │   │
│  │                                                          │   │
│  │  ───────────────────────────────────────────────────────│   │
│  │                                                          │   │
│  │  💡 함께 매치하면 좋아요                                │   │
│  │                                                          │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐                │   │
│  │  │          │ │          │ │    👖    │                │   │
│  │  │   img    │ │   img    │ │          │                │   │
│  │  │          │ │          │ │  슬랙스  │ ← 없으면 태그  │   │
│  │  │ 와이드   │ │ 카키     │ │  (추천)  │                │   │
│  │  │ 데님     │ │ 치노     │ │          │                │   │
│  │  │ ₩38,000  │ │ ₩45,000  │ │          │                │   │
│  │  │ [담기]   │ │ [담기]   │ │          │                │   │
│  │  └──────────┘ └──────────┘ └──────────┘                │   │
│  │                                                          │   │
│  │         [ 🔄 다른 추천 ]    [ 쇼핑 계속하기 ]           │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tailwind 구현

```tsx
// components/recommend/AIRecommendModal.tsx
interface AIRecommendModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedProducts: ProductResult[];
  userQuery?: string;
}

export function AIRecommendModal({
  isOpen,
  onClose,
  selectedProducts,
  userQuery
}: AIRecommendModalProps) {
  const {
    comment,
    isStreaming,
    matchingProducts,
    styleTags,
    recommend
  } = useRecommend();

  useEffect(() => {
    if (isOpen && selectedProducts.length > 0) {
      recommend(selectedProducts.map(p => p.product_id), userQuery);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* 백드롭 */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* 모달 */}
      <div className="relative w-full max-w-2xl max-h-[85vh] bg-white rounded-2xl shadow-2xl overflow-hidden animate-fadeIn">
        {/* 헤더 */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h2 className="text-lg font-bold text-gray-900">
            ✨ AI 스타일리스트 추천
          </h2>
          <button
            onClick={onClose}
            className="w-10 h-10 flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition-colors"
          >
            <span className="text-xl">×</span>
          </button>
        </div>

        {/* 스크롤 영역 */}
        <div className="overflow-y-auto max-h-[calc(85vh-140px)] p-6">
          {/* 선택한 아이템 */}
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-500 mb-3">
              선택하신 아이템
            </h3>
            <div className="flex gap-4 overflow-x-auto pb-2">
              {selectedProducts.map((product) => (
                <div key={product.product_id} className="flex-shrink-0 w-32">
                  <div className="aspect-[3/4] rounded-lg overflow-hidden bg-gray-100 mb-2">
                    <img
                      src={product.image_url}
                      alt={product.name}
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <p className="text-xs text-gray-500">{product.brand}</p>
                  <p className="text-sm text-gray-900 truncate">
                    {product.name_ko || product.name}
                  </p>
                  <p className="text-sm font-bold text-gray-900">
                    ₩{product.price.toLocaleString()}
                  </p>
                </div>
              ))}
            </div>
          </div>

          <hr className="border-gray-100 mb-6" />

          {/* AI 코멘트 */}
          <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl p-5 mb-6">
            <div className="flex gap-3">
              <span className="text-2xl">💬</span>
              <div className="flex-1">
                {isStreaming && !comment ? (
                  <div className="flex items-center gap-2 text-gray-500">
                    <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" />
                    <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                    <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                    <span className="ml-2">분석 중...</span>
                  </div>
                ) : (
                  <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                    {comment}
                    {isStreaming && (
                      <span className="inline-block w-0.5 h-5 bg-indigo-600 ml-0.5 animate-pulse" />
                    )}
                  </p>
                )}
              </div>
            </div>
          </div>

          <hr className="border-gray-100 mb-6" />

          {/* 매칭 아이템 */}
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-4">
              💡 함께 매치하면 좋아요
            </h3>
            <div className="grid grid-cols-3 gap-4">
              {/* DB에서 찾은 상품 */}
              {matchingProducts.map((product) => (
                <div key={product.product_id} className="group">
                  <div className="aspect-[3/4] rounded-lg overflow-hidden bg-gray-100 mb-2 relative">
                    <img
                      src={product.image_url}
                      alt={product.name}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                    />
                    {/* 호버 시 담기 버튼 */}
                    <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center">
                      <button className="opacity-0 group-hover:opacity-100 px-4 py-2 bg-white rounded-lg text-sm font-medium text-gray-900 transition-opacity">
                        담기
                      </button>
                    </div>
                  </div>
                  <p className="text-xs text-gray-500">{product.brand}</p>
                  <p className="text-sm text-gray-900 truncate">
                    {product.name_ko || product.name}
                  </p>
                  <p className="text-sm font-bold text-gray-900">
                    ₩{product.price.toLocaleString()}
                  </p>
                </div>
              ))}

              {/* 스타일 태그 (상품 없을 때) */}
              {styleTags.map((tag, i) => (
                <div
                  key={i}
                  className="aspect-[3/4] rounded-lg bg-gray-50 border-2 border-dashed border-gray-200 flex flex-col items-center justify-center"
                >
                  <span className="text-4xl mb-2">{getStyleEmoji(tag)}</span>
                  <span className="text-sm text-gray-600 font-medium">{tag}</span>
                  <span className="text-xs text-gray-400">(추천 스타일)</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 푸터 버튼 */}
        <div className="px-6 py-4 border-t border-gray-100 bg-gray-50 flex gap-3">
          <button
            onClick={() => recommend(selectedProducts.map(p => p.product_id), userQuery)}
            disabled={isStreaming}
            className="flex-1 py-3 border border-gray-300 rounded-xl text-gray-700 font-medium hover:bg-white disabled:opacity-50 transition-colors"
          >
            🔄 다른 추천
          </button>
          <button
            onClick={onClose}
            className="flex-1 py-3 bg-indigo-600 text-white font-medium rounded-xl hover:bg-indigo-700 transition-colors"
          >
            쇼핑 계속하기
          </button>
        </div>
      </div>
    </div>
  );
}

function getStyleEmoji(style: string): string {
  const map: Record<string, string> = {
    '데님': '👖',
    '슬랙스': '👔',
    '스니커즈': '👟',
    '로퍼': '🥿',
    '가방': '👜',
    '모자': '🧢',
    '벨트': '🪢',
  };
  return map[style] || '✨';
}
```

---

## 애니메이션

```tsx
// tailwind.config.js에 추가
module.exports = {
  theme: {
    extend: {
      animation: {
        'fadeIn': 'fadeIn 0.2s ease-out',
        'slideUp': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
}
```

---

## useRecommend 훅

```tsx
// hooks/useRecommend.ts
interface RecommendResult {
  comment: string;
  isStreaming: boolean;
  matchingProducts: ProductResult[];
  styleTags: string[];
  recommend: (productIds: string[], userQuery?: string) => Promise<void>;
}

export function useRecommend(): RecommendResult {
  const [comment, setComment] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [matchingProducts, setMatchingProducts] = useState<ProductResult[]>([]);
  const [styleTags, setStyleTags] = useState<string[]>([]);

  const recommend = async (productIds: string[], userQuery?: string) => {
    setIsStreaming(true);
    setComment('');
    setMatchingProducts([]);
    setStyleTags([]);

    try {
      const res = await fetch(`${API_URL}/api/v1/recommend?stream=true`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_ids: productIds, user_query: userQuery }),
      });

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader!.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;

          const event = JSON.parse(line.slice(6));

          switch (event.event) {
            case 'delta':
              setComment(prev => prev + event.data);
              break;
            case 'matching':
              setMatchingProducts(prev => [...prev, event.data]);
              break;
            case 'style_tag':
              setStyleTags(prev => [...prev, event.data]);
              break;
            case 'done':
              setIsStreaming(false);
              break;
          }
        }
      }
    } catch (error) {
      console.error('추천 실패:', error);
      setIsStreaming(false);
    }
  };

  return { comment, isStreaming, matchingProducts, styleTags, recommend };
}
```

---

## 상태별 UI

| 상태 | 표시 |
|------|------|
| 초기 로딩 | 점 3개 애니메이션 + "분석 중..." |
| 스트리밍 중 | 텍스트 + 깜빡이는 커서 |
| 완료 | 전체 코멘트 + 매칭 아이템 |
| 에러 | 에러 메시지 + 재시도 버튼 |
