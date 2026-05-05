#!/usr/bin/env python3
"""
MarketBot Feedback Loop — Capital Pilot Integration
====================================================
Captures sales data from Lemon Squeezy webhooks and
instructs the Scout agent (Stage 1) to prioritize based
on product performance.

Architecture:
  Flask/FastAPI webhook listener → parses sale events →
  updates sales performance log → triggers Stage 1 re-score
  with performance-weighted trend prompts.

Run: python3 scripts/marketbot_feedback.py [--port 5000]
"""
import json, os, sys, sqlite3, time
import subprocess as _subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from functools import wraps

# ─── CONFIG ──────────────────────────────────────────────────────────────────
WORKSPACE = Path("/home/mathew/.openclaw/workspace")
SALES_DB   = WORKSPACE / "output" / "sales_performance.db"
TRENDS_DIR = WORKSPACE / "wiki" / "trends"
SPOKE_SESSION = "spoke-marketbot"  # session key for Stage 1 Scout agent

ET = timezone(timedelta(hours=-4))

# ─── DATABASE ────────────────────────────────────────────────────────────────

def init_db():
    """Create the sales performance table if it doesn't exist."""
    SALES_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(SALES_DB))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sales_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id    TEXT UNIQUE NOT NULL,
            product_slug TEXT NOT NULL,
            product_name TEXT,
            variant_name TEXT,
            amount_cents INTEGER,
            currency    TEXT DEFAULT 'USD',
            customer_email TEXT,
            country     TEXT,
            created_at  TEXT,
            source      TEXT,
            created_at_ts TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS product_stats (
            product_slug  TEXT PRIMARY KEY,
            product_name  TEXT,
            total_sales   INTEGER DEFAULT 0,
            total_revenue_cents INTEGER DEFAULT 0,
            top_country   TEXT,
            updated_at    TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scout_signals (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            product_slug TEXT NOT NULL,
            signal_type  TEXT NOT NULL,
            strength     REAL DEFAULT 0.5,
            created_at   TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)
    conn.commit()
    conn.close()


def upsert_sale(event: dict) -> bool:
    """Write a sale event to the DB. Returns True if new, False if duplicate."""
    order_id    = event.get("meta", {}).get("id", "")
    data        = event.get("data", {})
    attrs       = data.get("attributes", {})

    product_slug = attrs.get("first_order_item", {})
    # Lemon Squeezy structure varies; normalize
    item = attrs.get("first_order_item", {}) or {}
    variant_name = item.get("variant_name", "")
    amount_cents = attrs.get("total", 0)   # total in cents
    currency     = attrs.get("currency", "USD")
    customer_email = attrs.get("user", {}).get("email", "") if isinstance(attrs.get("user"), dict) else ""
    country      = attrs.get("user", {}).get("address", {}).get("country", "") if isinstance(attrs.get("user"), dict) else ""
    created_at   = attrs.get("created_at", "")

    # Product lookup from slug map
    slug_map = {
        "you-first-for-once": "single_parent_teen_burnout_V1",
        "no-shame-saturday":  "single_parent_teen_burnout_V1",
        "off-switch":         "off_switch_V1",
    }
    product_name = attrs.get("product_name", "")
    product_key  = next((k for k in slug_map if k in (product_name or "").lower()), "")

    conn = sqlite3.connect(str(SALES_DB))
    try:
        conn.execute("""
            INSERT INTO sales_log (order_id, product_slug, product_name, variant_name,
                                   amount_cents, currency, customer_email, country, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (order_id, product_key, product_name, variant_name, amount_cents,
              currency, customer_email, country, created_at))
        conn.commit()
        new = True
    except sqlite3.IntegrityError:
        new = False
    conn.close()
    return new


def update_product_stats(product_slug: str, amount_cents: int, country: str):
    """Increment running totals for a product."""
    conn = sqlite3.connect(str(SALES_DB))
    cur = conn.execute("""
        SELECT total_sales, total_revenue_cents FROM product_stats
        WHERE product_slug = ?
    """, (product_slug,))
    row = cur.fetchone()
    if row:
        conn.execute("""
            UPDATE product_stats
            SET total_sales = total_sales + 1,
                total_revenue_cents = total_revenue_cents + ?,
                updated_at = datetime('now', 'localtime')
            WHERE product_slug = ?
        """, (amount_cents, product_slug))
    else:
        conn.execute("""
            INSERT INTO product_stats (product_slug, total_sales, total_revenue_cents)
            VALUES (?, 1, ?)
        """, (product_slug, amount_cents))
    conn.commit()
    conn.close()


def write_scout_signal(product_slug: str, signal_type: str = "sales_burst", strength: float = 1.0):
    """Write a scout signal to bias Stage 1 research toward a topic."""
    conn = sqlite3.connect(str(SALES_DB))
    conn.execute("""
        INSERT INTO scout_signals (product_slug, signal_type, strength)
        VALUES (?, ?, ?)
    """, (product_slug, signal_type, strength))
    conn.commit()
    conn.close()


# ─── GITHUB ACTION TRIGGER ───────────────────────────────────────────────────

def trigger_scout_refresh():
    """
    Phase 3: Signal the Scout agent to re-score trends with sales performance weighting.

    Uses the existing TrendScout pattern: writes a performance-weighted prompt
    modifier to wiki/trends/.scout_context, then optionally triggers a new Scout run.

    The Stage 1 Scout agent reads .scout_context at startup and biases its
    trend research accordingly.
    """
    conn = sqlite3.connect(str(SALES_DB))
    cur = conn.execute("""
        SELECT product_slug, total_sales, total_revenue_cents
        FROM product_stats ORDER BY total_sales DESC LIMIT 3
    """)
    top_products = cur.fetchall()
    conn.close()

    if not top_products:
        return  # No data yet — Scout runs on normal schedule

    # Build the context modifier from sales data
    lines = [
        "# Scout Context Override — Sales Performance",
        f"# Updated: {datetime.now(ET).strftime('%Y-%m-%d %H:%M ET')}",
        "",
        "## Top-Converting Products (bias research toward these sub-niches)",
    ]
    for slug, sales, revenue in top_products:
        lines.append(f"- **{slug}**: {sales} sales, ${revenue/100:.2f} revenue")

    lines.append("")
    lines.append("## Scout Prioritization Instructions")
    lines.append("When scoring new trend candidates, apply a 1.5× multiplier to")
    lines.append("sub-niches of the top-selling product. Example: if 'Caregiver")
    lines.append("Burnout' is top-converting, Stage 1 should flag 'Elder Care")
    lines.append("Burnout,' 'Compassion Fatigue,' and 'Caregiver Identity Loss'")
    lines.append("at 1.5× the base score for equivalent raw frustration signals.")
    lines.append("")
    lines.append("If no products have sales data yet, operate on normal TrendScout")
    lines.append("protocol (frustration score > 8/10 = HIGH CONVICTION).")

    context_path = TRENDS_DIR / ".scout_context"
    context_path.write_text("\n".join(lines))

    print(f"  [MarketBot] Scout context updated from {len(top_products)} products")
    print(f"  [MarketBot] Top product: {top_products[0][0] if top_products else 'none'}")


# ─── WEBHOOK LISTENER ────────────────────────────────────────────────────────

def build_app():
    """FastAPI/Flask app for Lemon Squeezy webhooks + GitHub Action handler."""
    try:
        from fastapi import FastAPI, Request, HTTPException
        from fastapi.responses import JSONResponse
        import uvicorn
        app = FastAPI(title="MarketBot Feedback Loop")
    except ImportError:
        # Fallback to Flask
        from flask import Flask, request, jsonify
        app = Flask("MarketBot")
        use_fastapi = False
    else:
        use_fastapi = True

    init_db()

    # ── Lemon Squeezy webhook ────────────────────────────────────────────────
    async def handle_ls_sale(request: Request):
        """Capture 'order_created' from Lemon Squeezy."""
        if use_fastapi:
            raw_body = await request.body()
        else:
            raw_body = request.get_data()

        try:
            event = json.loads(raw_body)
        except json.JSONDecodeError:
            if use_fastapi:
                raise HTTPException(400, "Invalid JSON")
            return jsonify({"error": "Invalid JSON"}), 400

        event_name = event.get("meta", {}).get("event_name", "")
        if event_name != "order_created":
            return {"status": "ignored", "event": event_name}

        new = upsert_sale(event)
        if not new:
            return {"status": "duplicate"}

        attrs = event.get("data", {}).get("attributes", {})
        amount = attrs.get("total", 0)
        item = attrs.get("first_order_item", {}) or {}
        product_name = attrs.get("product_name", "")
        slug_map = {
            "you-first-for-once": "single_parent_teen_burnout_V1",
            "no-shame-saturday":  "single_parent_teen_burnout_V1",
            "off-switch":         "off_switch_V1",
        }
        product_key = next((k for k in slug_map if k in (product_name or "").lower()), product_name)
        country = ""
        user_data = attrs.get("user", {})
        if isinstance(user_data, dict):
            country = user_data.get("address", {}).get("country", "")

        update_product_stats(product_key, amount, country)

        # Trigger Scout refresh on every sale (throttle via DB dedup in production)
        trigger_scout_refresh()

        return {"status": "recorded", "order": event.get("meta", {}).get("id")}

    if use_fastapi:
        @app.post("/api/webhooks/lemonsqueezy")
        async def ls_webhook(request: Request):
            return await handle_ls_sale(request)

        @app.get("/api/sales/stats")
        async def sales_stats():
            conn = sqlite3.connect(str(SALES_DB))
            conn.row_factory = sqlite3.Row
            cur = conn.execute("SELECT * FROM product_stats ORDER BY total_sales DESC")
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()
            return {"products": rows}

        @app.get("/api/sales/signals")
        async def scout_signals():
            conn = sqlite3.connect(str(SALES_DB))
            conn.row_factory = sqlite3.Row
            cur = conn.execute("SELECT * FROM scout_signals ORDER BY created_at DESC LIMIT 20")
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()
            return {"signals": rows}
    else:
        @app.route("/api/webhooks/lemonsqueezy", methods=["POST"])
        def ls_webhook():
            import asyncio
            return asyncio.run(handle_ls_sale(request))

        @app.route("/api/sales/stats", methods=["GET"])
        def sales_stats():
            conn = sqlite3.connect(str(SALES_DB))
            conn.row_factory = sqlite3.Row
            cur = conn.execute("SELECT * FROM product_stats ORDER BY total_sales DESC")
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()
            return jsonify({"products": rows})

    return app, use_fastapi


# ─── STANDALONE EXECUTION ────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="MarketBot Feedback Loop")
    parser.add_argument("--port", type=int, default=5000, help="Webhook listener port")
    parser.add_argument("--test-sale", metavar="SLUG", help="Simulate a test sale for SLUG")
    args = parser.parse_args()

    if args.test_sale:
        init_db()
        update_product_stats(args.test_sale, 2700, "US")
        write_scout_signal(args.test_sale, "test_injection", 1.0)
        trigger_scout_refresh()
        print(f"  ✅ Test sale injected for '{args.test_sale}'")
        sys.exit(0)

    print(f"[{datetime.now(ET).strftime('%H:%M:%S ET')}] MarketBot Feedback Loop starting...")
    init_db()
    print(f"  Database: {SALES_DB}")
    print(f"  Webhook: http://localhost:{args.port}/api/webhooks/lemonsqueezy")

    app, use_fastapi = build_app()

    if use_fastapi:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=args.port)
    else:
        app.run(host="0.0.0.0", port=args.port, debug=False)