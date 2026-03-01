# Project Scope: Pacemaker Telemetry MLOps Showcase

## 1) Project Summary

### Working Title

**Pacemaker Telemetry Risk Monitoring Platform (Interview Showcase)**

### Purpose

Build a production-style, interview-ready web application that demonstrates end-to-end software engineering across:

- Data simulation and ingestion
- AI/ML training and evaluation
- MLOps automation
- CI/CD with Azure DevOps

This project is intentionally designed as a showcase artifact for a summer software engineering internship interview in a medical-device R&D context.

### Audience

Primary audience: **technical interview panel** (engineering manager + software/data/ML engineers).

### Document Depth

**Balanced technical specification (2–4 pages)** focused on clarity, implementability, and demonstration value.

---

## 2) Context and Problem Statement

Medical device teams often process telemetry streams and must continuously evaluate device health trends. This project simulates that workflow by generating realistic synthetic pacemaker telemetry, training models to predict near-term device failure risk, and exposing outcomes through a web dashboard.

The goal is **not** to create a clinically validated product. The goal is to demonstrate strong engineering judgment, practical ML lifecycle management, and automation discipline in a realistic domain.

---

## 3) Objectives and Success Criteria

### Primary Objectives

1. Demonstrate **end-to-end MLOps thinking** from synthetic data generation to model deployment and monitoring.
2. Demonstrate **strong software engineering practices** (clear architecture, APIs, testing, traceability).
3. Demonstrate **model quality workflow** (training, validation, evaluation metrics, model versioning).
4. Demonstrate **Azure DevOps CI/CD fluency** (build/test/deploy pipelines plus scheduled ML workflow).

### Success Criteria (Interview-Facing)

- A live hosted web app is accessible via public URL without local setup.
- Telemetry appears as “incoming/live-like” synthetic data on the dashboard.
- The app shows patient-level risk predictions and model performance metrics.
- Multiple model versions are visible with metadata (version, timestamp, metrics, active status).
- A user can trigger a training run from the UI using newly ingested data, otherwise, the system automatically trains on new data every 24 hours.
- High-risk events and flags trigger automated email alerts sent to designated recipients.
- Azure DevOps pipelines are demonstrable for CI/CD and scheduled MLOps jobs.

### Non-Goals

- Clinical decision support or medical diagnosis.
- Regulatory-grade compliance implementation.
- Internet-scale distributed processing.
- Real patient data ingestion.

---

## 4) Scope Boundaries and Assumptions

### In Scope

- Synthetic pacemaker telemetry generation (large-scale dataset + ongoing incremental records).
- Backend API for data ingestion, model training trigger, model selection, and metrics retrieval.
- ML training/evaluation pipeline using Random Forest baseline.
- Model registry metadata and active-model selection.
- React dashboard for risk monitoring and model operations.
- Automated email notifications for high-risk predictions.
- Azure DevOps pipelines for CI/CD and scheduled MLOps execution.
- Cloud-hosted demo deployment (single environment suitable for interview showcase).

### Out of Scope

- Distributed training (Spark, Dask, etc.).
- Advanced AutoML/hyperparameter sweeps at large scale.
- Full RBAC/SSO enterprise auth flows.
- HIPAA production hardening and regulated validation workflows.
- Infrastructure as Code (IaC) for environment provisioning (manual setup is acceptable for demo).
- Infrastructure scaling beyond single-instance hosting (no Kubernetes or multi-node clusters).

### Operating Assumptions

- Data is 100% synthetic.
- App is demo-grade but engineering-rigorous.
- Architecture prioritizes reliability and explainability over scale complexity.

---

## 5) Functional Requirements

### FR-1 Data Generation

