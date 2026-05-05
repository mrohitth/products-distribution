# CDC Pipeline — Change Data Capture Patterns

**Owner:** [T] Titty  
**Type:** Engineering Pattern — Data Pipeline  
**Status:** Production  
**Stack:** Python 3.x + Bash | PostgreSQL | MinIO | dbt

---

## What It Is

Change Data Capture pipelines ingest source system changes (inserts, updates, deletes) and land them into a raw zone for downstream transformation. Core building block for historical warehouse builds.

**Implementation:** Python timestamp-based CDC extraction → MinIO JSONL landing → PostgreSQL staging → dbt transforms.

---

## Pipeline Stages

```
Source PostgreSQL → Python CDC Extract → MinIO JSONL Landing
    → PostgreSQL staging → dbt incremental models → Analytics
```

---

## CDC Methods

| Method | Mechanism | Tool | Pros | Cons |
|--------|-----------|------|------|------|
| **Timestamp-Based** | Queries `updated_at > last_run_ts` | Python `psycopg2` | Simple, no CDC license needed | Misses soft deletes, needs source column |
| **Trigger-Based** | DB triggers write to shadow table | PostgreSQL trigger functions | Reliable, captured at write time | Invasive, performance overhead |
| **Log-Based** | Reads DB transaction log | Python `wal2json` extension | Captures all changes, non-invasive | Complex setup |
| **Diff-Based** | Compare current vs prior snapshot | Python hash comparison | No source changes needed | Expensive at scale |

**Preferred method:** Timestamp-based for simplicity and reliability.

---

## Raw Landing Zone Schema

```python
# cdc_extract.py — Python CDC extraction
# Output: JSONL files in MinIO
# Schema:
RawZoneRecord = {
    "cdc_operation": "INSERT" | "UPDATE" | "DELETE",
    "cdc_timestamp": "2026-05-03T10:30:00Z",
    "natural_key": "customer_12345",
    "payload": {"customer_id": 12345, "name": "Acme Corp", "updated_at": "..."},
    "batch_id": "run_20260503_1030",
    "source_table": "orders",
}
```

**Storage path:** `s3://raw-warehouse/cdc/{source_table}/{date}/{batch_id}.jsonl`

---

## Key Principles

1. **Idempotency** — Every run re-runnable with same results (use `batch_id`)
2. **Ordering** — Handle out-of-order delivery via watermark + late arrival handling
3. **Delete propagation** — Soft deletes (flag) vs hard deletes (tombstone) vs logical deletes
4. **Schema evolution** — Handle source schema changes via explicit versioning in MinIO paths
5. **SCD Type 2 merge** — Python `run_pipeline.sh` calls `merge_scd2.py` with PostgreSQL MERGE

---

## Python CDC Extraction Pattern

```python
# cdc_extract.py — timestamp-based CDC extraction
import psycopg2
import json
from datetime import datetime

def cdc_extract(table, last_run_ts, output_path):
    conn = psycopg2.connect(os.getenv("POSTGRES_CONN"))
    sql = f"""
        SELECT * FROM {table}
        WHERE updated_at > %s
        ORDER BY updated_at
    """
    with conn.cursor() as cur:
        cur.execute(sql, (last_run_ts,))
        for row in cur.fetchall():
            record = {
                "cdc_operation": "INSERT",
                "cdc_timestamp": datetime.utcnow().isoformat(),
                "natural_key": row[0],
                "payload": json.dumps(row),
                "batch_id": f"run_{datetime.utcnow().strftime('%Y%m%d_%H%M')}",
                "source_table": table,
            }
            with open(output_path, "a") as f:
                f.write(json.dumps(record) + "\n")
```

---

**Cross-links:**
→ [../index.md](../index.md) — Wiki central  
→ [./index.md](./index.md) — Patterns index  
→ [scd-type2.md](./scd-type2.md) — SCD Type 2 pattern  
→ [../projects/cdc-platform.md](../projects/cdc-platform.md) — CDC Platform project