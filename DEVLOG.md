# DEVLOG

## 2026-02-05 (M3 검색 API)

### 완료한 작업
- **M3 검색 API 전체 구현 완료** (6개 커밋, `feature/m3-search-api` 브랜치)
- 커밋 1: `services/embedding.py` - CLIP ViT-B/32 이미지/텍스트 임베딩 + 하이브리드 가중 평균 결합
- 커밋 2: `services/cache.py` - Redis 비동기 캐싱 (JSON 직렬화, TTL 3600초, MD5 키)
- 커밋 3: `services/search.py` - Pinecone 벡터 검색 + Supabase 상품 정보 보강
- 커밋 4: `main.py`, `dependencies.py` - FastAPI lifespan 싱글톤 초기화 + DI 함수 3개
- 커밋 5: `api/v1/search.py` - /search 엔드포인트 (텍스트/이미지/하이브리드 멀티모달 검색)
- 커밋 6: `CLAUDE.md` M3 마일스톤 체크리스트 완료 처리
- **테스트**: 43개 통과, 1개 스킵 (CLIP 미설치 환경)
- **커버리지**: services + API 85% (cache 100%, search 100%, api/v1/search 98%)
- **코드 리뷰**: CRITICAL 3개, HIGH 5개 이슈 발견 후 전부 수정 완료

### 변경된 파일
- **생성 (4개)**:
  - `backend/tests/test_services/__init__.py` - 테스트 패키지
  - `backend/tests/test_services/test_embedding_service.py` - EmbeddingService 유닛 테스트 (11개, torch 미설치 시 스킵)
  - `backend/tests/test_services/test_cache_service.py` - CacheService 유닛 테스트 (10개)
  - `backend/tests/test_services/test_search_service.py` - SearchService 유닛 테스트 (18개)
- **수정 (9개)**:
  - `backend/app/services/embedding.py` - 스텁 → CLIP 임베딩 구현 (lazy import)
  - `backend/app/services/cache.py` - 스텁 → Redis 비동기 캐싱 구현
  - `backend/app/services/search.py` - 스텁 → Pinecone 검색 + Supabase 보강 구현
  - `backend/app/main.py` - lifespan 싱글톤 초기화 + 글로벌 예외 핸들러
  - `backend/app/core/dependencies.py` - DI 함수 3개 추가
  - `backend/app/api/v1/search.py` - 501 스텁 → 멀티모달 검색 구현
  - `backend/app/models/schemas.py` - image max_length 14MB, query_type Literal 타입
  - `backend/requirements.txt` - `redis` → `redis[asyncio]`
  - `backend/tests/test_search.py` - 스텁 테스트 → 통합 테스트 13개로 확장
  - `CLAUDE.md` - M3 체크리스트 완료, 현재 상태 M4로 업데이트

### 트러블슈팅
- **clip/torch 모듈 임포트 에러**: `app/services/embedding.py`에서 top-level `import clip`/`import torch`가 있으면 테스트 실행 시 ModuleNotFoundError → `__init__` 내부 lazy import로 변경, `self._clip`/`self._torch`에 저장하여 해결
- **redis 모듈 미설치**: `.venv/bin/pip install "redis[asyncio]==5.2.1"`로 해결
- **conftest.py 임포트 체인**: `tests/conftest.py → app.main → app.services.embedding → clip` 순서로 임포트 체인이 걸려 테스트 자체가 로드 불가 → lazy import로 체인 끊어 해결

### 기술적 결정사항
- **CLIP 모듈 lazy import**: `clip`과 `torch`를 모듈 레벨이 아닌 `__init__` 내부에서 임포트. 테스트/다른 모듈에서 heavy dependency 없이 모듈 사용 가능
- **하이브리드 가중치 60:40**: 패션 도메인은 시각 정보가 더 중요 → 이미지 임베딩 60%, 텍스트 40% 가중 평균
- **단일 Pinecone 쿼리**: 하이브리드 검색 시 이미지/텍스트 각각 쿼리 후 병합하는 대신, 가중 평균 벡터 1개로 단일 쿼리 (성능 + 단순성)
- **SHA-256 캐시 키**: Python `hash()`는 프로세스 재시작 시 랜덤화 → `hashlib.sha256` 사용으로 결정적 캐시 키 보장
- **asyncio.gather 병렬 임베딩**: 하이브리드 검색 시 이미지/텍스트 임베딩을 순차가 아닌 병렬 실행으로 레이턴시 감소
- **Supabase select 컬럼 제한**: `select("*")` 대신 ProductResult에 필요한 10개 컬럼만 조회하여 대역폭 절약
- **글로벌 예외 핸들러**: Pinecone/Supabase 장애 시 500 스택트레이스 노출 방지
- **CORS 제한**: `allow_methods=["*"]` → `["GET", "POST", "OPTIONS"]`, `allow_headers=["*"]` → `["Content-Type", "Authorization"]`

