# CDC Platform — Change Data Capture & Historical Warehouse

**Owner:** [T] Titty  
**Type:** Data Engineering / ETL  
**Status:** Production  
**Stack:** Python 3.x + Bash | PostgreSQL | MinIO | dbt

---

## What It Is

End-to-end Change Data Capture platform with temporal SCD Type 2 modeling. Builds historical warehouse views from source system change streams using timestamp-based CDC extraction and PostgreSQL MERGE for dimension versioning.

**GitHub:** `mrohitth/cdc-historical-warehouse-platform`

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Extraction** | Python `psycopg2` + Bash | Timestamp-based CDC extraction |
| **Storage** | MinIO (S3-compatible) | JSONL raw landing zone |
| **Transformation** | Python `merge_scd2.py` | SCD Type 2 merge logic |
| **Warehouse** | PostgreSQL | dim_orders_history, fact tables |
| **Orchestration** | `run_pipeline.sh` (Bash) | Pipeline scheduling and signal handling |
| **Transformation layer** | dbt | SQL incremental models |

---

## SCD Type 2 Overview

Slowly Changing Dimension Type 2: tracks full history of dimension changes with effective date ranges.

| Concept | Description |
|---------|-------------|
| **Surrogate Key** | BIGSERIAL — auto-generated sequential ID, never reused |
| **Natural Key** | Business key (e.g., `customer_id`) |
| **Version Number** | Monotonically increasing per natural key |
| **Effective Date** | `valid_from` — when this version became active |
| **Expiration Date** | `valid_to` — NULL = current |
| **Current Flag** | `is_current` — 'Y' for active, 'N' for expired |

---

## Architecture Pattern

```
Source PostgreSQL → Python CDC Extract → MinIO JSONL Landing
    → Python merge_scd2.py (SCD Type 2 merge)
    → PostgreSQL dim_orders_history
    → dbt transformation layer
    → Analytics
```

**Orchestration:** `run_pipeline.sh` — Bash script with signal handling (SIGTERM, SIGINT) for graceful Airflow DAG termination.

---

## Key Decisions

- **Merge strategy:** PostgreSQL `MERGE INTO` with `WHEN MATCHED UPDATE` for versioned updates
- **Expiry logic:** On new version, set `valid_to = CURRENT_TIMESTAMP - 1ms`
- **Null handling:** Natural keys never null; surrogate keys never conflict
- **Backfill:** Historical backfill uses `batch_id` for idempotent reprocessing
- **Delete handling:** Logical deletes via `is_deleted = 'Y'` flag

---

## run_pipeline.sh

```bash
#!/bin/bash
set -euo pipefail

BATCH_ID="run_$(date +%Y%m%d_%H%M%S)"
LAST_RUN=$(cat /var/state/last_run.watermark || echo "1970-01-01")

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

trap 'log "SIGTERM received — finishing current batch"; exit 0' SIGTERM
trap 'log "SIGINT received — aborting"; exit 1' SIGINT

log "Starting CDC pipeline — batch: $BATCH_ID"

python3 cdc_extract.py \
    --last-run "$LAST_RUN" \
    --output "s3://raw-warehouse/cdc/orders/$(date +%Y/%m/%d)/${BATCH_ID}.jsonl"

python3 merge_scd2.py \
    --source "s3://raw-warehouse/cdc/orders/$(date +%Y/%m/%d)/${BATCH_ID}.jsonl" \
    --target dim_orders_history

date +%Y-%m-%d\ %H:%M:%S > /var/state/last_run.watermark

log "CDC pipeline complete — batch: $BATCH_ID"
```

---

**Cross-links:**
→ [../patterns/scd-type2.md](../patterns/scd-type2.md) — SCD Type 2 pattern  
→ [../patterns/cdc-pipeline.md](../patterns/cdc-pipeline.md) — CDC pipeline pattern  
→ [./batch-analytics.md](./batch-analytics.md) — Batch Analytics platform  
→ [../index.md](../index.md) — Wiki central  
→ [./index.md](./index.md) — Projects index