- System provides `generate_data.py` (or equivalent service task) to create initial telemetry dataset with ~2,000,000+ rows.
- The data generation script I already have created and will import it as generate_data.py.
- Data schema includes:
  - `patient_id`: Integer identifier for each patient/device (0..num_patients-1).
  - `timestamp`: Unix timestamp of each telemetry ping.
  - `lead_impedance_ohms`: Electrical impedance of the lead, which can indicate lead integrity issues.
  - `capture_threshold_v`: Voltage required to capture the heart, which can rise as the device degrades.
  - `r_wave_sensing_mv`: Quality of R-wave sensing, which can drop as the device fails.
  - `battery_voltage_v`: Voltage of the device battery, which can drop rapidly before failure.
  - `target_fail_next_7d`: Binary target variable indicating if the device will fail within the next 7 days (1) or not (0).
  - `lead_impedance_ohms_rolling_mean_3d`: Trailing 3-day rolling mean of lead impedance.
  - `lead_impedance_ohms_rolling_mean_7d`: Trailing 7-day rolling mean of lead impedance.
  - `capture_threshold_v_rolling_mean_3d`: Trailing 3-day rolling mean of capture threshold.
  - `capture_threshold_v_rolling_mean_7d`: Trailing 7-day rolling mean of capture threshold.
  - `lead_impedance_ohms_delta_per_day_3d`: Average per-day change in impedance over trailing 3 days.
  - `lead_impedance_ohms_delta_per_day_7d`: Average per-day change in impedance over trailing 7 days.
  - `capture_threshold_v_delta_per_day_3d`: Average per-day change in threshold over trailing 3 days.
  - `capture_threshold_v_delta_per_day_7d`: Average per-day change in threshold over trailing 7 days.
- System supports continuous synthetic increments to simulate live telemetry data arrival.
- Initial synthetic dataset is ordered by `timestamp` then `patient_id`, so all patients are represented in parallel at each telemetry interval.

### FR-2 Data Ingestion API

- Backend can either seed the database with the initial synthetic dataset or provide an endpoint to receive data uploads.
- Default local demo behavior starts with an empty telemetry table (`SEED_PACEMAKER_DATA=False`) and receives incremental data through API ingestion.
- Backend will exposes endpoint(s) to perform the following:
  - Receive/add new telemetry records.
  - Get information about current data, models, and metrics.
  - Trigger model training with latest data.
  - Retrieve patient-level risk predictions.
  - Select active model version.
  - Retrieve model performance metrics and version history.
  - Trigger email alerts for high-risk predictions.
- Incoming records are validated and appended to the dataset/store (Azure PostgreSQL database).
- Primary ingest contract for the demo is a superuser-protected bulk POST endpoint (`/api/v1/telemetry/ingest`) that accepts a JSON array payload (typical daily batch up to ~1000 rows, max 2000 rows/request).
- Batch size is variable: smaller batches are expected when some simulated patient devices stop reporting (for example due to failure events).
- Each row requires `patient_id`, Unix-epoch `timestamp` (seconds, UTC), `lead_impedance_ohms`, `capture_threshold_v`, `r_wave_sensing_mv`, and `battery_voltage_v`; engineered features and `target_fail_next_7d` are optional.
- Duplicate rows (same `patient_id` + `timestamp`) are rejected and reported in the ingestion response summary.
- Ingestion events are auditable (timestamped run/event metadata).
- **Labeling and Training Window Brief:** Newly ingested telemetry is treated as unlabeled at arrival time for supervised retraining purposes. The active model still performs immediate inference for risk monitoring/alerts, while `Target_Fail_Next_7d` is backfilled only after the 7-day outcome window matures (or a failure event is confirmed within that window). Retraining jobs use only matured, outcome-labeled rows and never treat model predictions as ground-truth labels.

### FR-3 Model Training

