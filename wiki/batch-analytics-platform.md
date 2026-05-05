# Batch Analytics Platform

**Owner:** [T] Titty  
**Repo:** `mrohitth/batch-analytics-platform`  
**Type:** Data Engineering / Production  
**Status:** Production  
**Language:** Python 3.11+ | Airflow DAGs | dbt

---

## What It Is

A production-grade batch data analytics platform processing synthetic ecommerce event data. Demonstrates modern ELT (Extract, Load, Transform) practices with a focus on **data deduplication** in high-volume event streams.

---

## Problem It Solves

Without proper deduplication, ecommerce platforms face:
- Inflated revenue metrics (duplicate orders in financial reporting)
- Customer analytics errors (overcounted user interactions)
- Inventory management issues (duplicate stock updates)
- Compliance risks (inaccurate audit trails)

---

## Architecture

```
E-commerce Event Stream
  → Extract (Python)
  → Load (MinIO / S3-compatible object storage)
  → Transform (dbt)
  → Analytics Tables (PostgreSQL)
  → Airflow Orchestration
```

---

## Tech Stack

| Layer | Technology | Role |
|-------|-----------|------|
| Orchestration | **Apache Airflow** | DAG scheduling, SLA monitoring |
| Storage | **PostgreSQL** | Analytics tables, deduplication state |
| Object Storage | **MinIO** | S3-compatible event log storage |
| Transformation | **dbt** | SQL-based data transformation |
| Language | **Python 3.11+** | Extract, load, deduplication logic |

---

## Key Patterns

### Deduplication Logic
```python
# Fingerprint-based deduplication for event streams
def deduplicate_events(events: list[dict]) -> list[dict]:
    seen = set()
    deduped = []
    for event in events:
        fp = hash_event(event)  # content-based fingerprint
        if fp not in seen:
            seen.add(fp)
            deduped.append(event)
    return deduped
```

### Airflow DAG
```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator

with DAG("batch_analytics", sla=timedelta(hours=2)) as dag:
    extract = PythonOperator(task_id="extract_events", ...)
    load = PythonOperator(task_id="load_to_minio", ...)
    dedup = PythonOperator(task_id="deduplicate", ...)
    transform = dbtRunOperator(task_id="dbt_transform", ...)
    
    extract >> load >> dedup >> transform
```

---

**Cross-links:**
→ [../index.md](../index.md) — Wiki central  
→ [./Data_Engineering_Stack.md](./Data_Engineering_Stack.md) — Airflow + dbt stack  
→ [./CDC_Warehouse_SCD2.md](./CDC_Warehouse_SCD2.md) — Related: CDC + SCD Type 2 project  
→ [../patterns/cdc-pipeline.md](../patterns/cdc-pipeline.md) — CDC pipeline pattern