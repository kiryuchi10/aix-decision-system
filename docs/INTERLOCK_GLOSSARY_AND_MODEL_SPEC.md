# Interlock Response: Glossary & Model Spec

Reusable glossary (KO/EN) and model specification for the STOP/Release Decision AI and related FDC/ML concepts.

---

## 1. Glossary (KO/EN)

| Term (EN) | Term (KO) | Definition |
|-----------|-----------|------------|
| **Interlock** | 인터록 | A safety or process condition that triggers equipment stop or hold when a limit is exceeded. |
| **FDC** | FDC (결함 탐지·분류) | Fault Detection and Classification; monitoring sensor data for drift, step change, or anomaly. |
| **FDC Sensor Data** | FDC 센서 데이터 | Time-series sensor readings (e.g. temp, pressure, RF power) used for interlock and fault monitoring. |
| **STOP/Release Decision AI** | STOP/Release 판정 AI | AI that decides: NORMAL, RELEASE (simple check then run), or STOP (equipment repair). |
| **Release** | Release (간단 점검 후 가동) | Decision path: quick verification then resume operation. |
| **STOP** | STOP (설비 수리) | Decision path: halt equipment and perform repair/maintenance. |
| **Equipment Downtime** | 설비 유실 시간 | Time lost due to unplanned stops or unnecessary holds; goal is to reduce it. |
| **Control Limit** | 관리 한계 | Upper/lower bounds (UCL/LCL) within which process is considered in control. |
| **Interlock Monitoring** | Interlock 발생 여부 모니터링 | Continuous check for conditions that would trigger an interlock. |
| **LSTM** | LSTM (Long Short-Term Memory) | Recurrent network for sequential FDC data; output can be Normal/STOP/Release. |
| **Transformer** | Transformer | Encoder with self-attention for sequence modeling; input tokens from FDC data, output for status/decision. |
| **Self-Attention** | Self-Attention | Mechanism (Q, K, V) to weight importance of different time steps or features. |
| **Continual Learning** | Continual Learning (연속 학습) | Learning from new FDC data while applying forgetting-prevention so existing performance is maintained. |
| **Domain Adaptation** | Domain Adaptation (도메인 적응) | Adapting model to new process/distribution (e.g. new chamber) by reducing distribution difference. |
| **BiLSTM2D** | BiLSTM2D | Bidirectional LSTM in 2D (vertical + horizontal) for multi-channel or 2D time-series. |
| **P1, P2** | P1, P2 | Latent dimensions (e.g. from t-SNE/UMAP) for visualizing process status (STOP vs Release). |
| **Process (in plot)** | 공정 | A process type or recipe (e.g. IWZPBFVT, 1311UV) in scatter or status plots. |
| **Token** | 토큰 | Segment of time-series or window used as input to Transformer/LSTM. |
| **Windowing** | 윈도잉 | Splitting raw FDC data into fixed-length windows for model input. |

---

## 2. Model Spec: STOP/Release Decision AI

### 2.1 Purpose
- **Input:** FDC sensor snapshot or short window (e.g. temp, pressure, RF, gas flow, endpoint).
- **Output:** One of **NORMAL**, **RELEASE**, **STOP**.
- **Goal:** Reduce equipment downtime by:
  - Releasing when a quick check is enough.
  - Stopping only when repair is needed.

### 2.2 Input/Output
- **Input:** `sensor_snapshot` (dict or array), optional `chamber_id`, `recipe_id`, `interlock_detected` (bool).
- **Output:** `decision`, `confidence`, `reason_ko` / `reason_en`, `suggested_action_ko` / `suggested_action_en`, `timestamp`.

### 2.3 Possible Implementations
- **Rule-based:** Thresholds + simple rules (e.g. sigma distance, rate of change).
- **LSTM:** Recurrent model over FDC windows → 3-class (Normal/Release/Stop).
- **Transformer:** Tokenized FDC windows → encoder → classification head.
- **Hybrid:** Rules for clear cases, ML for borderline.

### 2.4 Integration
- **FDC:** Consumes FDC alarms/drift output and optional raw snapshot.
- **Coupling Control:** Decision feeds into “execute / request approval” and audit log.
- **Reports:** Interlock report template (figures + KPI table) uses same KPIs (events_24h, release_count, stop_count, downtime_saved_hr).

---

## 3. Model Spec: Deep Learning Architectures (FDC)

### 3.1 LSTM for FDC
- **Input:** FDC 데이터 (time-series).
- **Output:** 정상 / STOP / Release (or multi-class alarm type).
- **Use:** Sequential pattern and short-term memory for drift/step/intermittent.

### 3.2 Transformer Encoder for FDC
- **Input:** 입력 토큰 (windowed FDC data) + 시정정보 (position encoding).
- **Block:** Self-Attention (Q, K, V) + Feed-Forward + LayerNorm + Residual.
- **Output:** 출력 토큰 → classification (정상/STOP/Release).

### 3.3 Attention & BiLSTM2D
- **Attention:** Norm → MH Attention → Norm → Channel MLP (with skip).
- **BiLSTM2D:** Vertical BiLSTM + Horizontal BiLSTM → concat → Channel Fusion; for 2D or multi-channel FDC.

### 3.4 Data Windowing
- Raw FDC stream → fixed-length windows → tokens (token1, token2, …) for LSTM/Transformer input.

---

## 4. Report Template Usage

- **Template:** `backend/app/templates/sop/jinja2/interlock_report.html`
- **Renderer:** `render_interlock_report(interlock_data, report_meta, data_meta, figures_placeholder, kpi_table, figures)`
- **Placeholders:** Up to 4 figures (FDC sensor, Decision AI, Continual/Domain, Process P1–P2 scatter); KPI table (metric_en, metric_ko, value).

---

## 5. API Endpoints (Stub)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/interlock/decision` | Request STOP/Release decision (stub). |
| GET | `/api/v1/interlock/status` | Aggregate status (events_24h, release_count, stop_count, downtime_saved_hr). |
| POST | `/api/v1/interlock/reports/generate` | Generate interlock HTML report. |

All require auth (`get_current_user`) where applicable.
