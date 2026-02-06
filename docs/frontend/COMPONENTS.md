# Frontend Components

## 컴포넌트 목록

| 컴포넌트 | 경로 | 설명 |
|---------|------|------|
| SearchBar | `components/search/SearchBar.tsx` | 이미지 + 텍스트 검색 입력 |
| ImageUpload | `components/search/ImageUpload.tsx` | 드래그앤드롭 이미지 업로드 |
| FilterPanel | `components/search/FilterPanel.tsx` | 카테고리/가격/색상 필터 |
| ProductGrid | `components/product/ProductGrid.tsx` | 상품 카드 그리드 레이아웃 |
| ProductCard | `components/product/ProductCard.tsx` | 개별 상품 카드 |
| SelectedProducts | `components/product/SelectedProducts.tsx` | 선택된 상품 하단 바 |
| AIRecommend | `components/recommend/AIRecommend.tsx` | AI 추천 모달 컨테이너 |
| AIComment | `components/recommend/AIComment.tsx` | 스트리밍 코멘트 표시 |
| MatchingItems | `components/recommend/MatchingItems.tsx` | 매칭 상품/스타일 태그 |

---

## 컴포넌트 상세

### SearchBar

```typescript
interface SearchBarProps {
  onSearch: (query: string, image?: File) => void;
  isLoading?: boolean;
}
```

**기능:**
- 텍스트 입력 필드
- 이미지 업로드 영역 (ImageUpload 포함)
- 검색 버튼
- 로딩 상태 표시

---

### ImageUpload

```typescript
interface ImageUploadProps {
  onImageSelect: (file: File) => void;
  preview?: string;
  onClear: () => void;
}
```

**기능:**
- 클릭하여 파일 선택
- 드래그 앤 드롭
- 이미지 미리보기
- 삭제 버튼

---

### ProductCard

```typescript
interface ProductCardProps {
  product: ProductResult;
  isSelected: boolean;
  onToggle: (id: string) => void;
}
```

**기능:**
- 상품 이미지 (aspect-ratio 3:4)
- 이름, 가격, 브랜드 표시
- 선택 체크박스
- 호버 시 확대 효과
- 선택 시 테두리 강조

---

### SelectedProducts

```typescript
interface SelectedProductsProps {
  products: ProductResult[];
  onRemove: (id: string) => void;
  onRecommend: () => void;
  maxCount?: number; // 기본 5
}
```

**기능:**
- 화면 하단 고정 바
- 선택된 상품 썸네일 표시
- 개별 삭제 버튼
- AI 코디 추천 버튼
- 최대 선택 개수 표시

---

### AIRecommend

```typescript
interface AIRecommendProps {
  isOpen: boolean;
  onClose: () => void;
  productIds: string[];
  userQuery?: string;
}
```

**기능:**
- 모달 또는 슬라이드 오버
- AIComment + MatchingItems 포함
- 닫기 버튼
- 로딩/에러 상태 처리

---

### AIComment

```typescript
interface AICommentProps {
  comment: string;
  isStreaming: boolean;
}
```

**기능:**
- 스트리밍 텍스트 표시
- 타이핑 커서 애니메이션
- 완료 시 커서 숨김

---

### MatchingItems

```typescript
interface MatchingItemsProps {
  products: ProductResult[];  // DB에서 찾은 매칭 상품
  styleTags: string[];        // 매칭 상품 없을 때 스타일 태그
}
```

**기능:**
- 매칭 상품이 있으면: 상품 카드 표시
- 없으면: 스타일 태그 표시 (예: 👖 와이드 데님)

---

## 공통 컴포넌트

### Button

```typescript
interface ButtonProps {
  variant: 'primary' | 'secondary' | 'ghost';
  size: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  disabled?: boolean;
  children: React.ReactNode;
  onClick?: () => void;
}
```

### Modal

```typescript
interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
}
```

### Loading

```typescript
interface LoadingProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
}
```
