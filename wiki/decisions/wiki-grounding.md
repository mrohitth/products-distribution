# Wiki Grounding — /wiki as Authoritative Source

**Date:** 2026-05-03  
**Decision by:** Mathew  
**Status:** ✅ LIVE

---

## Context

Every agent in the crew — Kitty, Witty, Mitty, Bitty, Titty — must use `/wiki` as the authoritative source for all data engineering facts.

---

## The Rule

**If it's not documented in `/wiki`, it didn't happen.**

When any agent generates or verifies code, architecture, or technical decisions:
1. Check `/wiki` for existing entries
2. If the information isn't in `/wiki`, create an entry first
3. Cross-link related entries to build the knowledge graph

---

## Why This Matters

The workspace contains multiple sources of truth: daily logs, MEMORY.md, session transcripts, and `/wiki`. Of these, only `/wiki` is designed for cross-linked, searchable, durable knowledge.

Daily logs expire. MEMORY.md is aggregate. Session transcripts are implicit. `/wiki` is explicit.

---

## Enforcement

All agent hard boundaries now include: "verify against `/wiki` first."

The Bitty Wiki Guardian runs every 15 minutes to scan for new files and ensure Correction Ledger compliance.

---

**Cross-links:**
→ [../index.md](../index.md) — Wiki central  
→ [./memory-purge.md](./memory-purge.md) — Stack standardization decision  
→ [./crew-roster-v3.md](./crew-roster-v3.md) — Agent definitions
