# AiX Decision System — 프로젝트 요약

반도체 FDC(드리프트 감지) + Adaptive DoE 플래너 통합, Artifact-First Viz 파이프라인, ML 앙상블 자동화.

---

## 1. 디렉터리 구조 및 역할

```
aix-decision-system/
├── backend/                    # FastAPI 백엔드
│   ├── app/
│   │   ├── core/               # 설정, DB, WebSocket
│   │   │   ├── config.py       # 환경변수(.env) 기반 설정
│   │   │   ├── database.py     # SQLAlchemy engine, Session, Base
│   │   │   └── websocket_manager.py  # 실시간 센서 브로드캐스트
│   │   ├── routers/            # API 라우트 (thin controller)
│   │   │   ├── auth.py         # 로그인/회원가입/me
│   │   │   ├── chat.py         # AI 채팅
│   │   │   ├── coupling.py     # 결합 제어
│   │   │   ├── dashboard.py    # KPI/verdict/top-causes (RCA)
│   │   │   ├── data_management.py
│   │   │   ├── datasets.py     # DataHub: 업로드/미리보기/커밋
│   │   │   ├── doe.py          # DoE 실험/공정창/추천
│   │   │   ├── fdc.py          # FDC 알람/드리프트/공정능력
│   │   │   ├── generator.py    # 합성 데이터 생성(etch/depo/litho)
│   │   │   ├── interlock.py    # 인터락
│   │   │   ├── kpi.py
│   │   │   ├── ml_pipeline.py  # ML 앙상블 파이프라인
│   │   │   ├── papers.py       # 논문 업로드/추출
│   │   │   ├── recommendations.py
│   │   │   ├── seeds.py        # 시드 카탈로그
│   │   │   ├── settings.py     # process_window, alarm_thresholds, integrations
│   │   │   ├── spc.py          # SPC 차트/위반/Cpk
│   │   │   ├── viz.py          # Viz Automation: run-step, artifacts
│   │   │   ├── vpd.py          # VPD 그리드/설정/DoE runs
│   │   │   └── workflow.py
│   │   ├── services/           # 비즈니스 로직 (routes에서 호출)
│   │   │   ├── data_integration_service.py
│   │   │   ├── db_query_service.py
│   │   │   ├── deepseek_service.py
│   │   │   ├── doe_service.py
│   │   │   ├── generator/      # etch_generator
│   │   │   ├── ml_ensemble_service.py
│   │   │   ├── pipeline_service.py
│   │   │   ├── report_renderer.py
│   │   │   ├── viz_steps.py
│   │   │   └── vpd_service.py
│   │   ├── etchfdc/            # Viz 파이프라인 (raw→policy)
│   │   │   ├── io/mat_reader.py
│   │   │   └── pipeline/steps/ # raw, clean, eda, fe, pca, cluster, models, policy
│   │   ├── templates/sop/      # Jinja2 리포트 (FDC, SPC, interlock, RCA)
│   │   └── utils/
│   ├── schema.sql              # MySQL DDL (단일 소스)
│   ├── scripts/                # DB 설정, 시드, 마이그레이션
│   └── requirements.txt
├── frontend/                   # React + Vite + TypeScript
│   └── src/
│       ├── api/                # vpd 등 API 클라이언트
│       ├── app/apiClient.ts    # 공통 HTTP 클라이언트
│       ├── components/         # ProtectedRoute, Sidebar, TopBar
│       ├── contexts/           # AuthContext
│       ├── features/           # 기능별 API + 훅
│       │   ├── fdc/            # fdc.api, useFdcAlarms
│       │   ├── settings/       # settings.api, useProcessWindow
│       │   ├── spc/            # spc.api, useSpcChart
│       │   └── viz/            # vizAutomationApi
│       ├── pages/              # 라우트별 페이지 (Dashboard, FDC, DoE, …)
│       └── types/
├── docs/                       # 요구사항, 설계, API 계약, 용어
│   ├── REQUIREMENTS.md
│   ├── DESIGN.md
│   ├── API_CONTRACT.md        # API 명세 (진실 소스)
│   └── INTERLOCK_GLOSSARY_AND_MODEL_SPEC.md
├── notebooks/                  # .mat → 파이프라인 아티팩트 (01~06)
├── streamlit_app/              # Streamlit 대시보드 (Overview, RCA, Predictions, Cost, Viz)
├── monitoring/                 # Prometheus 설정
├── docker-compose.yml
├── deploy.sh / deploy.bat
└── scripts/                    # start-backend, start-frontend (ps1/cmd)
```

---

## 2. 아키텍처

- **백엔드**: 계층 분리  
  - **Routes** (routers): HTTP 요청/응답만 처리.  
  - **Services**: 비즈니스 로직, DB/파일 접근, ML·Viz 파이프라인 호출.  
  - **Core**: 설정, DB 연결, WebSocket 매니저.
- **프론트엔드**:  
  - **Pages**: 레이아웃·라우팅.  
  - **Features**: 도메인별 `*.api.ts` + React Query 훅.  
  - **apiClient**: 인증 헤더·베이스 URL 공통화.
