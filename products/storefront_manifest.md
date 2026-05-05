# Storefront Settings Manifest — Lemon Squeezy
## "You First, For Once" | Single Parent Survival Guide

---

## Product Configuration

| Field | Value |
|-------|-------|
| **Product Name** | You First, For Once: The Single Parent's Survival Guide |
| **Price** | $27 |
| **Slug** | `you-first-for-once` |
| **Format** | PDF (80+ pages) + fillable worksheets + script cheat sheets |
| **Product Type** | Digital download |
| **Checkout Theme** | Minimal / Smart-Casual |

---

## Checkout Flow

```
[Product Page] → [Checkout] → [Order Bump: $7] → [Payment] → [Post-Purchase]
```

---

## Order Bump — "No Shame Saturday" Checklist

**Product:** Quick-Start Checklist: No Shame Saturday + 5 Core Scripts  
**Price:** $7  
**Type:** One-click add-on at checkout

### Placement
Positioned immediately below the main order summary, before the payment block.  
Rendered as a pre-checked checkbox with clear value copy. Labeled:

```
☐ Add the Quick-Start Checklist — $7
```

### Checkout Copy (displayed under the checkbox)

> **One morning. Zero guilt. This checklist gets you there.**
>
> The exact 3-step No Shame Saturday launch, the 5 scripts in
> screenshot-ready format, and the Week 1 kickoff conversation
> template. Everything you need to start this Saturday.
>
> Adds ~$0.02 to your processing time. Saves you hours of guilt.

### Technical Notes
- Requires `lemonsqueezy.js` overlay v2.x or Lemon Squeezy native overlay
- Pass `variant_id: 12345` for the bump variant in your Lemon Squeezy product dashboard
- Bump must be a **separate product/variant** (not a bundle) to appear as one-click add-on
- Checkout must have "Allow order bumps" enabled in Store Settings → Checkout

### Upsell Logic
- If declined, checkout continues without friction
- Decline copy: *"No thanks, I'll figure it out"*
- If accepted, adds $7 to total without page reload

---

## Post-Purchase Redirect

**Redirect URL:** `https://yoursite.com/welcome` (hosted thank-you page)  
**Delivery:** PDF delivered via **GitHub Release URL** in first email  
**No file upload to Lemon Squeezy** — keeps delivery permanent and version-controlled

### Thank-You Page Copy
```
Thank you for your order.

Your PDF is on its way — check your email (inbox + spam).

If it doesn't arrive in 5 minutes:
→ Email: mathew.r.thomson@gmail.com

Your delivery email contains your permanent GitHub-hosted
download link. This link doesn't expire.
```

---

## Checkout Visual Spec

- **Primary button:** Deep Navy (#1A365D), white text, Inter 600
- **Bump checkbox:** Moss green accent (#4ADE80) for checked state
- **Background:** Off-white (#FAFAFA)
- **Font:** Inter for all UI elements, Charter for long-form copy blocks
- **No gradients, no shadows, no stock photos**

---

## Lemon Squeezy Store Settings Checklist

- [ ] Products created with `slug: you-first-for-once`
- [ ] Bump product created as separate variant: `no-shame-saturday-checklist`
- [ ] Checkout overlay enabled in Store → Settings → Checkout
- [ ] "Thank you" page URL set to redirect to hosted page
- [ ] Gumroad cross-listing disabled (separate migration path if needed)
- [ ] Email passthrough disabled (use GitHub delivery, not LS attachment)
- [ ] Custom checkout CSS applied from `products/assets/storefront_overrides.css` if needed