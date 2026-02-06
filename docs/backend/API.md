# Backend API Reference

## Base URL

- Local: `http://localhost:8000`
- Production (API): `{RAILWAY_URL}` (배포 후 확인)
- Production (Frontend): `{VERCEL_URL}` (배포 후 확인)

---

## 헬스체크

### GET /health

서버 상태 확인

**Response**
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

---

## 검색 API

### POST /api/v1/search

멀티모달 패션 상품 검색

**Request Body**
```json
{
  "query": "오버핏 캐주얼 셔츠",
  "image": "data:image/jpeg;base64,...",
  "category": "상의",
  "sub_category": "셔츠",
  "brand": null,
  "min_price": 30000,
  "max_price": 80000,
  "color": "화이트",
  "season": "여름",
  "limit": 20
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| query | string | △ | 텍스트 검색어 (query 또는 image 중 하나 필수) |
| image | string | △ | Base64 인코딩 이미지 (최대 ~10MB) |
| category | string | X | 카테고리 필터 |
| sub_category | string | X | 서브카테고리 필터 |
| brand | string | X | 브랜드 필터 |
| min_price | int | X | 최소 가격 |
| max_price | int | X | 최대 가격 |
| color | string | X | 색상 필터 |
| season | string | X | 시즌 필터 |
| limit | int | X | 결과 수 (기본 20, 최대 100) |

**Response (200)**
```json
{
  "results": [
    {
      "product_id": "p001",
      "name": "Relaxed Fit Oxford Shirt",
      "name_ko": "릴렉스핏 옥스포드 셔츠",
      "price": 45000,
      "brand": "브랜드A",
      "category": "상의",
      "sub_category": "셔츠",
      "style_tags": ["캐주얼", "오버핏"],
      "color": "화이트",
      "image_url": "https://...",
      "score": 0.92
    }
  ],
  "total": 48,
  "query_type": "hybrid"
}
```

**Error Responses**

| 코드 | 설명 |
|------|------|
| 400 | query와 image 모두 없음 |
| 503 | 검색 서비스 장애 |

---

## 추천 API

### POST /api/v1/recommend

AI 스타일리스트 코디 추천

**Request Body**
```json
{
  "product_ids": ["p001", "p003"],
  "user_query": "오버핏 셔츠"
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| product_ids | string[] | O | 선택한 상품 ID (1~10개) |
| user_query | string | X | 원래 검색어 |

**Query Parameters**

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| stream | bool | false | SSE 스트리밍 모드 |

---

### 비스트리밍 응답 (stream=false)

**Response (200)**
```json
{
  "comment": "화이트 오버핏 셔츠를 선택하셨네요! 이런 스타일은 편안하면서도 트렌디한 무드를 연출할 수 있어요. 와이드 데님이나 슬랙스와 매치하면 완벽한 캐주얼룩이 완성됩니다.",
  "product_ids": ["p001", "p003"],
  "matching_products": [
    {
      "product_id": "p023",
      "name_ko": "와이드 데님 팬츠",
      "price": 38000,
      "image_url": "https://...",
      "match_reason": "와이드핏 데님"
    }
  ],
  "style_tags": ["슬랙스", "스니커즈"]
}
```

| 필드 | 설명 |
|------|------|
| comment | AI 생성 코멘트 |
| product_ids | 입력 상품 ID |
| matching_products | DB에서 찾은 매칭 상품 |
| style_tags | DB에 없는 추천 스타일 (텍스트만) |

---

### 스트리밍 응답 (stream=true)

**Content-Type**: `text/event-stream`

**이벤트 형식**
```
data: {"event": "delta", "data": "화이트 오버핏"}

data: {"event": "delta", "data": " 셔츠를 선택하셨네요!"}

data: {"event": "matching", "data": {"product_id": "p023", ...}}

data: {"event": "style_tag", "data": "슬랙스"}

data: {"event": "done", "data": ""}
```

| 이벤트 | 설명 |
|--------|------|
| delta | 코멘트 텍스트 청크 |
| matching | 매칭 상품 정보 |
| style_tag | 추천 스타일 태그 |
| done | 스트리밍 완료 |
| error | 에러 발생 |

---

## 에러 응답 형식

```json
{
  "detail": "에러 메시지"
}
```

| 코드 | 설명 |
|------|------|
| 400 | 잘못된 요청 (입력 검증 실패) |
| 422 | Pydantic 검증 실패 |
| 500 | 서버 내부 오류 |
| 503 | 외부 서비스 장애 |

---

## 사용 예시

### cURL - 텍스트 검색

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "오버핏 셔츠", "limit": 10}'
```

### cURL - AI 추천 (스트리밍)

```bash
curl -N -X POST "http://localhost:8000/api/v1/recommend?stream=true" \
  -H "Content-Type: application/json" \
  -d '{"product_ids": ["p001"], "user_query": "오버핏 셔츠"}'
```

### JavaScript - SSE 처리

```javascript
const response = await fetch('/api/v1/recommend?stream=true', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ product_ids: ['p001'] })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const event = JSON.parse(line.slice(6));
      console.log(event);
    }
  }
}
```
