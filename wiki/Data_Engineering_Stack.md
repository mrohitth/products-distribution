# Data Engineering Stack — Mathew's Professional Toolkit

**Owner:** [T] Titty  
**Type:** Reference — Professional Stack  
**Status:** Canonical  
**Last Updated:** 2026-05-03

---

## What It Is

Reference page for the complete Python/PostgreSQL/dbt stack. Standardized architecture for performance, observability, and cost-efficiency.

---

## Core Technologies

### Data Extraction & CDC
**Python 3.x + Bash** — Timestamp-based CDC extraction using `psycopg2` + bash scripts. JSONL output to MinIO for lightweight, auditable change capture.

### Orchestration
**Apache Airflow** — DAG scheduling for ETL pipelines with SLA monitoring and cross-DAG dependencies.

### Transformation
**dbt** — SQL incremental models on PostgreSQL. Version-controlled, tested transformations with data lineage tracking.

### Warehouse
**PostgreSQL** — Operational and analytics warehouse. Supports SCD Type 2 via `MERGE INTO` for dimension versioning. Primary storage for dim tables and fact tables.

### Object Storage
**MinIO** — S3-compatible object storage. Stores raw JSONL CDC landing files, checkpoints, and backfill artifacts.

### Cloud Infrastructure
**AWS EKS + Lambda + S3** — Containerized workloads via Kubernetes (EKS) for scalable ETL, serverless functions (Lambda) for lightweight tasks, and S3 for long-term archival.

---

## Architecture Patterns

```
Source Systems → Python/Bash CDC Extract → MinIO JSONL Landing
    → PostgreSQL staging → dbt transforms → Analytics layer

Airflow orchestrates: extraction → staging → dbt run → dbt test → archival
```

**Key principles:**
- Idempotent batch processing with `batch_id` fingerprinting
- Delta-only processing (`WHERE updated_at > last_run`)
- dbt tests gate every transformation layer

---

## Related Patterns

→ [./patterns/scd-type2.md](./patterns/scd-type2.md) — SCD Type 2 pattern  
→ [./patterns/cdc-pipeline.md](./patterns/cdc-pipeline.md) — CDC pipeline pattern  
→ [./projects/cdc-platform.md](./projects/cdc-platform.md) — CDC Warehouse platform  
→ [./projects/batch-analytics.md](./projects/batch-analytics.md) — Batch Analytics platform

---

**Cross-links:**
→ [./index.md](./index.md) — Wiki central  
→ [./projects/index.md](./projects/index.md) — Projects index