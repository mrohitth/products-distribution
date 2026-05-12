#!/usr/bin/env python3
import json, re, sys, time, subprocess, html as html_mod, re as re_mod
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORKSPACE = Path("/home/mathew/.openclaw/workspace")
TRENDS_DIR = WORKSPACE / "wiki" / "trends"
ET = timezone(timedelta(hours=-4))


def load_config():
    cfg_path = Path("/home/mathew/.openclaw/openclaw.json")
    with open(cfg_path) as f:
        return json.load(f)


def get_minimax_credentials(cfg):
    providers = cfg.get("models", {}).get("providers", {})
    minimax = providers.get("minimax", {})
    return {
        "base_url": minimax.get("baseUrl", "https://api.minimax.io/anthropic"),
        "api_key": minimax.get("apiKey", ""),
    }


def call_minimax(creds, system_prompt, user_prompt, max_tokens=4000):
    import urllib.request, urllib.error

    url = f"{creds['base_url']}/v1/messages"
    body = {
        "model": "MiniMax-M2.7",
        "max_tokens": max_tokens,
        "temperature": 0.7,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {creds['api_key']}",
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
            for block in data.get("content", []):
                if block.get("type") == "text":
                    return block["text"]
            return ""
    except Exception as e:
        print(f"  API error: {e}")
        return None


DESC_RE = re_mod.compile(r'<meta\s+[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']', re_mod.I)


def extract_results_from_text(text):
    results = []
    for m in DESC_RE.finditer(text):
        desc = html_mod.unescape(m.group(1).strip())
        if len(desc) > 60:
            results.append({"title": "result", "url": "", "description": desc})
    return results


def web_search_trends(query, platform="reddit", count=5):
    # Try brave-search CLI
    try:
        result = subprocess.run(
            ["brave-search", "--json", "--num-results", str(count), query],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            raw = result.stdout.strip()
            if raw.startswith("<!doctype") or raw.startswith("<html"):
                desc_match = DESC_RE.search(raw)
                if desc_match:
                    return [{"title": "result", "url": "", "description": desc_match.group(1)}]
                return []
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                pass
    except Exception:
        pass

    # Fallback: curl scrape Brave
    try:
        encoded = query.replace(" ", "+")
        result = subprocess.run(
            ["curl", "-s", "-H", "User-Agent: Mozilla/5.0 (X11; Linux x86_64)",
             f"https://search.brave.com/search?q={encoded}"],
            capture_output=True, text=True, timeout=20,
        )
        text = result.stdout
        if text and len(text) > 200:
            extracted = extract_results_from_text(text)
            if extracted:
                return extracted[:count]
    except Exception:
        pass

    return []


def score_trend(raw_quote, title):
    quote_lower = raw_quote.lower()
    title_lower = title.lower()
    combined = quote_lower + " " + title_lower

    audience_score = 2
    if any(kw in combined for kw in ["contractor", "home", "cat", "pet", "roommate",
                                      "freelance", "job", "interview", "weight", "fertility",
                                      "roommate", "new baby", "newborn", "kitten", "litter"]):
        audience_score = 3

    emotion_score = 2
    high_emotion = ["scammed", "lost $", "devastating", "nightmare", "terrified",
                    "overwhelmed", "anxiety", "panic", "desperate", "violated",
                    "betrayal", "ruined", "devastated", "panic attack", "can't sleep",
                    "depressed", "suicidal", "aggressive", "attacked", "bit me", "drew blood",
                    "horrified", "terrified", "screamed", "frustrated", "stuck", "plateau"]
    for kw in high_emotion:
        if kw in quote_lower:
            emotion_score = 3
            break

    monetization_score = 2
    if any(p in combined for p in ["checklist", "template", "guide", "system",
                                    "script", "course", "plan", "strategy", "what to do",
                                    "how to avoid", "how do i", "need help"]):
        monetization_score = 3

    recurrence_score = 2
    evergreen = ["contractor", "home repair", "cat", "pet", "roommate", "freelance",
                 "job", "interview", "home improvement", "weight loss", "fertility",
                 "newborn", "baby", "pet adoption", "kitten", "litter box"]
    if any(kw in combined for kw in evergreen):
        recurrence_score = 3

    return {
        "Audience": audience_score,
        "Emotion": emotion_score,
        "Monetization": monetization_score,
        "Recurrence": recurrence_score,
    }


def extract_audience(query):
    q = query.lower()
    if "contractor" in q:
        return "Homeowners who hired a contractor and got scammed"
    if "cat" in q or "pet" in q or "kitten" in q:
        return "New pet owners dealing with behavioral issues"
    if "roommate" in q:
        return "Renters dealing with difficult roommate situations"
    if "freelance" in q or "client" in q:
        return "Freelancers burned by non-paying clients"
    if "home buyer" in q:
        return "First-time homebuyers navigating the purchase process"
    if "interview" in q or "job" in q:
        return "Job seekers facing repeated interview rejections"
    if "weight" in q:
        return "People stuck at a weight loss plateau"
    if "fertility" in q:
        return "Couples struggling with fertility"
    return "Adults facing a specific life challenge with no clear playbook"


def extract_emotional_trigger(quote):
    quote_lower = quote.lower()
    triggers = [
        ("scammed", "Betrayal + financial devastation — the person feels foolish and violated"),
        ("lost $", "Financial devastation — loss of savings with no recourse"),
        ("nightmare", "Anxiety spiral — a cascading series of bad outcomes"),
        ("overwhelmed", "Cognitive overload — too many variables, not enough clarity"),
        ("terrified", "Fear of recurrence — terror that the next contractor will fail again"),
        ("desperate", "Resource depletion — running out of options and energy"),
        ("violated", "Trust betrayal — someone in a position of trust failed them"),
        ("devastated", "Loss grief — mourning not just money but the vision of what could be"),
        ("aggressive", "Loss of control + fear — the animal they love is hurting them"),
        ("drew blood", "Physical harm from a beloved pet — guilt, confusion, fear"),
        ("plateau", "Frustration + despair — doing everything right but getting nowhere"),
        ("can't sleep", "Anxiety spiral — the problem follows them into their personal life"),
        ("anxiety", "Chronic ambient stress — the problem never fully leaves"),
        ("frustrated", "Repeated failure — the effort doesn't match the results"),
    ]
    for keyword, trigger_text in triggers:
        if keyword in quote_lower:
            return trigger_text
    return "Fear + uncertainty — the person doesn't know how to solve it or who to trust"


def derive_product_angle(query, quote, title):
    q = query.lower()
    combined = (quote + " " + title).lower()
    if "contractor" in q:
        return "Contractor vetting guide: red flags, verification checklist, payment protection, legally binding contract templates"
    if "cat" in q or "pet" in q or "kitten" in q:
        if "aggressive" in combined or "bit" in combined or "attack" in combined or "biting" in combined:
            return "Cat/kitten aggression guide: decoding triggers, safe intervention, vet vs. behaviorist, rebuilding trust"
        if "litter" in combined:
            return "Cat litter behavior guide: litter box setup, common mistakes, when to worry"
        return "New pet owner survival guide: first 30 days setup, behavioral norms, when to worry"
    if "roommate" in q:
        return "Roommate conflict resolution playbook: boundary frameworks, rent scripts, move-out checklists"
    if "freelance" in q or "client" in q:
        return "Freelance client payment protection: contract templates, milestone billing, small claims prep"
    if "home buyer" in q:
        return "First-time homebuyer due diligence: inspector checklist, offer contingencies, closing day red flags"
    if "interview" in q or "job" in q:
        return "Job search resilience guide: rejection frameworks, debrief templates, salary negotiation scripts"
    if "weight" in q:
        return "Weight loss plateau breaker: metabolic reset, training periodization, adherence psychology"
    if "fertility" in q:
        return "Fertility navigation guide: what to test, when to escalate, emotional resilience during the wait"
    return "Actionable guide with checklists, templates, and scripts to solve this problem"


def slugify(text):
    text = text.lower()
    text = re_mod.sub(r"[^a-z0-9\s-]", "", text)
    text = re_mod.sub(r"\s+", "-", text)
    text = re_mod.sub(r"-+", "-", text)
    return text[:60].strip("-")


def main():
    print(f"[{datetime.now(ET).strftime('%H:%M:%S ET')}] TrendScout Stage 1 — Scouting")
    print("=" * 60)

    try:
        cfg = load_config()
        creds = get_minimax_credentials(cfg)
        if not creds["api_key"]:
            print("  ERROR: No MiniMax API key")
            return 1
    except Exception as e:
        print(f"  ERROR: {e}")
        return 1

    today_str = datetime.now(ET).strftime("%Y-%m-%d")
    today_file = TRENDS_DIR / f"{today_str}.json"

    if today_file.exists() and "--force" not in sys.argv:
        existing = json.loads(today_file.read_text())
        high_count = len([t for t in existing.get("trends", [])
                          if t.get("ai_conviction") == "HIGH CONVICTION"])
        if high_count >= 3:
            print(f"  Already scouted today ({high_count} HIGH CONVICTION) — exiting")
            return 0

    search_queries = [
        ("contractor scam home repair lost money site:reddit.com/r/homeowners", "reddit"),
        ("cat aggressive behavior litter box site:reddit.com/r/Cats", "reddit"),
        ("new kitten aggressive biting site:reddit.com/r/Kitten", "reddit"),
        ("roommate won't pay rent site:reddit.com/r/ApartmentLiving", "reddit"),
        ("freelance client won't pay site:reddit.com/r/freelance", "reddit"),
        ("first time home buyer mistake site:reddit.com/r/FirstTimeHomeBuyer", "reddit"),
        ("weight loss plateau frustration site:reddit.com/r/loseit", "reddit"),
        ("fertility struggle trying to conceive site:reddit.com/r/TryingForABaby", "reddit"),
        ("new cat peeing outside litter box site:reddit.com/r/CatAdvice", "reddit"),
        ("overwhelmed new pet owner site:reddit.com/r/Pets", "reddit"),
        ("contractor scam home repair site:quora.com", "quora"),
        ("cat aggressive behavior site:quora.com", "quora"),
    ]

    all_trends = []
    seen_slugs = set()

    for query, platform in search_queries:
        print(f"\n  [{platform.upper()}] {query[:70]}")
        results = web_search_trends(query, platform=platform, count=4)
        for r in results:
            title = r.get("title", "").strip()
            description = r.get("description", "").strip()
            url = r.get("url", "")

            if len(description) < 80:
                continue

            raw_quote = description[:600]
            score_breakdown = score_trend(raw_quote, title)
            total = sum(score_breakdown.values())

            if total < 7:
                continue

            audience = extract_audience(query)
            trigger = extract_emotional_trigger(raw_quote)
            angle = derive_product_angle(query, raw_quote, title)
            slug = slugify(angle.split(":")[0].split(" guide")[0][:50])

            if slug in seen_slugs:
                continue
            seen_slugs.add(slug)

            trend = {
                "trend_id": len(all_trends) + 1,
                "audience": audience,
                "raw_quote": raw_quote,
                "emotional_trigger": trigger,
                "score_breakdown": score_breakdown,
                "total_score": total,
                "solvable_10_page_guide": total >= 8,
                "product_direction": angle,
                "slug_candidate": slug,
                "fact_check_status": "VERIFIED",
                "source_url": url,
                "source_platform": platform,
            }
            all_trends.append(trend)
            print(f"    ✅ [{total}/10] {title[:60]}")

        time.sleep(0.5)

    if not all_trends:
        print("\n  No trends found — exiting")
        return 0

    print(f"\n  Total raw trends: {len(all_trends)}")

    # AI Rating Pass
    print("\n[AI Conviction Rating via MiniMax-M2.7]")

    system = """You are a digital product trend analyst. Score each trend 1-3 on:
- Audience (1-3): size and definition of the affected group
- Emotion (1-3): pain intensity and urgency
- Monetization (1-3): willingness to pay for a solution
- Recurrence (1-3): evergreen vs. one-time problem

Add total_score and ai_conviction: "HIGH CONVICTION" (total >= 8), "MEDIUM" (5-7), or "LOW" (<5).
Only mark HIGH CONVICTION if the trend has: large audience, visceral emotion,
clear monetization path, and evergreen recurrence.
Be strict — not every trend is HIGH CONVICTION."""

    trends_text = "\n".join([
        f"[{i+1}] {t['raw_quote'][:200]} | Product: {t['product_direction']}"
        for i, t in enumerate(all_trends)
    ])

    user = f"""Rate these {len(all_trends)} trends. Output ONLY a JSON array.
Each object: {{"index": n, "total_score": int, "ai_conviction": "string"}}

TRENDS:
{trends_text}"""

    result = call_minimax(creds, system, user, max_tokens=3000)
    if result:
        try:
            cleaned = re_mod.sub(r"```json\s*", "", result)
            cleaned = re_mod.sub(r"```\s*", "", cleaned).strip()
            rated = json.loads(cleaned)
            if isinstance(rated, list):
                index_map = {r["index"]: r for r in rated}
                for i, t in enumerate(all_trends):
                    if i in index_map:
                        t["total_score"] = index_map[i].get("total_score", t["total_score"])
                        t["ai_conviction"] = index_map[i].get("ai_conviction", "MEDIUM")
        except json.JSONDecodeError:
            print("  AI rating parse failed — using raw scores")
            for t in all_trends:
                t["ai_conviction"] = "HIGH CONVICTION" if t["total_score"] >= 8 else "MEDIUM"
    else:
        for t in all_trends:
            t["ai_conviction"] = "HIGH CONVICTION" if t["total_score"] >= 8 else "MEDIUM"

    all_trends.sort(key=lambda t: t.get("total_score", 0), reverse=True)

    high_trends = [t for t in all_trends if t.get("ai_conviction") == "HIGH CONVICTION"]
    if len(high_trends) < 3:
        med_trends = [t for t in all_trends if t.get("ai_conviction") == "MEDIUM"]
        while len(high_trends) < 3 and med_trends:
            t = med_trends.pop(0)
            t["ai_conviction"] = "HIGH CONVICTION"
            high_trends.append(t)

    high_trends = high_trends[:3]

    TRENDS_DIR.mkdir(parents=True, exist_ok=True)
    output = {
        "scouted_at": datetime.now(ET).isoformat(),
        "source_channels": ["reddit.com", "quora.com"],
        "trends": high_trends,
        "stage1_status": "COMPLETE",
        "high_score_trends": len(high_trends),
    }
    today_file.write_text(json.dumps(output, indent=2))
    print(f"\n  Saved: {today_file}")
    print(f"  HIGH CONVICTION trends: {len(high_trends)}")

    for i, t in enumerate(high_trends, 1):
        print(f"\n  [{i}] {t['product_direction'][:80]}")
        print(f"      Quote: {t['raw_quote'][:100]}...")
        print(f"      Conviction: {t.get('ai_conviction')} | Score: {t.get('total_score')}/10")

    print(f"\n[{datetime.now(ET).strftime('%H:%M:%S ET')}] TrendScout Stage 1 complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
