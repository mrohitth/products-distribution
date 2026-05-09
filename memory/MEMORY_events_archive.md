# Memory Events Archive

_Last updated: 2026-05-09_

### MiniMax Professional Subscription — Activated
- **Date:** 2026-05-05 · **Model:** MiniMax-M2.7 (reasoning, 200K context) · **Role:** T2 Workhorse
- **Highspeed removed** — no longer in subscription; all traces purged from config and docs
- **New primary model:** `minimax/MiniMax-M2.7` with reasoning enabled
- **New fallback chain:** MiniMax-M2.7 → DeepSeek V4 Pro → DeepSeek V4 Flash

### Bitty Local Engine — Setup Complete
- **Binary:** `~/.local/bin/ollama` v0.22.1 · **Model:** `llama3.2:3b` (Q4_K_M, ~2GB)  
- **Model path:** `/run/media/mathew/OS/ollama/models/` · **Privacy Engine:** `bitty_core.py`
- **RAM Threshold:** 70% · **API:** `http://127.0.0.1:11434`
- **GPU note:** GTX 1650 Ti 4GB VRAM CC 7.5 — GPU acceleration inactive (CPU only, /tmp disk quota issue)

### Mitty Security Audit — Enabled
- **Cron ID:** `ab1be4b3-4dc0-46fd-b185-058fc4847ec6` · **Schedule:** `0 23 * * *` (11 PM Eastern)
- **Delivery:** announce → `telegram:5607383477` · **Payload:** Full SSH/firewall/gateway/cron/ram/filesystem audit

---