# Email Monetization Funnel — "You First, For Once"

## Overview

This document describes the end-to-end email monetization funnel for the "You First, For Once: The Single Parent's Survival Guide" product ($27 PDF + $7 order bump).

---

## Funnel Flow

```
LEAD MAGNET (free checklist)
       ↓
EMAIL CAPTURE PAGE (capture_page.html)
  → email opt-in form
  → redirects to thank_you.html on submit
       ↓
THANK YOU PAGE (thank_you.html)
  → sets expectation: 3 emails over 8 days
  → teasers for the full guide
       ↓
WELCOME EMAIL SEQUENCE (you-first-for-once_email_sequence.md)
  → Email 1: Day 2 — insight from the guide
  → Email 2: Day 5 — parent story
  → Email 3: Day 8 — full guide offer ($27)
       ↓
POST-PURCHASE SEQUENCE (post_purchase_emails.md)
  → Email 1 (Day 0): Thank you + deliver PDF + Notion template bump
  → Email 2 (Day 3): Useful tip (20% Rule) + Notion template bridge
  → Email 3 (Day 7): Soft upsell for Notion template ($17)
```

---

## File Map

| File | Purpose |
|------|---------|
| `distro/email/you-first-for-once_lead_magnet.md` | The free 21-point checklist PDF content |
| `distro/email/you-first-for-once_email_sequence.md` | 5-email welcome sequence (pre-purchase) |
| `distro/email/capture_page.html` | Email capture landing page |
| `distro/email/thank_you.html` | Post-opt-in thank you / "check your inbox" page |
| `distro/email/post_purchase_emails.md` | 3-email post-purchase sequence |
| `distro/manifest/state.json` | Email lead counter (update on capture) |

---

## Lemon Squeezy Webhook — Email Capture

To track email opt-ins and trigger the welcome sequence via Lemon Squeezy:

### 1. Configure the Webhook

In your Lemon Squeezy dashboard → Product → Webhooks, add an endpoint:

```
https://yourdomain.com/api/lemon-squeezy-webhook
```

Or use a middleware service like **Webhook.site**, **Pipedream**, or **Woodstack** to forward events to your email service provider (ESP).

### 2. Event to Listen For

Subscribe to the **`order_created`** or **`checkout_completed`** event.

For **email capture only** (lead magnet opt-in), you'll need a separate capture mechanism (e.g., a form on the capture page that submits to your ESP directly). Lemon Squeezy webhooks fire on purchases, not opt-ins.

### 3. ESP Integration Options

| Provider | How to connect |
|----------|---------------|
| **Mailchimp** | Use Zapier/Make to connect LS webhook → Mailchimp audience add |
| **ConvertKit** | LS webhook → Zapier → ConvertKit form subscriber |
| **Beehiiv** | LS webhook → Zapier → Beehiiv API add subscriber |
| **Buttondown** | LS webhook → Pipedream → Buttondown API |
| **Resend** | Custom integration via Pipedream or a serverless function |
| **Klaviyo** | LS webhook → Klaviyo create/update profile |

### 4. Minimal Zapier/Make Setup (Example)

```
Lemon Squeezy Webhook (checkout_completed)
  → Filter: product_id = "YOUR_LEAD_MAGNET_PRODUCT_ID"
  → Add Subscriber to Mailchimp (status: subscribed, tag: "lead_magnet")
```

### 5. state.json Counter Update

When the webhook fires and a new subscriber is added to your ESP, increment the counter in `distro/manifest/state.json`:

```json
{
  "email_leads": 123,
  "last_capture": "2026-05-06T12:00:00Z"
}
```

---

## Deliverability Best Practices

### Authentication (Must-Do)
- **SPF:** Authorize Lemon Squeezy / your sending domain to send emails on your behalf
- **DKIM:** Enable DKIM signing in your ESP (most major providers do this automatically)
- **DMARC:** Set policy to `quarantine` or `reject` at minimum (`p=quarantine; rua=mailto:your@email.com`)

### List Hygiene
- **No purchased lists.** Ever.会导致 reputation.
- **Double opt-in recommended** for highest deliverability — but adds friction.权衡.
- **Bounce handling:** Immediately suppress hard bounces. Your ESP handles this automatically if configured.
- **Complaint handling:** Use **Feedback Loop (FBL)** / abuse reporting — route complaints to a dedicated suppress list.

### Sending Practices
- **Warm up your IP** if using a new sending domain or dedicated IP — start slow (50-100 emails/day, increase over 4-6 weeks).
- **Rotate sending domains** if open rates drop below 15%.
- **Send frequency:** 1 email per week to cold leads (pre-purchase sequence) is fine. Post-purchase, max 2 per week including sequence.
- **Avoid spammy words** in subject lines: FREE, ACT NOW, LIMITED TIME, 100%, guarantee — use sparingly.
- **Plain-text fallback:** Include a plain-text version of each email. Many ESPs auto-generate this, but verify.
- **List unsubscribe header:** Required by CAN-SPAM and deliverable best practice — include `List-Unsubscribe` header (all major ESPs do this by default).

### Monitoring
- **Track:** Open rate (>20% is healthy for a warm audience), click rate (>5% is good), unsubscribe rate (<0.5% per send is normal)
- **Tools:** Postdrop, MXToolbox for blacklist checks; Google Postmaster for Gmail delivery
- **Gmail tabs:** Note that Gmail categorizes promotional emails separately — personal/inquiry emails have better chance of landing in Primary

### Template Design
- **Mobile-first:** ≥ 30% of your audience will read on mobile. All our templates use responsive CSS.
- **Single column layout** for maximum compatibility.
- **Images:** Keep images under 100KB each; include `alt` text; don't use images as the only way to convey content.
- **Links:** Use clearly labeled HTML links (not bare URLs); track clickthrough.

---

## Configuration Checklist

- [ ] Capture page deployed (`capture_page.html`)
- [ ] Thank you page deployed (`thank_you.html`)
- [ ] ESP account created and audience list set up
- [ ] Welcome email sequence uploaded to ESP (tags: `lead_magnet`)
- [ ] Lemon Squeezy product created for $27 guide
- [ ] Lemon Squeezy product created for $17 Notion template order bump
- [ ] Post-purchase email sequence uploaded to ESP (tags: `purchased_guide`)
- [ ] Zapier/Make webhook integration configured
- [ ] state.json `email_leads` counter wired up to webhook
- [ ] SPF/DKIM/DMARC configured for sending domain
- [ ] First test send completed (to yourself + test inbox)

---

_Generated 2026-05-06 — distro flywheel build_
