# Model Switch — Chief of Staff to Sonnet 3.5

**Date:** 2026-05-03  
**Decision by:** Mathew  
**Status:** ✅ APPROVED

## Changes Made

| Item | Before | After |
|------|--------|-------|
| Chief of Staff model | MiniMax M2.7 | Claude Sonnet 3.5 |
| Bitty RAM threshold | 80% | 70% |

## Why

Mathew approved the model switch after pre-validation of all agents completed successfully:
- **Witty [W]:** ✅ Wiki decision entry created, index updated
- **Mitty [M]:** ✅ Mini-audit passed — all checks CLEAN (0 failed logins, 3 crons verified, no credential exposure, RAM 49.8%)
- **Bitty [B]:** ⏳ Test pending (in progress)

## Sonnet's First Tasks

1. Verify Bitty's MEMORY_THRESHOLD = 70% in `bitty_core.py`
2. Confirm $25/mo budget monitoring is active (check `/api/usage` or OPERATING.md)
3. Log this session handover in MEMORY.md

## Cross-Links
→ [../../MEMORY.md](../../MEMORY.md) — Hybrid Swarm Actions section  
→ [../index.md](../index.md) — Wiki central
