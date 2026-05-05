# MODEL_SPECS.md — MiniMax M2.7 & DeepSeek V4 Reference

_Version 1.0 | Compiled 2026-05-05 from official docs | Kitty's operating manual_

---

## 🟢 MiniMax M2.7 — Professional Subscription (Default Workhorse)

**Source:** https://platform.minimax.io/docs/guides/models-intro
**API Ref:** https://platform.minimax.io/docs/api-reference/text-anthropic-api

### Vital Statistics

| Parameter | Value |
|-----------|-------|
| API endpoint | `https://api.minimax.io/anthropic` (Anthropic-compatible) |
| Context window | **204,800 tokens** |
| Max output | 131,072 tokens |
| Output speed | ~60 tokens/sec |
| Reasoning | ✅ Supported (thinking blocks) |
| Tool calls | ✅ Fully supported |
| Streaming | ✅ Supported |
| Temperature | (0.0, 1.0], **recommended: 1.0** |
| System prompt | ✅ Supported |

### NOT Supported
- Image input (`type="image"`) — not yet
- Document input (`type="document"`) — not yet
- `top_k`, `stop_sequences`, `service_tier`, `mcp_servers`, `context_management`, `container` — all **ignored silently**

### Prompt Caching (Anthropic API pattern)
- Uses cache-create / cache-read API
- Costs tracked in billing as `cache-create(Text API)` and `cache-read(Text API)`
- Cache tokens are cheaper than chatcompletion tokens
- Cache persists across sessions — keep system prompts stable

### Best For (Subscription — $0 marginal cost)
- ✅ All cron jobs (TrendScout, Kaizen, etc.)
- ✅ Routine conversations
- ✅ Code generation and review
- ✅ Structured output / data processing
- ✅ Any task under 204K tokens
- ✅ Enable reasoning for complex tasks
- ✅ Temperature 1.0 for creative/general, 0.3-0.7 for factual

### When NOT to use
- ❌ Tasks requiring >204K context → use DeepSeek V4
- ❌ Image/document analysis → not supported

---

## 🔵 DeepSeek V4 Pro — Pay-As-You-Go (Architect Tier)

**Source:** https://api-docs.deepseek.com/news/news260424
**Pricing:** https://api-docs.deepseek.com/quick_start/pricing
**Thinking Mode:** https://api-docs.deepseek.com/guides/thinking_mode
**Context Caching:** https://api-docs.deepseek.com/guides/kv_cache

### Vital Statistics

| Parameter | Value |
|-----------|-------|
| Architecture | 1.6T total / 49B active params |
| API endpoints | OpenAI: `https://api.deepseek.com` · Anthropic: `https://api.deepseek.com/anthropic` |
| Context window | **1,000,000 tokens (1M)** |
| Max output | **384,000 tokens** |
| Thinking mode | ✅ Default ON · reasoning_effort: `high` (default) or `max` |
| Tool calls | ✅ (must preserve reasoning_content in multi-turn) |
| JSON mode | ✅ `response_format: {type: "json_object"}` |
| FIM completion | ✅ Non-thinking mode only |
| Streaming | ✅ |

### Pricing (75% discount until 2026-05-31)

| Token Type | Price per 1M |
|------------|-------------|
| Input (cache miss) | **$1.74** |
| Input (cache hit) | **$0.0145** (99% cheaper!) |
| Output | **$3.48** |

### Thinking Mode Rules (CRITICAL)
- **Enabled by default** — toggle with `thinking: {type: "enabled/disabled"}`
- **Reasoning effort:** `high` (default) or `max` for agent tasks
- In thinking mode: `temperature`, `top_p`, `presence_penalty`, `frequency_penalty` are IGNORED (set them anyway for compat, no error)
- **Multi-turn without tool calls:** reasoning_content from prior turns is IGNORED, don't need to pass it back
- **Multi-turn WITH tool calls:** reasoning_content MUST be passed back in all subsequent turns (400 error if missing)

