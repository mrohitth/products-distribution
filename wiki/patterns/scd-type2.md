# SCD Type 2 — Slowly Changing Dimensions Pattern

**Owner:** [T] Titty  
**Type:** Engineering Pattern — Data Modeling  
**Status:** Production  
**Stack:** Python 3.x + PostgreSQL MERGE + dbt

---

## What It Is

Slowly Changing Dimension Type 2 tracks complete history of dimension changes. Each change creates a new versioned row with effective date ranges. Used for historical reporting and point-in-time analysis.

**Implementation:** PostgreSQL `MERGE INTO` with Python orchestration via `run_pipeline.sh`. dbt incremental models layer on top for analytics.

---

## Schema Design

| Column | Type | Description |
|--------|------|-------------|
| `surrogate_key` | BIGSERIAL | Auto-generated PK — never reused |
| `natural_key` | VARCHAR | Business key (e.g., `customer_id`) — unique per version |
| `version_number` | INT | Monotonically increasing per natural_key |
| `attribute_name` | VARCHAR | The dimension attribute being tracked |
| `old_value` | VARCHAR | Previous value (before change) |
| `new_value` | VARCHAR | New value (current) |
| `valid_from` | TIMESTAMP | When this version became active |
| `valid_to` | TIMESTAMP | When this version was superseded (NULL = current) |
| `is_current` | CHAR(1) | 'Y' = active, 'N' = expired |

---

## Key Behavior

| Scenario | Behavior |
|-----------|----------|
| **New record** | Insert with `version_number=1`, `is_current='Y'` |
| **Attribute change** | Set `valid_to=NOW()`, `is_current='N'`; insert new row with incremented `version_number` |
| **No change** | Leave existing current row unchanged |
| **Point-in-time query** | `WHERE valid_from <= :as_of AND (valid_to > :as_of OR valid_to IS NULL)` |

---

## PostgreSQL MERGE (Python/Bash)

```python
# merge_scd2.py — SCD Type 2 merge into PostgreSQL
import psycopg2

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

## dbt Incremental Model

```sql
-- models/staging/dim_orders_scd2.sql
{{ config(
    materialied='incremental',
    unique_key='natural_key',
    on_schema_change='sync_all_columns'
) }}

WITH source AS (
    SELECT natural_key, new_value, valid_from,
        ROW_NUMBER() OVER (
            PARTITION BY natural_key
            ORDER BY valid_from DESC
        ) AS rn
    FROM {{ source('raw_warehouse', 'cdc_orders') }}
    {% if is_incremental() %}
    WHERE valid_from > (SELECT MAX(valid_from) FROM this)
    {% endif %}
)

SELECT natural_key, version_number, new_value, valid_from, valid_to, is_current
FROM source WHERE rn = 1
```

---

## Anti-Patterns

- ❌ Using `valid_to = '9999-12-31'` instead of `NULL` for current — breaks point-in-time queries
- ❌ Reusing surrogate keys — violates uniqueness
- ❌ Allowing `natural_key` to be NULL — breaks join logic
- ❌ Skipping the MERGE and doing INSERT-only — creates duplicate versions

---

**Cross-links:**
→ [../index.md](../index.md) — Wiki central  
→ [./index.md](./index.md) — Patterns index  
→ [./cdc-pipeline.md](./cdc-pipeline.md) — CDC pipeline pattern  
→ [../projects/cdc-platform.md](../projects/cdc-platform.md) — CDC Platform project