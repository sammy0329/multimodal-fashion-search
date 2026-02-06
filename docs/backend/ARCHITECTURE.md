# Backend Architecture

## 기술 스택

- **Framework**: FastAPI
- **Language**: Python 3.11+
- **AI/ML**: OpenAI CLIP (ViT-B/32), GPT-4o-mini
- **Vector DB**: Pinecone (512차원)
- **Database**: Supabase (PostgreSQL)
- **Cache**: Redis
- **배포**: Railway (배포 후 URL 확인)

---

## 디렉토리 구조

```
backend/
├── app/
│   ├── main.py                 # FastAPI 엔트리포인트 + lifespan
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py     # 라우터 통합
│   │       ├── search.py       # /search 엔드포인트
│   │       └── recommend.py    # /recommend 엔드포인트
│   ├── services/
│   │   ├── embedding.py        # CLIP 임베딩
│   │   ├── search.py           # Pinecone + Supabase 검색
│   │   ├── cache.py            # Redis 캐싱
│   │   ├── llm.py              # OpenAI GPT 클라이언트
│   │   ├── prompt.py           # 프롬프트 템플릿
│   │   └── recommend.py        # 추천 로직
│   ├── models/
│   │   └── schemas.py          # Pydantic 스키마
│   ├── core/
│   │   ├── config.py           # 환경변수 설정
│   │   └── dependencies.py     # DI 의존성
│   └── utils/
│       └── image.py            # 이미지 전처리
├── tests/
│   ├── test_search.py
│   ├── test_recommend.py
│   └── test_services/
├── Dockerfile
└── requirements.txt
```

---

## 서비스 레이어

```
┌─────────────────────────────────────────────────────────────┐
│                         FastAPI                              │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │  /api/v1/search │  │ /api/v1/recommend│                   │
│  └────────┬────────┘  └────────┬────────┘                   │
│           │                    │                             │
├───────────┼────────────────────┼─────────────────────────────┤
│           ▼                    ▼                             │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │ EmbeddingService│  │ RecommendService│                   │
│  │   (CLIP)        │  │   (LLM + DB)    │                   │
│  └────────┬────────┘  └────────┬────────┘                   │
│           │                    │                             │
│  ┌────────▼────────┐  ┌────────▼────────┐                   │
│  │  SearchService  │  │   LLMService    │                   │
│  │ (Pinecone+Supa) │  │  (GPT-4o-mini)  │                   │
│  └────────┬────────┘  └─────────────────┘                   │
│           │                                                  │
│  ┌────────▼────────┐                                        │
│  │  CacheService   │                                        │
│  │    (Redis)      │                                        │
│  └─────────────────┘                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 싱글톤 초기화 (Lifespan)

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 초기화
    app.state.embedding_service = EmbeddingService()
    app.state.search_service = SearchService(pinecone, supabase)
    app.state.cache_service = CacheService(redis)
    app.state.llm_service = LLMService(openai_key)
    app.state.recommend_service = RecommendService(llm, supabase)

    yield

    # 종료 시 정리
    await app.state.cache_service.close()
```

---

## API 엔드포인트

### POST /api/v1/search

멀티모달 검색 (이미지/텍스트/하이브리드)

| 입력 | 타입 | 설명 |
|------|------|------|
| query | string? | 텍스트 검색어 |
| image | string? | Base64 이미지 |
| category | string? | 카테고리 필터 |
| min_price | int? | 최소 가격 |
| max_price | int? | 최대 가격 |
| limit | int | 결과 수 (기본 20) |

### POST /api/v1/recommend

AI 코디 추천

| 입력 | 타입 | 설명 |
|------|------|------|
| product_ids | string[] | 선택한 상품 ID (1~10개) |
| user_query | string? | 원래 검색어 |
| stream | bool | SSE 스트리밍 여부 |

---

## 추천 로직 흐름

```
1. product_ids로 상품 정보 조회 (Supabase)
      ↓
2. 프롬프트 구성
   - 시스템: AI 스타일리스트 역할
   - 사용자: 상품 정보 + 검색어
      ↓
3. LLM 호출 (GPT-4o-mini)
   - "이 상품에 어울리는 스타일은?"
   - 응답: "와이드 데님, 슬랙스..."
      ↓
4. 키워드 추출 → DB 검색
   - category != 선택상품.category
   - style_tags 매칭
      ↓
5. 응답 조합
   - 코멘트 텍스트
   - 매칭 상품 (있으면)
   - 스타일 태그 (없으면)
```

---

## 에러 처리

| 상황 | 코드 | 응답 |
|------|------|------|
| 입력 검증 실패 | 400 | 상세 에러 메시지 |
| 상품 없음 | 400 | "요청한 상품을 찾을 수 없습니다" |
| 서비스 장애 | 503 | "서비스 일시 장애" |
| 서버 오류 | 500 | "서버 내부 오류" |

---

## 환경변수

```env
# AI
OPENAI_API_KEY=

# Pinecone
PINECONE_API_KEY=
PINECONE_INDEX=style-matcher

# Supabase
SUPABASE_URL=
SUPABASE_SERVICE_KEY=

# Redis
REDIS_URL=redis://localhost:6379

# LLM
LLM_MODEL=gpt-4o-mini
LLM_MAX_TOKENS=1024
LLM_TEMPERATURE=0.3

# App
APP_ENV=development
```
