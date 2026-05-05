# Memory Purge — Stack Standardization

**Date:** 2026-05-03  
**Decision by:** Mathew  
**Status:** ✅ Standardized

---

## Context

The workspace was originally populated with broad "professional stack" entries referencing technologies that are not part of the actual implementation.

---

## What Was Done

Standardized architecture on **Python/Postgres/dbt stack** for performance, observability, and cost-efficiency.

All data engineering documentation now reflects:
- **Python 3.x + Bash** for CDC extraction and ETL
- **PostgreSQL** for warehouse and dimension tables
- **dbt** for SQL incremental transformations
- **Airflow** for orchestration
- **MinIO** for S3-compatible object storage

---

**Cross-links:**
→ [../index.md](../index.md) — Wiki central  
→ [./wiki-grounding.md](./wiki-grounding.md) — Wiki as authoritative source