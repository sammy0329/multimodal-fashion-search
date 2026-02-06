# Frontend Architecture

## 기술 스택

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **상태 관리**:
  - 서버 상태: React Query (TanStack Query)
  - 클라이언트 상태: Zustand
- **인증**: Supabase Auth
- **배포**: Vercel (배포 후 URL 확인)

---

## 디렉토리 구조

```
frontend/
├── src/
│   ├── app/                    # App Router 페이지
│   │   ├── page.tsx            # 메인 (검색)
│   │   ├── results/
│   │   │   └── page.tsx        # 검색 결과
│   │   ├── layout.tsx          # 루트 레이아웃
│   │   └── globals.css         # 글로벌 스타일
│   │
│   ├── components/             # 재사용 컴포넌트
│   │   ├── common/             # 공통 UI
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Modal.tsx
│   │   │   └── Loading.tsx
│   │   ├── search/             # 검색 관련
│   │   │   ├── SearchBar.tsx
│   │   │   ├── ImageUpload.tsx
│   │   │   └── FilterPanel.tsx
│   │   ├── product/            # 상품 관련
│   │   │   ├── ProductGrid.tsx
│   │   │   ├── ProductCard.tsx
│   │   │   └── SelectedProducts.tsx
│   │   └── recommend/          # AI 추천 관련
│   │       ├── AIRecommend.tsx
│   │       ├── AIComment.tsx
│   │       └── MatchingItems.tsx
│   │
│   ├── hooks/                  # 커스텀 훅
│   │   ├── useSearch.ts        # 검색 API
│   │   ├── useRecommend.ts     # 추천 API (SSE)
│   │   └── useSelectedProducts.ts  # 선택 상태
│   │
│   ├── lib/                    # 유틸리티
│   │   ├── api.ts              # FastAPI 호출
│   │   ├── supabase.ts         # Supabase 클라이언트
│   │   └── utils.ts            # 헬퍼 함수
│   │
│   ├── stores/                 # Zustand 스토어
│   │   └── useProductStore.ts  # 선택된 상품 상태
│   │
│   └── types/                  # 타입 정의
│       └── index.ts
│
├── public/                     # 정적 파일
├── next.config.js
├── tailwind.config.js
├── tsconfig.json
└── package.json
```

---

## 페이지 구성

| 경로 | 파일 | 설명 |
|------|------|------|
| `/` | `app/page.tsx` | 메인 검색 화면 |
| `/results` | `app/results/page.tsx` | 검색 결과 + AI 추천 |

---

## 데이터 흐름

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Search    │────▶│   FastAPI   │────▶│   Results   │
│  (query/    │     │  /search    │     │   (상품     │
│   image)    │     │             │     │    그리드)  │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                                               ▼ 상품 선택
                                        ┌─────────────┐
                                        │  Selected   │
                                        │  Products   │
                                        │  (Zustand)  │
                                        └─────────────┘
                                               │
                                               ▼ AI 추천 클릭
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│     AI      │◀────│   FastAPI   │◀────│  Recommend  │
│  Comment    │ SSE │ /recommend  │     │   Modal     │
│ (streaming) │     │  ?stream    │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
```

---

## 주요 컴포넌트

### SearchBar
- 이미지 업로드 (드래그 앤 드롭)
- 텍스트 입력
- 검색 버튼

### ProductCard
- 상품 이미지
- 이름, 가격, 브랜드
- 선택 체크박스
- 호버 효과

### AIRecommend
- 모달 또는 슬라이드 패널
- 스트리밍 코멘트 (타이핑 효과)
- 매칭 상품 카드 or 스타일 태그

---

## 상태 관리

### 서버 상태 (React Query)

```typescript
// 검색 결과
const { data, isLoading } = useQuery({
  queryKey: ['search', query, image],
  queryFn: () => searchProducts({ query, image })
});

// 추천 (SSE는 별도 처리)
```

### 클라이언트 상태 (Zustand)

```typescript
// 선택된 상품
interface ProductStore {
  selectedIds: string[];
  toggle: (id: string) => void;
  clear: () => void;
}
```

---

## API 연동

### 검색

```typescript
// lib/api.ts
export async function searchProducts(params: SearchRequest): Promise<SearchResponse> {
  const res = await fetch(`${API_URL}/api/v1/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  return res.json();
}
```

### 추천 (SSE)

```typescript
// hooks/useRecommend.ts
export function useRecommend() {
  const [comment, setComment] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);

  const recommend = async (productIds: string[], userQuery?: string) => {
    setIsStreaming(true);
    setComment('');

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
      // SSE 파싱 후 comment 업데이트
      const event = parseSSE(chunk);
      if (event.event === 'delta') {
        setComment(prev => prev + event.data);
      }
    }

    setIsStreaming(false);
  };

  return { comment, isStreaming, recommend };
}
```