### Context Caching (Automatic Disk Cache)
- Enabled by default for all users — no code changes needed
- Cache persists at: request boundaries, common prefix detection, fixed token intervals
- Cache hit requires FULL prefix match (not partial)
- Cache hit is 99% cheaper than cache miss — **structure prompts for prefix reuse**
- Check hit status: `prompt_cache_hit_tokens` / `prompt_cache_miss_tokens` in usage
- Cache auto-clears after hours/days of inactivity

### Best For
- ✅ Tasks requiring >204K context (beyond MiniMax M2.7 limit)
- ✅ Deep architecture/strategy work needing maximum reasoning
- ✅ Complex agentic coding tasks
- ✅ Multi-step reasoning chains with tool calls
- ✅ When M2.7 reasoning isn't deep enough

### When NOT to use
- ❌ Routine tasks (use MiniMax — it's free on subscription)
- ❌ Simple conversations
- ❌ Tasks under 200K tokens that M2.7 handles fine

---

## 🟡 DeepSeek V4 Flash — Pay-As-You-Go (Sentinel Tier)

### Vital Statistics

| Parameter | Value |
|-----------|-------|
| Architecture | 284B total / 13B active params |
| Context window | **1,000,000 tokens (1M)** |
| Max output | 384,000 tokens |
| Thinking mode | ✅ Supports both thinking and non-thinking |
| Speed | Faster than V4 Pro |

### Pricing

| Token Type | Price per 1M |
|------------|-------------|
| Input (cache miss) | **$0.14** |
| Input (cache hit) | **$0.0028** (nearly free!) |
| Output | **$0.28** |

### Best For
- ✅ High-volume, low-complexity tasks
- ✅ 1M context at minimal cost
- ✅ Fast response time needs
- ✅ Non-thinking mode for speed, thinking for quality
- ✅ Was used for TrendScout before migration to MiniMax

---

## 📊 Routing Decision Matrix

| Task | Model | Why |
|------|-------|-----|
| Cron jobs (daily) | **MiniMax M2.7** | Subscription, $0 marginal |
| Routine chat | **MiniMax M2.7** | Default, 204K context fine |
| Code generation | **MiniMax M2.7** | Strong at coding, $0 cost |
| Deep architecture review | DeepSeek V4 Pro | Max reasoning depth |
| >204K context needed | DeepSeek V4 Pro or Flash | Only options with 1M context |
| High-volume cheap processing | DeepSeek V4 Flash | $0.14/1M input, nearly free cache |
| Agentic multi-tool chains | DeepSeek V4 Pro | Thinking mode + tool call support |
| Fallback (MiniMax fails) | V4 Pro → V4 Flash | Escalation ladder |

---

## 💡 Optimization Rules (Apply Every Prompt)

### For MiniMax M2.7:
1. **Maximize cache hits:** Keep system prompts and workspace context stable between sessions
2. **Use reasoning deliberately:** Enable when complexity warrants, skip for simple tasks
3. **Temperature tuning:** 1.0 for creative/chat, 0.5-0.7 for factual, 0.3 for code
4. **Stay under 204K tokens:** Compact before hitting the limit
5. **Compaction at 5K** keeps sessions lean — M2.7 has plenty of headroom at 204K

### For DeepSeek V4 Pro (when used):
1. **Prefix reuse is 99% cheaper:** Structure multi-turn conversations with identical prefixes
2. **Thinking mode is default ON** — disable only when speed > quality
3. **Preserve reasoning_content in tool call chains** or get 400 errors
4. **Keep thinking on for agent tasks** — reasoning_effort auto-set to max for Claude Code/OpenClaw
5. **Cache hit strategy:** First request builds cache, second+ requests benefit

### For DeepSeek V4 Flash (when used):
1. **Non-thinking mode for speed** — use when reasoning overhead isn't needed
2. **Cache hit is nearly free** ($0.0028/1M vs $0.14/1M)
3. **Good for high-volume filtering/processing** where cheap per-token cost matters

### Universal:
1. **Stable system prompts maximize cache hits across all models**
2. **When in doubt, MiniMax first** — it's already paid for
3. **DeepSeek only when:** context >204K, reasoning depth critical, or MiniMax unavailable

---

_Last updated: 2026-05-05 | Sources: minimax.io/docs, api-docs.deepseek.com_
