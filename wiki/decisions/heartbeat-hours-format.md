# Heartbeat Hours Format — Countdown Shows Hours When > 60 Minutes

**Date:** 2026-05-03  
**Agents:** [K] Kitty  
**Trigger:** User feedback: heartbeat countdown should be human-readable for longer durations

---

## Context

Heartbeat is scheduled every 30 minutes. When the next run is > 60 minutes away, showing `MM:SS` is not useful — showing `2:45:30h` is immediately clearer.

## Options Considered

- **Option A (kept):** Always show `MM:SS` — inconsistent when > 60 min
- **Option B (chosen):** Show hours when diff > 3600s: `2:45:30h` else `MM:SS`

## Decision Made

`formatCountdown(diff)` function:
- `diff <= 0` → `00:00`
- `diff > 3600s (1h)` → `H:MM:SS` format with `h` suffix: `2:45:30h`
- `diff <= 3600s` → `MM:SS` padded: `45:30`

## Implementation

```typescript
function formatCountdown(diffMs: number): string {
  if (diffMs <= 0) return "00:00";
  const totalSec = Math.floor(diffMs / 1000);
  const h = Math.floor(totalSec / 3600);
  const m = Math.floor((totalSec % 3600) / 60);
  const s = totalSec % 60;
  if (h > 0) {
    return `${h}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}h`;
  }
  return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}
```

## Affected Files

- `katzen/app/(main)/projects/page.tsx` — Scheduler countdown
- (Also in `command-bar.tsx` if it has its own countdown logic)

---

**Cross-links:**
→ [../index.md](../index.md) — Wiki central  
→ [../decisions/index.md](./index.md) — Decisions index  
→ [portfolio-pl-card.md](./portfolio-pl-card.md) — Related decision: same UX sweep  
→ [../projects/katzen.md](../projects/katzen.md) — KATZEN project