- Uses scikit-learn for ML training.
- Baseline model is Random Forest Classifier.
- `MLEngine` class in `ml_engine.py` is the training orchestrator for preprocessing, model fitting, prediction, and model serialization.
- Training pipeline includes preprocessing, feature selection/engineering, and cross-validation.
- `Patient_ID` and raw `Timestamp` are excluded as direct predictive features unless transformed purposefully.
- `MLEngine` includes a data preparation step that isolates feature/target columns, drops non-predictive columns, and removes rows with missing values produced by rolling-window features.
- `MLEngine` accepts configurable Random Forest hyperparameters (for example: `n_estimators`, `max_depth`, and `random_state`) through class initialization.
- Trained model artifact is persisted with version metadata, with model serialization/deserialization implemented via `joblib`.
- **Data Retrieval Strategy:** The local training script (`ml_engine.py`) connects directly to the Azure PostgreSQL database. To minimize data transfer and database load, it performs an incremental pull of new records based on the latest timestamp and appends them to a local Parquet cache file before loading into a pandas DataFrame for training.
- **Delayed Supervised Retraining Rule:** At training time `T_now`, candidate models are trained only on rows whose label windows are mature (typically records with `Timestamp <= T_now - 7 days`, plus any records positively resolved earlier by confirmed failure events). This avoids self-training feedback loops from pseudo-labeling.
- See `docs/training_loop.md` for the detailed delayed-label training lifecycle and promotion guardrails.

### FR-4 Model Evaluation

- Utilize Out-of-Bag (OOB) error for rapid iteration during training, and K-Fold cross-validation for final model validation.
- Evaluate overall model performance using Accuracy
- Use Scikit-Learn’s `classification_report` to generate a comprehensive breakdown of Precision, Recall, F1-Score, and Support for each class.
- Set `oob_score=True` within the `RandomForestClassifier` to natively compute the OOB score as a baseline metric.
- Log all hyperparameter configurations and resulting evaluation metrics (Run History) to a structured format to enable comparison across models; the training layer exposes applied hyperparameters and outputs for downstream run-history logging.

### FR-5 Model Registry and Selection

- System tracks model versions with:
  - Version identifier (timestamp based)
  - Training time
  - Dataset range/size
  - Evaluation metrics
  - Active/inactive status
- User can select an active model from dashboard/API.

### FR-6 Predictions and Risk Monitoring

- Active model generates patient-level risk predictions.
- Dashboard presents “at risk” patients and supporting telemetry context.
- Dashboard updates every hour with new predictions and telemetry data.

### FR-7 Alerting

- When risk crosses defined threshold/flag condition, system sends email notification to a predefined alerting email address.
- For the purpose of this project, emails will be caught by mailcatcher in the local development environment.
- Alert message includes patient identifier and relevant prediction metadata.

### FR-8 UI/UX (Dashboard)

- Will be designed and initially drafted in Subframe.
- The dashboard is built with React + TypeScript and styled with Tailwind CSS.
- Dashboard UI elements include:
  - Live/stream-like telemetry feed view
  - Patient risk table/list ordered by risk level showing the top 10 at-risk patients with key telemetry features and risk scores. Paginated view.
  - Model metrics panel to show current active model performance (accuracy, precision, recall, F1) and training metadata.
  - Model version details and active model selection.
- There will be another page for model management that includes:
  - List of models with metadata and metrics.
  - Current active model clearly indicated and details.
  - Training trigger control (“Train new model with latest data”).
  - Model selection control to set active model.
  - Delete model control to remove underperforming models from registry.

### FR-9 CI/CD + MLOps Automation (Azure DevOps)

- The platform uses a **hybrid setup** with an Azure-hosted web application and Azure DevOps orchestration, while model training/evaluation executes on a **self-hosted Azure DevOps agent running on my local PC**.
- Azure does not directly call into the local machine; instead, Azure DevOps queues jobs and the local self-hosted agent polls and picks up training jobs.
- Reference: `docs/training_loop.md` contains the detailed inference-vs-retraining loop and label backfill process used by scheduled/manual MLOps runs.

- **Pipeline Separation**
  - `CI` validates code quality and build integrity.
  - `CD` deploys approved backend/frontend changes to the hosted environment.
  - `Scheduled MLOps` handles recurring data/model lifecycle runs and routes training jobs to the local self-hosted agent pool.

- **CI Pipeline (Trigger: push/PR)**
  - Runs on pull requests and branch updates for backend/frontend code.
  - Performs linting, testing, and build validation for application code.
  - Publishes logs and test results as pipeline artifacts for traceability.

- **CD Pipeline (Trigger: main branch or approved release)**
  - Deploys backend and frontend to the hosted demo environment.
  - Executes smoke checks after deployment; if checks fail, deployment is marked failed and previous stable release remains active.

