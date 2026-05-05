# CDC Warehouse — SCD Type 2 Implementation

**Owner:** [T] Titty  
**Type:** Data Engineering / ETL  
**Status:** Production  
**Tech Stack:** Python 3.x + Bash | PostgreSQL | MinIO (S3-compatible) | dbt | Airflow

---

## What It Is

End-to-end Change Data Capture platform that builds historical warehouse views with temporal SCD Type 2 modeling. Uses timestamp-based CDC extraction with Python + PostgreSQL for lean, cost-efficient transformations.

**GitHub:** `mrohitth/cdc-historical-warehouse-platform`  
**Pattern:** Python + Bash + PostgreSQL + MinIO + dbt

---

## Architecture

```
Source PostgreSQL → Python CDC Extract → MinIO JSONL Landing
    → Python SCD Type 2 Merge → PostgreSQL dim_orders_history
    → dbt transformation layer → Analytics
```

**Orchestration:** `run_pipeline.sh` — Bash script with signal handling (SIGTERM, SIGINT) for graceful Airflow DAG termination.

---

## SCD Type 2 Overview

Slowly Changing Dimension Type 2 tracks complete history of dimension changes with effective date ranges.

| Concept | Description |
|---------|-------------|
| **Surrogate Key** | BIGSERIAL — auto-generated sequential ID, never reused |
| **Natural Key** | Business key (e.g., `customer_id`) |
| **Version Number** | Monotonically increasing per natural key |
| **Effective Date** | `valid_from` — when this version became active |
| **Expiration Date** | `valid_to` — NULL = current |
| **Current Flag** | `is_current` — 'Y' for active, 'N' for expired |

---

## Correct Stack

- **CDC Detection:** Timestamp-based (`WHERE updated_at > last_run`)
- **Processing:** Python 3.x (`psycopg2`, `boto3` for MinIO)
- **Transport:** JSON change logs on filesystem (MinIO)
- **Target:** PostgreSQL dimensional table
- **Orchestration:** Bash `run_pipeline.sh`
- **Transformation:** dbt incremental models
- **Monitoring:** Airflow SLA monitoring + z-score anomaly detection

---

## SCD Type 2 in Python

```python
# merge_scd2.py — PostgreSQL MERGE for SCD Type 2
import psycopg2
import json
from datetime import datetime

MERGE_SQL = """
MERGE INTO dim_orders AS target
USING (SELECT %s AS natural_key, %s AS new_value, %s AS valid_from) AS source
ON target.natural_key = source.natural_key AND target.is_current = 'Y'
WHEN MATCHED AND target.new_value != source.new_value THEN
  UPDATE SET valid_to = source.valid_from, is_current = 'N'
WHEN NOT MATCHED THEN
  INSERT (natural_key, version_number, new_value, valid_from, valid_to, is_current)
  VALUES (source.natural_key, 1, source.new_value, source.valid_from, NULL, 'Y');
"""

def merge_record(natural_key, new_value, valid_from):
    conn = psycopg2.connect(os.getenv("POSTGRES_CONN"))
    with conn.cursor() as cur:
        cur.execute(MERGE_SQL, (natural_key, new_value, valid_from))
    conn.commit()
```

---

## run_pipeline.sh

```bash
#!/bin/bash
set -euo pipefail

BATCH_ID="run_$(date +%Y%m%d_%H%M%S)"
LAST_RUN=$(cat /var/state/last_run.watermark || echo "1970-01-01")

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

trap 'log "SIGTERM — finishing batch"; exit 0' SIGTERM
trap 'log "SIGINT — aborting"; exit 1' SIGINT

log "CDC pipeline — batch: $BATCH_ID"

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

## dbt Incremental Model

```sql
-- models/staging/dim_orders_scd2.sql
{{ config(
    materialized='incremental',
    unique_key='natural_key',
    on_schema_change='sync_all_columns'
) }}

WITH source AS (
    SELECT natural_key, new_value, valid_from,
        ROW_NUMBER() OVER (PARTITION BY natural_key ORDER BY valid_from DESC) AS rn
    FROM {{ source('raw_warehouse', 'cdc_orders') }}
    {% if is_incremental() %}
    WHERE valid_from > (SELECT MAX(valid_from) FROM this)
    {% endif %}
)
SELECT natural_key, version_number, new_value, valid_from, valid_to, is_current
FROM source WHERE rn = 1
```

---

**Cross-links:**
→ [../index.md](../index.md) — Wiki central  
→ [../patterns/scd-type2.md](../patterns/scd-type2.md) — SCD Type 2 pattern  
→ [../patterns/cdc-pipeline.md](../patterns/cdc-pipeline.md) — CDC pipeline pattern  
→ [../projects/index.md](../projects/index.md) — Projects index