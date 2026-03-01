# Training Loop: Delayed Labels, Real-Time Inference, and Safe Model Promotion

## 1) Why this document exists

This project predicts whether a pacemaker will fail in the next 7 days (`Target_Fail_Next_7d`).
Because that target is outcome-based, most newly ingested telemetry rows are unlabeled at arrival time.

This document defines the production-style pattern used in this repo:

- run inference immediately for monitoring and alerts,
- delay supervised retraining until label windows mature,
- promote new models only through gated champion/challenger evaluation.

---

## 2) Core principle

Never use model predictions as supervised ground truth for retraining.

If predictions are fed back in as labels, model errors can self-reinforce over time.
Instead, labels come only from observed (or simulator-defined) outcomes.

---

## 3) Label definition

For a telemetry row at time $\tau$ for a specific patient/device:

- `Target_Fail_Next_7d = 1` if a confirmed failure event time `f` exists such that $\tau < f \leq \tau + 7\text{ days}$
- `Target_Fail_Next_7d = 0` otherwise (once full 7-day follow-up is available)

Implication:

- At ingestion time, the label is usually unknown.
- The row becomes trainable only after label resolution.

---

## 4) Two-loop operating model

### A) Online inference loop (real-time)

Runs continuously as telemetry arrives.

1. Ingest telemetry row(s) and validate schema.
2. Compute any required derived features.
3. Score with current active model.
4. Persist prediction probability and risk flag.
5. Trigger alerts if thresholds are crossed.

This loop serves dashboard freshness and alerting latency.

### B) Delayed training loop (scheduled/manual)

Runs on a cadence (for example daily) or manual trigger.

1. Identify rows with matured 7-day outcome windows.
2. Backfill true labels from failure outcomes.
3. Build training dataset from matured, outcome-labeled rows only.
4. Train challenger model.
5. Evaluate against baseline/champion and gate promotion.
6. Register artifact and metadata; activate only if gates pass.

This loop protects label quality and retraining integrity.

---

## 5) What “matured data” means

At training time `T_now`, a common maturity filter is:

- Include rows where `Timestamp <= T_now - 7 days`

Plus optional early positive resolution:

- If a failure is confirmed before full 7 days, affected prior rows can be labeled positive immediately.

Important:

- A row older than 7 days is **not automatically negative**.
- It is negative only if no qualifying failure occurred in its forward 7-day window.

---

## 6) Backfill process (conceptual)

For each patient/device timeline:

1. Collect failure event timestamps.
2. For each telemetry row at time `tau`, scan `(tau, tau+7d]` for failure.
3. Set `Target_Fail_Next_7d` accordingly.
4. Mark label status as resolved/matured.

Recommended metadata to track per row:

- `label_status` (`unresolved`, `resolved`)
- `label_resolved_at`
- `label_source` (`simulator_outcome`, `observed_outcome`)

---

## 7) Champion/challenger promotion policy

Use current active model as champion and newly trained model as challenger.

Promotion gates should include:

- minimum Recall and F1 for positive risk class,
- no unacceptable degradation in precision/false-positive burden,
- successful pipeline quality checks and artifact integrity.

If gates fail:

- keep challenger artifact for audit,
- keep champion active,
- never overwrite active model on failed run.

---

## 8) How this maps to project pipelines

For scheduled/on-demand MLOps runs in this project:

1. Ingest incremental synthetic telemetry.
2. Append + validate storage records.
3. Backfill matured labels from synthetic outcome timeline.
4. Train challenger on matured labeled subset.
5. Evaluate + log metrics and run metadata.
6. Register artifacts/metrics.
7. Promote only if thresholds pass.
8. Refresh prediction views and model metadata.

This aligns with the model registry, rollback safety, and traceability goals in `project.md`.

---

## 9) Anti-patterns to avoid

- Using prediction outputs as if they were true labels for supervised retraining.
- Training on unresolved rows with unknown outcomes.
- Mixing unresolved and resolved rows without explicit filtering.
- Auto-promoting models without metric gates and rollback path.

---

## 10) Notes for this repository

- Current data is synthetic, so outcome truth can be generated deterministically by simulation rules.
- If migrated toward real telemetry in the future, keep the same architecture but replace simulator truth with confirmed outcome events.
- Keep inference and training responsibilities separate: fast online scoring, delayed supervised learning.