- **Training Trigger Paths**
  - Manual: user clicks “Train new model with latest data” in the dashboard.
  - Automated: scheduled MLOps run (every 24 hours by default).
  - Both trigger Azure DevOps, which queues a training/evaluation job on the local self-hosted agent.

- **Scheduled/On-Demand MLOps Job Sequence**
  1. Generate/ingest new synthetic telemetry batch.
  2. Append and validate incoming data in dataset/storage.
  3. Backfill matured `Target_Fail_Next_7d` labels from observed/simulated outcomes.
  4. Train candidate model on local self-hosted agent using only matured, outcome-labeled rows.
  5. Evaluate candidate model and persist metrics/run metadata.
  6. Publish model artifact and metrics back to Azure artifact storage/registry.
  7. Promote model to active only if promotion thresholds are met.
  8. Refresh dashboard-facing metrics and predictions.

- **Promotion, Rollback, and Failure Handling**
  - Promotion gate compares candidate metrics to baseline thresholds (emphasis on Recall/F1 for risk detection).
  - Candidate models below threshold are retained for audit but not activated.
  - Failed training/evaluation never overwrites the active model.
  - Manual rollback to previous stable model version is supported from model controls.

- **Observability and Auditability**
  - Every pipeline run stores run ID, commit reference, stage status, timestamps, and generated artifacts.
  - Every model version stores source run ID, dataset window/size, hyperparameters, and evaluation metrics.
  - Dashboard and API expose active model metadata and latest pipeline outcomes.

---

## 6) Non-Functional Requirements

### Reliability

- Pipeline jobs produce clear pass/fail signals and logs.
- Failed training/evaluation must not silently overwrite active model.

### Traceability

- Each model version links to training run metadata and evaluation outputs.

### Performance (Demo-Scale Targets)

- Initial training should complete in practical demo time.
- Dashboard API responses should remain responsive for interactive demo usage.

### Security (Demo Baseline)

- Secrets managed via environment variables / secure pipeline variables.
- No hardcoded credentials.

### Maintainability

- Clear module boundaries (data, training, serving, UI, pipelines).
- Readable docs and reproducible local/CI workflows.

---

## 7) High-Level Architecture

### Components

1. **Data Generator Service/Script**
   - Creates initial + incremental synthetic telemetry.
2. **Backend (FastAPI)**
   - Ingestion endpoints
   - Training/evaluation orchestration endpoints
   - Model metadata endpoints
   - Prediction endpoints
   - Alert dispatch logic
   - **Storage:** Azure PostgreSQL database for telemetry records, users, and model metadata.
3. **ML Layer**
  - Preprocessing + training + validation (encapsulated by the `MLEngine` class in `ml_engine.py`)
  - Artifact persistence via `joblib`
   - Metrics persistence
4. **Frontend (React Dashboard)**
   - Telemetry/risk views
   - Model lifecycle controls and visualizations
5. **Azure DevOps Pipelines**
   - CI/CD automation and scheduled MLOps jobs
   - Job orchestration and artifact storage in Azure DevOps
6. **Local Self-Hosted Training Agent (Personal PC)**
   - Executes queued model training/evaluation jobs from Azure DevOps
   - Publishes model artifacts and metrics back to Azure
7. **Notification Service**
   - Email alerts for high-risk events

### Data Flow (Nominal)

1. Synthetic telemetry generated/ingested.
2. Data stored in Azure PostgreSQL and made available for training/prediction.
3. Training is requested by UI action or schedule, which triggers Azure DevOps pipeline run.
4. Azure DevOps queues the training job to the local self-hosted agent.
5. Local agent performs an incremental pull of new telemetry data from PostgreSQL, updates its local Parquet cache, trains/evaluates the model, and publishes artifacts/metrics back to Azure.
6. Candidate model is registered; active model is updated only if promotion gates pass.
7. Predictions refresh dashboard risk views using the active model.
8. High-risk predictions trigger email alert.

---

## 8) Azure DevOps Pipeline Design

