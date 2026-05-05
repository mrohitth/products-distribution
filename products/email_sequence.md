# Post-Purchase Email Sequence
## "You First, For Once" | 3-Email Sequence

**Tone:** Clinical, empathetic, smart-casual.  
**Voice:** A calm, evidence-grounded colleague who has been through this.  
**Aesthetic:** Matte-finish. No exclamation marks. No "game-changer." No emoji in body copy.

---

## Email 1 — Instant Delivery

**Trigger:** Purchase confirmed (Lemon Squeezy webhook: `order_created`)  
**Send:** Immediate (0 minutes)  
**Subject:** Your copy of "You First, For Once" — plus what to do next

**From:** `Human Infrastructure <hello@[yourdomain.com]>`  
**Reply-To:** `mathew.r.thomson@gmail.com`

---

**Body:**

---

Hi [First Name],

Your order is confirmed. Here is your permanent download link:

**[Download Your PDF](https://github.com/mrohitth/products-distribution/releases/download/v1/single_parent_teen_burnout_V1.pdf)**

This link doesn't expire and doesn't require a login.

---

**A few things before you start:**

The guide is designed to be worked, not just read. The 72-Hour Energy Audit (Part 1) is where most people get stuck — not because it's hard, but because sitting down to track your own time feels indulgent when you're already running on empty.

Don't skip it. The data it produces is the foundation for every system in the book. If you do nothing else this week, do the audit.

The No Shame Saturday Protocol starts on Page 12. If you're reading this on a Thursday or Friday, that's not a coincidence — that's your setup window.

**The one thing most people get wrong in the first week:**

They try to implement everything at once. The guide gives you a 4-week rollout for a reason. Week 1 is only the 20% Rule: one recurring task, handed off to your teen. That's it.

---

Welcome to the Human Infrastructure community.

You're not broken. You were just running a two-person system with one person's resources.

— Mathew

*P.S. If the download link doesn't work (some email clients block GitHub links), reply to this email and I'll send the file directly.*

---

## Email 2 — Day 2 Check-In

**Trigger:** 48 hours after delivery email opened (or 48h after purchase, tracked via Lemon Squeezy open pixel)  
**Send:** Day 2, ~10:00 AM recipient local time (send via scheduler, not UTC)  
**Subject:** Quick check-in — did you find your first Quick Win yet?

**From:** `Human Infrastructure <hello@[yourdomain.com]>`  
**Reply-To:** `mathew.r.thomson@gmail.com`

---

**Body:**

---

Hi [First Name],

It's been about 48 hours since your order. Wanted to check in with a focused question:

**Did you run the 72-Hour Energy Audit yet?**

Specifically — did you identify the 6–12 tasks you've been absorbing out of guilt or speed?

If yes: good. The hardest part is done. Now circle one. Just one. That's your Week 1 Quick Win.

If no: here's the short version of why it matters and why it takes 20 minutes.

The audit isn't about finding time you don't have. It's about identifying the work you've been doing invisibly — the cognitive load of managing a household where you're the only adult making decisions. Once you see it on paper, the offloading conversation with your teen becomes concrete. Not a lecture about responsibility. A practical negotiation.

The "Who Was I Before?" exercise (page 31) is the one people mention most often in replies. If you haven't gotten there yet, skip ahead. It takes 15 minutes and it resets something.

Let me know how Week 1 is going. I read every reply.

— Mathew

---

## Email 3 — Day 7 Request for Testimonial

**Trigger:** 7 days after purchase  
**Send:** Day 7, subject line personalized if open data available  
**Subject:** 7 days in — what's working?

**From:** `Human Infrastructure <hello@[yourdomain.com]>`  
**Reply-To:** `mathew.r.thomson@gmail.com`

---

**Body:**

---

Hi [First Name],

One week in. How's the No Shame Saturday holding up?

If you've done it once: you're probably noticing it's harder to stay in your closed door than you expected. That's the conditioning. The scripts in the guide are designed for the moments when the knock comes at 9:15 and your first instinct is to open it. Page 19 has the exact language for that.

If you haven't done it yet: this is your reminder. Saturday morning, closed door, 8am–noon. You don't need the guide for this part. You just need the boundary.

---

**The reason I'm asking:**

If this guide is helping you, your experience is the most honest thing I can put in front of the next person deciding whether to buy it. And I don't have a marketing team — I have you.

If you're willing to share 2–3 sentences about what changed (or what almost changed, or what you're working toward), I'll use it as a testimonial on the sales page. Anonymity is fine — "Single parent, 41, two teens" is enough context.

**The 30-second version of what I'm looking for:**

- What problem were you facing before you bought the guide?
- What did you actually do in the first week?
- What's different now (even slightly)?

You can reply directly to this email. I read everything.

If it's not working — tell me that too. That's actually more useful.

— Mathew

---

## Sequence Configuration (Lemon Squeezy + External Email)

| Email | Trigger | Method |
|-------|---------|--------|
| Day 0 (Instant) | `order_created` webhook | External ESP (ConvertKit / Buttondown / Mailchimp) via Lemon Squeezy webhook |
| Day 2 | 48h post-open or 48h post-purchase | Same ESP, scheduled campaign |
| Day 7 | 7 days post-purchase | Same ESP, final follow-up |

### Webhook Setup
- Lemon Squeezy webhook endpoint: `https://yoursite.com/api/webhooks/lemonsqueezy`
- Event: `order_created` → trigger welcome email + store customer email in ESP list
- Merge fields needed: `{{customer_email}}`, `{{customer_name}}`, `{{product_name}}`

### GitHub Release URL in Email 1
The permanent download URL is structured as:
```
https://github.com/mrohitth/products-distribution/releases/download/v{VERSION}/{SLUG}.pdf
```
This must be updated in the ESP template each time a new version is released. The ESP cannot auto-resolve this — it is a static link in the email body.