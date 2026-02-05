# Style Matcher

> 이미지와 자연어를 결합한 멀티모달 AI 패션 검색 서비스.
> 사진 한 장 또는 자연어 설명으로 원하는 스타일의 옷을 찾아주고, AI 스타일리스트가 추천 이유를 설명한다.

---

## 기술 스택

- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS → **Vercel** 배포
- **Backend (AI API)**: Python 3.11+, FastAPI, Uvicorn → **Railway** 배포
- **AI/ML**: OpenAI CLIP (ViT-B/32), LLM (Claude / GPT-4o)
- **Vector DB**: Pinecone (512차원 임베딩)
- **DB + Auth**: Supabase (PostgreSQL + Auth + Realtime)
- **Cache**: Redis (검색 결과 캐싱)
- **CI/CD**: GitHub Actions

---

## 아키텍처 개요

```
[사용자]
   │
   ▼
[Next.js - Vercel]  ← 프론트엔드 + BFF (가벼운 API)
   │
   ├──→ [Supabase]         ← Auth, 상품 메타데이터 (PostgreSQL)
   │
   └──→ [FastAPI - Railway] ← AI 전용 서버 (무거운 처리)
           │
           ├──→ [CLIP 모델]    ← 이미지/텍스트 임베딩
           ├──→ [Pinecone]     ← 벡터 유사도 검색
           └──→ [LLM API]      ← 추천 코멘트 생성
```

### 역할 분리

| 레이어 | 담당 | 이유 |
|--------|------|------|
| **Next.js (Vercel)** | UI, 라우팅, Supabase 직접 호출 | 빠른 배포, SSR/SSG |
| **FastAPI (Railway)** | CLIP 임베딩, 벡터 검색, LLM 호출 | Python 전용 ML 라이브러리 필수 |
| **Supabase** | PostgreSQL, Auth, 실시간 구독 | DB + 인증 통합 관리 |
| **Pinecone** | 벡터 저장/검색 | 관리형 벡터 DB |

---

## 디렉토리 구조

```
style-matcher/
├── frontend/                    # Next.js (Vercel 배포)
│   ├── src/
│   │   ├── app/                 # App Router 페이지
│   │   │   ├── page.tsx         # 메인 (검색 화면)
│   │   │   ├── results/
│   │   │   │   └── page.tsx     # 검색 결과
│   │   │   └── layout.tsx
│   │   ├── components/
│   │   │   ├── SearchBar.tsx    # 이미지 업로드 + 텍스트 입력
│   │   │   ├── ProductCard.tsx  # 상품 카드
│   │   │   ├── FilterPanel.tsx  # 가격/브랜드/카테고리 필터
│   │   │   └── AIComment.tsx    # AI 추천 코멘트 (스트리밍)
│   │   ├── hooks/
│   │   │   └── useSearch.ts     # 검색 API 호출 훅
│   │   ├── lib/
│   │   │   ├── supabase.ts      # Supabase 클라이언트
│   │   │   └── api.ts           # FastAPI 호출 래퍼
│   │   └── types/
│   │       └── index.ts         # 공통 타입 정의
│   ├── package.json
│   └── next.config.js
│
├── backend/                     # FastAPI (Railway 배포)
│   ├── app/
│   │   ├── main.py              # FastAPI 엔트리포인트
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── search.py    # /search 엔드포인트
│   │   │       └── recommend.py # /recommend 엔드포인트
│   │   ├── services/
│   │   │   ├── embedding.py     # CLIP 임베딩 처리
│   │   │   ├── search.py        # Pinecone 벡터 검색
│   │   │   ├── recommend.py     # LLM 추천 코멘트 생성
│   │   │   └── cache.py         # Redis 캐싱
│   │   ├── models/
│   │   │   └── schemas.py       # Pydantic 요청/응답 스키마
│   │   ├── core/
│   │   │   ├── config.py        # 환경변수 설정
│   │   │   └── dependencies.py  # DI 의존성
│   │   └── utils/
│   │       └── image.py         # 이미지 전처리 유틸리티
│   ├── scripts/
│   │   └── seed_data.py         # 데이터셋 임베딩 배치 처리
│   ├── tests/
│   │   ├── test_search.py
│   │   ├── test_recommend.py
│   │   └── test_embedding.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── docker-compose.yml           # 로컬 개발 환경
├── CLAUDE.md                    # 이 파일
└── PRD.md
```

---

## 개발 명령어

```bash
# Frontend
cd frontend
npm install
npm run dev              # http://localhost:3000

# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 테스트
cd backend
pytest                   # 전체 테스트
pytest --cov=app         # 커버리지 포함

# Docker (로컬 전체 실행)
docker-compose up -d

# 배포
# Frontend: Vercel에 Git 연동 (자동 배포)
# Backend: Railway에 Git 연동 (자동 배포)
```

---

## API 엔드포인트

### FastAPI (AI 서버)

| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/v1/search` | 멀티모달 검색 (이미지/텍스트/복합) |
| POST | `/api/v1/recommend` | AI 추천 코멘트 생성 (스트리밍) |

### Supabase (직접 호출)

| 기능 | Supabase 서비스 | 설명 |
|------|-----------------|------|
| 상품 메타데이터 조회 | Database (PostgreSQL) | product_id로 상세 정보 |
| 사용자 인증 | Auth | Google 소셜 로그인 |
| 실시간 업데이트 | Realtime | 재고 상태 변경 등 |

---

## 코딩 컨벤션

### Python (Backend)
- 포맷터: Black (line-length=88)
- 린터: Ruff
- 타입 힌트 필수 (모든 함수 인자/리턴)
- Pydantic v2로 요청/응답 스키마 정의
- 비동기 우선 (async/await)
- 환경변수: pydantic-settings로 관리, 하드코딩 금지

### TypeScript (Frontend)
- 컴포넌트: PascalCase (예: ProductCard.tsx)
- 함수/변수: camelCase
- 타입: interface 우선
- 스타일: Tailwind CSS
- 상태 관리: React Query (서버 상태) + Zustand (클라이언트 상태)

### 공통
- 커밋 메시지: Conventional Commits (feat:, fix:, docs:, test:, refactor:)
- 브랜치: feature/기능명, fix/버그명
- PR 시 테스트 커버리지 80% 이상

---

## 환경변수

### Backend (.env)
```env
# AI
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# Pinecone
PINECONE_API_KEY=
PINECONE_INDEX=style-matcher

# Supabase
SUPABASE_URL=
SUPABASE_SERVICE_KEY=

# Redis
REDIS_URL=redis://localhost:6379

# App
APP_ENV=development
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 데이터 전략

### MVP 데이터: AI Hub 공공데이터 (한국어 라벨 포함)

| 데이터셋 | 출처 | 내용 | 활용 단계 |
|---------|------|------|----------|
| **K-Fashion 이미지** | AI Hub (dataSetSn=51) | 한국 패션 이미지 + 카테고리/속성 라벨링 | MVP 메인 |
| **패션상품 및 착용 영상** | AI Hub (dataSetSn=78) | 스튜디오 촬영 전신 + 상품 이미지 | 검색 정확도 향상 |

### 데이터 전처리 파이프라인

```
AI Hub 다운로드 → 이미지 리사이즈 (224x224) → CLIP 임베딩 → Pinecone 적재
       ↓
라벨/메타데이터 파싱 (JSON) → Supabase (PostgreSQL) 적재
```

### 한국어 검색 보완 전략

```
사용자 입력: "힙한 오버핏 셔츠"
       ↓
1. CLIP 텍스트 임베딩 → Pinecone 벡터 검색 (시각적 유사도)
2. 한국어 라벨 메타데이터 필터링 (카테고리, 스타일 태그)
3. 두 결과 결합 → 최종 랭킹
```

---

## 데이터베이스 스키마

### Supabase (PostgreSQL) - products 테이블

```sql
CREATE TABLE products (
    product_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    name_ko VARCHAR(255),
    price INTEGER NOT NULL,
    brand VARCHAR(100),
    category VARCHAR(50),
    sub_category VARCHAR(50),
    style_tags TEXT[],
    color VARCHAR(50),
    image_url TEXT NOT NULL,
    description TEXT,
    material VARCHAR(100),
    season VARCHAR(20),
    data_source VARCHAR(50),
    is_soldout BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_brand ON products(brand);
CREATE INDEX idx_products_price ON products(price);
```

### Pinecone - 벡터 구조

```json
{
  "id": "product_{product_id}",
  "values": [512차원 CLIP 임베딩],
  "metadata": {
    "category": "상의",
    "sub_category": "셔츠",
    "style_tags": ["오버핏", "캐주얼"],
    "color": "화이트",
    "season": "여름",
    "price": 45000,
    "brand": "brand_a",
    "data_source": "k-fashion",
    "is_soldout": false
  }
}
```

---

## 마일스톤

### M1: 기반 구축
- [x] FastAPI 보일러플레이트 세팅
- [x] Next.js 프로젝트 초기화
- [x] Supabase 프로젝트 생성 + 테이블 생성
- [x] Pinecone 인덱스 생성
- [x] CLIP 모델 로컬 환경 구성
- [x] Docker Compose 환경 구성

### M2: 데이터 파이프라인
- [x] AI Hub 데이터 신청 및 다운로드
- [x] 한국어 라벨/메타데이터 파싱
- [x] CLIP 임베딩 배치 스크립트
- [x] 메타데이터 Supabase 적재
- [x] 벡터 + 메타데이터 Pinecone 적재
- [x] 데이터 파이프라인 오케스트레이터 (seed_data.py CLI)

### M3: 검색 API
- [ ] /search 엔드포인트 구현
- [ ] 이미지 임베딩 처리
- [ ] 텍스트 임베딩 처리
- [ ] 하이브리드 필터링

### M4: 추천 코멘트
- [ ] /recommend 엔드포인트 구현
- [ ] LLM 프롬프트 최적화
- [ ] 스트리밍 응답 구현

### M5: 프론트엔드
- [ ] 검색 입력 UI (이미지 업로드 + 텍스트)
- [ ] 검색 결과 카드 UI
- [ ] AI 코멘트 스트리밍 표시
- [ ] 필터 UI
- [ ] Supabase Auth 연동 (Google 로그인)

### M6: 배포
- [ ] Backend → Railway 배포
- [ ] Frontend → Vercel 배포
- [ ] GitHub Actions CI/CD 파이프라인
- [ ] 환경변수 세팅

---

## 성능 목표

| 지표 | 목표 |
|------|------|
| 검색 정확도 (Precision@5) | 80% 이상 |
| 검색 응답 속도 | 1.5초 이내 (LLM 제외) |
| 시스템 가용성 | 99% |

---

## 현재 상태

**Phase**: M2 완료
**작업 중**: M3 검색 API