### PR
- PR #3 생성 및 `develop` 머지 완료

### 머지 후 코드 리뷰 결과
- **전체 평가**: Approve with Warnings (아키텍처/테스트 양호, HIGH 3건 수정 필요)

#### HIGH (수정 필요)
1. **`assert` → 명시적 검증** (`api/v1/search.py:133-144`): Python `-O` 플래그 시 assert 제거되어 NoneType 에러 가능 → `HTTPException`으로 교체
2. **서비스 장애 처리 추가** (`api/v1/search.py:68-123`): Pinecone/Supabase 장애 시 503 반환 + 로깅 필요 (현재 글로벌 핸들러에만 의존)
3. **필수 API 키 fail-fast** (`core/config.py`): `pinecone_api_key`, `supabase_url`, `supabase_service_key` 빈 문자열 기본값 → 시작 시 누락되면 즉시 에러

#### MEDIUM (개선 권장)
- 외부 서비스 호출에 타임아웃 없음 (`asyncio.wait_for`)
- 캐시 키 MD5 → SHA-256 통일
- SHA-256 해시 16자 절단 → 32자로 확대
- Supabase 미조회 상품 fallback 이름이 카테고리명 → 혼란 가능
- 서비스 장애 시나리오 테스트 부재
- `requirements.txt` httpx 중복
- `combine_embeddings` 가중치 합계 검증 없음
- pinecone 버전 `>=5.0.0` → `>=5.0.0,<6.0.0` 권장

### HIGH 수정 완료 (`fix/m3-review` 브랜치, PR #4 → develop 머지)
- `assert` → `HTTPException(400)` + 한국어 에러 메시지 (3곳)
- Pinecone/Supabase 장애 시 `try/except` → 503 반환 + `exc_info` 로깅
- `@model_validator`로 프로덕션 환경 필수 API 키 검증 (개발 환경은 통과)
- 서비스 장애 시나리오 테스트 2건 추가 (총 45 passed)

### 다음 할 일
- M4 추천 코멘트 구현
  1. `/api/v1/recommend` 엔드포인트
  2. LLM 프롬프트 최적화 (Claude/GPT-4o)
  3. SSE 스트리밍 응답 구현

---

## 2026-02-05 (M2 데이터 파이프라인)

### 완료한 작업
- **M2 데이터 파이프라인 전체 구현 완료** (6개 커밋, `feature/m2-data-pipeline` 브랜치)
- 커밋 1: `pipeline/constants.py`, `pipeline/schemas.py` - 의류 타입, 가격 범위, 브랜드 매핑, Pydantic v2 스키마 (AIHubLabel, ProductRecord, PineconeRecord 등)
- 커밋 2: `pipeline/parser.py`, `pipeline/name_generator.py` - AI Hub JSON 라벨 파싱, 영문/한국어 상품명 생성, 가격/브랜드 시드 기반 랜덤 생성
- 커밋 3: `pipeline/embedder.py` - CLIP ViT-B/32 배치 임베딩 + `.npy` 캐시, 디바이스 자동 감지 (CUDA > MPS > CPU)
- 커밋 4: `pipeline/loader_supabase.py`, `pipeline/loader_pinecone.py` - Supabase products upsert + Storage 이미지 업로드, Pinecone 벡터 upsert
- 커밋 5: `scripts/seed_data.py` CLI 오케스트레이터 - `--dry-run`, `--skip-embedding`, `--skip-upload` 지원
- 커밋 6: `CLAUDE.md` M2 마일스톤 체크리스트 완료 처리
- **테스트**: 78개 통과, 3개 스킵 (CLIP 미설치 통합 테스트)
- **주요 모듈 커버리지**: constants 100%, schemas 100%, name_generator 100%, parser 98%, loader_pinecone 100%, seed_data 90%

