# Git Workflow

## 언어 규칙

- **커밋 메시지**: 한국어
- **코드 리뷰**: 설명은 한국어, 코드/기술 용어는 영어 그대로
- **PR 본문**: 한국어

---

## Commit Message Format

```
<type>: <한국어 설명>

<선택: 상세 내용>
```

### Types

| 타입     | 용도         | 예시                                             |
| -------- | ------------ | ------------------------------------------------ |
| feat     | 새 기능 추가 | feat: 멀티모달 검색 API 엔드포인트 추가          |
| fix      | 버그 수정    | fix: CLIP 임베딩 메모리 누수 수정                |
| refactor | 리팩토링     | refactor: search 서비스 비동기 처리 개선         |
| docs     | 문서 변경    | docs: CLAUDE.md 마일스톤 업데이트                |
| test     | 테스트       | test: 검색 API 유닛 테스트 추가                  |
| chore    | 설정/빌드    | chore: Docker Compose Redis 설정 추가            |
| perf     | 성능 개선    | perf: Pinecone 쿼리 배치 처리로 응답 속도 개선   |
| ci       | CI/CD        | ci: GitHub Actions 테스트 자동화 워크플로우 추가 |

### 커밋 규칙

- 제목은 50자 이내
- 본문은 선택이지만, 복잡한 변경은 "왜" 변경했는지 작성
- 하나의 커밋에 하나의 논리적 변경만 포함

---

## Code Review 규칙

리뷰 시 다음 형식을 따른다:

```
[심각도] 파일명:라인 - 설명

예시:
[CRITICAL] search.py:45 - SQL injection 가능성 있음. parameterized query 사용 필요
[HIGH] embedding.py:23 - CLIP model을 매 요청마다 로딩하고 있음. 앱 시작 시 한번만 로딩하도록 변경 필요
[MEDIUM] ProductCard.tsx:12 - key prop이 index로 되어있음. product_id 사용 권장
[LOW] api.ts:8 - 미사용 import 제거 필요
```

### 심각도 기준

| 심각도   | 기준                          | 반드시 수정? |
| -------- | ----------------------------- | ------------ |
| CRITICAL | 보안 취약점, 데이터 유실 가능 | ✅ 필수      |
| HIGH     | 버그, 성능 심각한 저하        | ✅ 필수      |
| MEDIUM   | 코드 품질, 유지보수성         | △ 권장       |
| LOW      | 스타일, 네이밍                | △ 선택       |

---

## Pull Request 전략

### PR 제목

```
[타입] 한국어 설명

예시:
[feat] 멀티모달 검색 API 구현
[fix] CLIP 임베딩 타임아웃 에러 수정
[refactor] 추천 서비스 코드 구조 개선
```

### PR 본문 템플릿

````markdown
## 📋 변경사항 요약

### 무엇을 변경했나?

- (변경 내용 구체적으로)

### 왜 변경했나?

- (변경 이유, 배경)

### 어떻게 변경했나?

- (기술적 접근 방식)

---

## 📸 스크린샷 / 테스트 결과

### UI 변경 시 스크린샷

| Before     | After      |
| ---------- | ---------- |
| (스크린샷) | (스크린샷) |

### API 변경 시 테스트 결과

```bash
# 테스트 실행 결과
pytest --cov=app
# Coverage: 85%
# Tests passed: 12/12
```
````

---

## ✅ 체크리스트

### 코드 품질

- [ ] 린터/포맷터 통과 (Black, Ruff / ESLint, Prettier)
- [ ] 타입 힌트 / TypeScript 타입 작성 완료
- [ ] 미사용 코드, console.log 제거

### 테스트

- [ ] 유닛 테스트 추가/수정
- [ ] 테스트 커버리지 80% 이상
- [ ] E2E 테스트 통과 (해당 시)

### 보안

- [ ] API 키, 시크릿 하드코딩 없음
- [ ] 입력값 검증 추가
- [ ] CORS 설정 확인 (해당 시)

### 문서

- [ ] CLAUDE.md 업데이트 (해당 시)
- [ ] API 문서 업데이트 (해당 시)
- [ ] DEVLOG.md 기록 (/log)

```

### PR 규칙

- base branch: `develop` (릴리즈 시에만 `main`)
- 하나의 PR에 하나의 기능/수정
- 큰 기능은 여러 PR로 분리
- `/code-review` 통과 후 PR 생성
- 셀프 리뷰: PR 올리기 전 자신의 diff를 한번 확인

---

## Branch 전략

```

main ← 배포 가능 상태만 (production)
└── develop ← 개발 통합 브랜치
├── feature/search-api ← 기능 개발
├── feature/frontend-ui ← 기능 개발
├── fix/embedding-timeout ← 버그 수정
└── docs/update-readme ← 문서 작업

```

### 흐름

```

feature/xxx → develop (PR) → main (릴리즈)

```

- `develop`에서 feature 브랜치 생성
- 작업 완료 → `develop`으로 PR
- 릴리즈 시 `develop` → `main` 머지

### 브랜치 네이밍 (영어만)

```

feature/search-api → 새 기능
feature/clip-embedding → 새 기능
fix/pinecone-timeout → 버그 수정
fix/cors-config → 버그 수정
docs/update-claude-md → 문서 작업
refactor/search-service → 리팩토링
test/search-unit-tests → 테스트 추가

```

### 규칙

- 브랜치명은 **영어 소문자 + 하이픈(-)** 만 사용
- 2~4 단어로 간결하게
- feature, fix 브랜치는 반드시 `develop`에서 분기

---

## Feature Implementation Workflow

1. **계획 수립**
   - `/plan` 으로 구현 계획 생성
   - 의존성과 리스크 파악
   - 작업을 작은 단위로 분리

2. **TDD 개발**
   - `/tdd` 로 테스트 먼저 작성 (RED)
   - 테스트 통과하는 최소 코드 구현 (GREEN)
   - 리팩토링 (IMPROVE)
   - 커버리지 80% 이상 확인

3. **코드 리뷰**
   - `/code-review` 로 품질 점검
   - CRITICAL, HIGH 이슈 반드시 수정
   - MEDIUM 이슈 가능하면 수정

4. **커밋 & PR**
   - 위 커밋 메시지 형식 준수
   - PR 템플릿에 맞게 작성
   - 체크리스트 전부 확인

5. **기록**
   - `/log` 로 DEVLOG.md에 작업 기록

Note: Attribution disabled globally via ~/.claude/settings.json.
```