- **데이터**:  
  - **Raw**: 업로드 원본 (`data/raw/`).  
  - **Stage**: datasets.stage = DRAFT → PREVIEW → COMMITTED.  
  - **Artifact-First**: Viz 단계별 png/csv/json은 `reports/figures/{dataset_id}/{step}/` 등에 저장 후 URL로 제공.

---

## 3. 백엔드·DB·프론트 워크플로우

### 3.1 데이터 허브 → Viz Automation

1. **Datasets (DataHub)**  
   - 업로드(CSV/.mat) → DRAFT.  
   - POST preview → PREVIEW, 미리보기 JSON 저장.  
   - POST commit → COMMITTED (`committed=1`이어야 run-step 허용).
2. **Viz Automation**  
   - committed 데이터셋에 대해 `POST /viz/{id}/run-step?step=raw|clean|eda|fe|pca|cluster|models|policy`.  
   - 백엔드가 etchfdc 파이프라인으로 아티팩트 생성 → 디스크에 저장.  
   - 프론트는 `GET /viz/{id}/artifacts?step=...` 및 `GET /viz/artifacts/{path}`로 표시.
3. **DB**  
   - `datasets`: stage, committed, storage_path, schema_json.  
   - 나머지 메타는 `schema.sql` 기준 (users, papers, process_window, alarm_thresholds, vpd_*, doe_* 등).

### 3.2 대시보드 / RCA / 예측 / 비용

- **Dashboard**: `/dashboard/kpis`, `/dashboard/verdict`, `/dashboard/top-causes` (실제 데이터 기반 GO/WATCH/NO-GO).  
- **RCA**: `/rca/pareto`, `/rca/drivers`, `/rca/clusters`, `/rca/clusters/{id}/causes`.  
- **Prediction**: `/prediction/risk-table`, `/prediction/calibrate`, `/prediction/policy`.  
- **Cost**: `/cost/optimal-threshold`, `/cost/alarm-volume`.  
- 프론트: 해당 페이지에서 위 API 호출 후 카드/차트/테이블로 표시.

### 3.3 인증·실시간

- **Auth**: POST login/signup → JWT. `GET /auth/me`로 현재 사용자.  
- **WebSocket**: `/ws` — 센서 시뮬레이션 브로드캐스트(개발/데모).

---

## 4. 구현된 API (요약)

- **Auth**: `POST /api/v1/auth/login`, `signup`, `GET /api/v1/auth/me`  
- **Datasets**: `GET/POST /api/v1/datasets`, upload, `{id}`, `{id}/preview`, `{id}/undo-preview`, `{id}/commit`  
- **Viz**: `POST /api/v1/viz/{id}/run-step`, `GET /api/v1/viz/{id}/summary`, `GET /api/v1/viz/{id}/artifacts`, `GET /api/v1/viz/artifacts/{path}`  
- **Dashboard**: `GET /dashboard/kpis`, `/dashboard/verdict`, `/dashboard/top-causes`  
- **RCA**: `GET /api/v1/rca/pareto`, `/rca/drivers`, `/rca/clusters`, `/rca/clusters/{id}/causes`  
- **Prediction**: `GET /api/v1/prediction/risk-table`, `policy`, `POST calibrate`  
- **Cost**: `POST /api/v1/cost/optimal-threshold`, `GET /api/v1/cost/alarm-volume`  
- **FDC**: alarms/active, process/capability, sensors/data 등  
- **SPC**: chart, violations, cpk-trend  
- **DoE**: experiments/plan, active; process-window, recommendations  
- **ML Pipeline**: run-automated-pipeline, pipeline-status, pipeline-results, select-best-combination  
- **Settings**: process_window, alarm_thresholds, integrations  
- **VPD**: grids, settings, DoE runs  
- **Papers, Seeds, Generator, Chat, Coupling, Interlock, Recommendations, Data Management** 등  
- **Health**: `GET /`, `/health`, `/api/v1/health`  
- **WebSocket**: `WS /ws`

상세 경로·요청/응답 형식은 **docs/API_CONTRACT.md**를 기준으로 한다.

---

## 5. 데이터베이스 (MySQL)

- **schema.sql** 한 파일에 전체 DDL.  
- 테이블: users, papers, paper_extractions, datasets(stage, committed), seed_catalog, synthetic_runs, process_window, alarm_thresholds, integrations, vpd_grids, vpd_settings, doe_runs, doe_measurements.  
- Raw 테이블은 갱신 최소화; 설정/피처/메트릭은 버전·파생 원칙 유지.

---

## 6. 정리 후 문서 구조

- **필수 문서**: `README.md`, `docs/REQUIREMENTS.md`, `docs/DESIGN.md`, `docs/API_CONTRACT.md`, `docs/INTERLOCK_GLOSSARY_AND_MODEL_SPEC.md`, `docs/SUPPLEMENTS.md`, `docs/PROJECT_SUMMARY.md`(본 문서).  
- **배포/보안**: 루트 `SECURITY.md`, 필요 시 `DEPLOYMENT_GUIDE.md` 하나로 통합.  
- **DB**: `backend/schema.sql` 단일. 스크립트는 `backend/scripts/`에만 두고 중복 제거.

이 요약은 디렉터리 구조, 폴더/파일 역할, 백엔드·DB·프론트 워크플로우, API, 아키텍처를 한곳에서 보기 위한 것이다.