### 변경된 파일
- **생성 (14개)**:
  - `backend/app/pipeline/constants.py` - GARMENT_TYPES, PRICE_RANGE, BRAND_MAP, 로마자 변환 매핑
  - `backend/app/pipeline/schemas.py` - StyleLabel, GarmentLabel, AIHubLabel, ProductRecord, PineconeRecord
  - `backend/app/pipeline/parser.py` - parse_label_file(), extract_valid_garments(), scan_data_directory()
  - `backend/app/pipeline/name_generator.py` - generate_product_name(), generate_price(), build_product_record()
  - `backend/app/pipeline/embedder.py` - CLIPEmbedder 클래스
  - `backend/app/pipeline/loader_supabase.py` - SupabaseLoader 클래스
  - `backend/app/pipeline/loader_pinecone.py` - PineconeLoader 클래스
  - `backend/scripts/__init__.py` - 모듈 인식용
  - `backend/tests/fixtures/sample_label_single.json` - 로맨틱 원피스 테스트 데이터
  - `backend/tests/fixtures/sample_label_multi.json` - 레트로 아우터+상의+하의 테스트 데이터
  - `backend/tests/fixtures/sample_label_resort.json` - 리조트 상의 테스트 데이터
  - `backend/tests/test_pipeline/` - test_schemas, test_parser, test_name_generator, test_embedder, test_loader_supabase, test_loader_pinecone, test_seed_data (7개 테스트 파일)
- **수정 (3개)**:
  - `backend/scripts/seed_data.py` - 스텁 → CLI 오케스트레이터로 완전 교체
  - `backend/app/core/config.py` - clip_batch_size, clip_device, supabase_storage_bucket 설정 추가
  - `backend/requirements.txt` - `pinecone-client` → `pinecone>=5.0.0`, numpy/tqdm 추가
  - `CLAUDE.md` - M2 체크리스트 `[x]` 처리, 현재 상태 업데이트

### 트러블슈팅
- **`_clip_available()` NameError**: `@pytest.mark.skipif` 데코레이터에서 참조하는 함수가 파일 하단에 정의되어 있어 NameError 발생 → 함수 정의를 클래스 위로 이동하여 해결
- **Mock 패칭 실패 (모듈 해석)**: `patch("app.pipeline.loader_supabase.create_client")`가 `module has no attribute` 에러 → `import app.pipeline.loader_supabase as loader_module` + `patch.object(loader_module, "create_client", mock)` 패턴으로 변경하여 해결
- **pinecone 패키지 충돌**: `pinecone-client` v6이 "패키지명이 `pinecone`으로 변경됨" 에러 발생 → `pip uninstall pinecone-client && pip install pinecone==5.4.2`로 해결, `requirements.txt`도 `pinecone>=5.0.0`으로 수정
- **venv 미활성화**: anaconda base Python이 사용되어 supabase/pinecone 패키지 미설치 에러 → `.venv/bin/python`으로 직접 실행하여 해결

### 기술적 결정사항
- **GarmentLabel 한국어 alias**: Pydantic `Field(alias="카테고리")` 패턴으로 AI Hub JSON 한국어 키를 직접 파싱, 별도 변환 레이어 불필요
- **빈 슬롯 판별**: `GarmentLabel.is_empty()` → `category is None`으로 판별. AI Hub JSON에서 빈 의류 슬롯은 `[{}]`로 표현됨
- **시드 기반 재현성**: `seed = image_id * 100 + hash(suffix) % 100`으로 동일 입력에 항상 같은 가격/브랜드 생성
- **Lazy import**: CLIPEmbedder 내부에서 `import clip`을 `__init__`에서 수행하여 CLIP 미설치 환경에서도 다른 모듈 import 가능
- **model_copy() 사용**: seed_data.py에서 ProductRecord에 image_url 설정 시 mutation 대신 `model_copy(update=...)` 사용 (immutability 원칙)

