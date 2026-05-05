# Batch Analytics — High-Volume Processing

**Owner:** [T] Titty  
**Type:** Data Engineering / Analytics  
**Status:** Production  
**Stack:** Python 3.x + Bash | PostgreSQL | Airflow | dbt | MinIO

---

## What It Is

High-volume batch processing platform using Python + dbt + PostgreSQL + MinIO. Processes large datasets with idempotent ETL pipelines, SLA compliance, and data observability.

**GitHub:** `mrohitth/batch-analytics-platform`

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Orchestration** | Apache Airflow | DAG scheduling, SLA monitoring |
| **Transformation** | dbt | SQL incremental models on PostgreSQL |
| **Warehouse** | PostgreSQL | dim tables, fact tables, analytics |
| **Object Storage** | MinIO (S3-compatible) | Raw JSONL landing, checkpoints |
| **Extraction** | Python + Bash | CDC extract, batch file processing |
| **CI/CD** | GitHub Actions | dbt test gates, data quality checks |

---

## Architecture Principles

| Principle | Implementation |
|-----------|----------------|
| **Idempotency** | Every job re-runnable — use `batch_id` for deduplication |
| **Partitioning** | By date/entity for parallel processing |
| **Checkpoints** | Savepoint files in MinIO for fault-tolerant reprocessing |
| **Data Quality** | dbt tests + z-score anomaly detection before write |
| **Lineage Tracking** | Track source → transform → output via dbt lineage graph |
| **SCD Type 2** | Python MERGE + PostgreSQL for dimension versioning |

---

## Key Patterns

- **Delta processing:** Only process new/updated records (`WHERE updated_at > last_run`)
- **Job ordering:** Dependencies resolved via Airflow DAG (no circular refs)
- **Alerting:** SLA breach → trigger notification + log to daily journal
- **Backfill:** Idempotent reprocessing via `batch_id` isolation in MinIO
- **Fingerprinting:** MD5 hash of source rows for deduplication before write

---

## Airflow DAG Structure

```python
# dags/batch_analytics_dag.py
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

with DAG(
    "batch_analytics",
    default_args={"retries": 2},
    schedule_interval="0 6 * * *",
    start_date=datetime(2026, 1, 1),
) as dag:

    extract = BashOperator(
        task_id="extract_batch",
        bash_command="""
        python3 /opt/etl/cdc_extract.py \
            --batch-id "run_{{ ds }}" \
            --output "s3://raw-warehouse/batch/{{ ds }}.jsonl"
        """,
    )

    load_staging = BashOperator(
        task_id="load_staging",
        bash_command="""
        python3 /opt/etl/load_staging.py \
            --input "s3://raw-warehouse/batch/{{ ds }}.jsonl" \
            --staging-schema staging
        """,
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/dbt && dbt run --profiles-dir . --target prod",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="cd /opt/dbt && dbt test --profiles-dir . --target prod",
    )

    extract >> load_staging >> dbt_run >> dbt_test
```

---

**Cross-links:**
→ [../patterns/cdc-pipeline.md](../patterns/cdc-pipeline.md) — CDC pipeline patterns  
→ [../patterns/scd-type2.md](../patterns/scd-type2.md) — SCD Type 2 pattern  
→ [./cdc-platform.md](./cdc-platform.md) — CDC Platform (shares patterns)  
→ [../index.md](../index.md) — Wiki central  
→ [./index.md](./index.md) — Projects index