# Data Observability Platform

**Owner:** [T] Titty  
**Repo:** `mrohitth/data-observability-platform`  
**Type:** Data Engineering / Production  
**Status:** Production  
**Language:** Python | SQL | CI/CD

---

## What It Is

A configuration-driven data observability engine that **detects statistical anomalies** based on dynamic historical baselines and generates actionable alerts. Integrates into CI/CD reliability pipelines.

---

## Problem It Solves

Silent data failures are the most dangerous threat to data reliability. Data quality issues propagate undetected for days, corrupting analytics, ML models, and business decisions.

**Silent failures addressed:**
- Empty/correctly-structured-but-wrong data (ETL success = false security)
- Schema drift (source systems change without notification)
- Stale data (dashboards show outdated information)
- Volume anomalies (sudden drops indicate upstream failures)
- Quality degradation (slow drift over time)

---

## Architecture

```
Data Source → Pipeline → [Monitors] → Observability Engine → Alerting

Monitors check:
  - Volume (row count vs historical baseline)
  - Schema (contract validation)
  - Distribution (null %, unique count, z-score)
  - Freshness (data age)
```

---

## Key Capabilities

### Dynamic Baselines
Continuously calculates historical baselines (mean, σ) for each metric — adapts to seasonality.

### Z-Score Anomaly Detection
3σ threshold identifies statistically significant deviations.

### Data Contract Validation
Enforces schema contracts to catch drift before it impacts consumers.

### Alert Deduplication
Prevents alert fatigue — intelligent grouping + contextual enrichment.

### CI/CD Integration
```yaml
pipeline.yaml
  monitors:
    - table: orders
      metrics:
        - row_count: zscore_threshold=3
        - null_pct: threshold=0.05
        - freshness: max_age_minutes=30
```

---

## Industry Use Cases

| Industry | Problem Detected |
|----------|-----------------|
| E-commerce | Order processing failures before revenue loss |
| Financial Services | Regulatory reporting data integrity |
| Healthcare | Patient data quality for critical systems |
| Analytics Platforms | ML training data reliability |

---

**Cross-links:**
→ [../index.md](../index.md) — Wiki central  
→ [./Data_Engineering_Stack.md](./Data_Engineering_Stack.md) — Observability stack  
→ [./projects/index.md](./projects/index.md) — All projects  
→ [../patterns/scd-type2.md](../patterns/scd-type2.md) — Related: data quality patterns