### CI Pipeline (On Push/PR)

- Install dependencies
- Static checks/lint
- Unit/integration tests
- Build backend/frontend artifacts
- Optional security scans
- Publish test reports

### CD Pipeline (On Main / Approved)

- Deploy backend + frontend to hosted environment
- Run smoke checks
- Publish deployment metadata

### Scheduled MLOps Pipeline (Daily/Weekly)

- Generate/ingest new synthetic batch
- Queue training/evaluation job on local self-hosted Azure DevOps agent
- **Data Sync:** Local agent performs an incremental pull of new telemetry data from Azure PostgreSQL and updates its local Parquet cache.
- Retrain model on latest dataset (local PC compute)
- Evaluate and log metrics
- Publish/register versioned artifact back to Azure artifact storage/registry
- Optionally auto-promote model based on metric thresholds
- Refresh dashboard data source/state

### Hybrid Compute Notes

- Hosted web app and API remain online in Azure; training/evaluation compute runs locally on the self-hosted agent.
- If the local agent is offline, training jobs remain queued until the agent is available.
- This setup is acceptable for demo/interview scope and can later migrate to cloud compute without changing pipeline contracts.

### Suggested Guardrails (optional, skip unless asked for)

- Promotion gate: only activate new model if F1/Recall meet baseline threshold.
- Rollback support: revert active model to previous stable version.

---

## 9) Data and Modeling Notes

### Synthetic Data Intent

Telemetry should emulate plausible drift and degradation patterns, such as:

- Increasing lead impedance trends
- Rising capture thresholds
- Falling R-wave sensing quality
- Battery voltage decline

### Labeling Logic

`target_fail_next_7d` is engineered to represent near-term failure risk from synthetic/derived rules and event simulation.

### Baseline Modeling Plan

- Start with Random Forest for interpretability and robust baseline performance.
- Use chronological considerations to avoid leakage (time-aware splits where appropriate).
- Track confusion matrix and threshold behavior to support risk-alert tuning.

---

## 10) Demo Readiness Requirements

To maximize interview impact, the hosted application should support this narrative flow:

1. Open public URL.
2. Show live-like incoming telemetry updates.
3. Show current active model and its metrics.
4. Explore at-risk patients and recent predictions.
5. Trigger training with latest data.
6. Show new model version + updated metrics.
7. Demonstrate risk alert and email workflow.
8. Explain Azure DevOps CI/CD + scheduled MLOps automation.

---

## 11) Risks and Mitigations

- **Risk:** Synthetic patterns are too simplistic and produce unrealistic metrics.
  - **Mitigation:** Add controlled noise, drift regimes, and class imbalance handling.

- **Risk:** Model retraining causes unstable quality swings.
  - **Mitigation:** Use promotion thresholds + fallback to last stable model.

- **Risk:** Demo dependency failures (email service, hosting, pipeline trigger timing).
  - **Mitigation:** Add smoke checks, mock fallback mode, and pre-demo health checklist.

- **Risk:** High database egress costs and slow training times due to large data transfers (2M+ rows).
  - **Mitigation:** Implement an incremental pull strategy and local Parquet caching on the self-hosted agent to only fetch new rows.

---

## 12) Delivery Plan (Suggested)

### Phase 1 — Foundation

- Define schema and generate initial 2M+ synthetic dataset.
- Implement ingestion and storage path.

### Phase 2 — Baseline ML

- Build preprocessing + training + evaluation pipeline.
- Persist model artifacts and metrics history.

### Phase 3 — Product Surface

- Build FastAPI endpoints and React dashboard views.
- Add model selection + training trigger + risk table.

### Phase 4 — Automation + Hosting

- Implement Azure DevOps CI/CD + scheduled MLOps pipeline.
- Deploy hosted app and validate demo flow end-to-end.

---

## 13) Final Statement

This project is a focused, practical demonstration of modern software + ML engineering in a healthcare-adjacent scenario. It intentionally balances technical depth with delivery realism: a complete, hosted, and automated end-to-end system that can be discussed concretely in an interview setting.