### 다음 할 일
- PR 생성: `feature/m2-data-pipeline` → `develop`
- M3 검색 API 구현
  1. `/api/v1/search` 엔드포인트 (이미지/텍스트/복합 검색)
  2. CLIP 텍스트 임베딩 → Pinecone 벡터 검색
  3. 한국어 메타데이터 필터링 (카테고리, 스타일 태그)
  4. 하이브리드 결과 결합 + 랭킹

---

## 2026-02-05 (M1 기반 구축 + M2 계획)

### 완료한 작업
- **M1 기반 구축 전체 완료** (6개 체크리스트 모두 달성)
- Git 브랜치 전략 수립: `main → develop → feature/m1-foundation`
- FastAPI 백엔드 보일러플레이트: 헬스체크, 스텁 API(/search, /recommend), 서비스 인터페이스, 이미지 전처리 유틸리티
- Next.js 14 프론트엔드 초기화: App Router, TypeScript, Tailwind, 스텁 컴포넌트 4개, Supabase/React Query/Zustand 설정
- 외부 서비스 설정 스크립트: Supabase DDL(products 테이블 + RLS), Pinecone 인덱스 생성, CLIP ViT-B/32 검증
- Docker Compose 로컬 개발 환경: Backend + Frontend + Redis
- GitHub 리포지토리 연결 및 PR #1 생성 → develop 머지 완료
- CLAUDE.md M1 마일스톤 체크리스트 업데이트
- **M2 데이터 파이프라인 계획 수립 완료** (Plan Mode)
  - sample-data 디렉토리 분석: AI Hub K-Fashion 2,200개 이미지+라벨 확인
  - JSON 라벨 스키마 파악 (스타일/색상/카테고리/소재/디테일 등)
  - 파이프라인 아키텍처 설계: 모듈형 (parser → embedder → loader)

### 변경된 파일
- **생성 (63개)**:
  - `backend/app/` - FastAPI 앱 전체 구조 (main, api/v1, services, models, core, utils)
  - `backend/tests/` - pytest 테스트 4개 파일 (15 테스트, 커버리지 85%)
  - `backend/scripts/` - init_db.sql, init_pinecone.py, verify_clip.py, seed_data.py(스텁)
  - `backend/` - requirements.txt, pyproject.toml, Dockerfile, .env.example, .gitignore, .dockerignore
  - `frontend/` - Next.js 14 프로젝트 전체 (create-next-app + 커스텀 컴포넌트/훅/타입/lib)
  - `docker-compose.yml`, `.gitignore` (루트)
- **수정**:
  - `CLAUDE.md` - M1 체크리스트 `[x]` 처리

### 트러블슈팅
- **git push 충돌**: 리모트에 Initial commit이 이미 있어서 push 실패 → `git rebase origin/main`으로 로컬 main을 리모트 위에 rebase 후 develop, feature 브랜치도 순서대로 rebase하여 해결

### 기술적 결정사항
- **CLIP 비용 0원 확인**: OpenAI 오픈소스 모델로 로컬 실행, API 과금 없음 (ViT-B/32 사용)
- **멀티 아이템 전략**: 이미지 1장에 의류 여러 개 → 아이템 단위로 product row 분리 (`kf_{id}_{type}`)
- **가격/브랜드 생성**: AI Hub에 없는 필드는 카테고리별 현실적 범위 내 랜덤 생성 + 가상 브랜드 12개 (스타일별 4개)
- **이미지 URL**: Supabase Storage 업로드 방식 채택 (`--skip-upload` 플래그 지원)

### 다음 할 일
- M2 데이터 파이프라인 구현 (계획 승인 후)
  1. `pipeline/constants.py`, `pipeline/schemas.py` - 스키마 및 상수 정의
  2. `pipeline/parser.py`, `pipeline/name_generator.py` - JSON 파서 + 상품명 생성
  3. `pipeline/embedder.py` - CLIP 배치 임베딩 + 캐시
  4. `pipeline/loader_supabase.py`, `pipeline/loader_pinecone.py` - 데이터 적재
  5. `scripts/seed_data.py` - 오케스트레이터 (CLI)
  6. 테스트 작성 (80%+ 커버리지)
