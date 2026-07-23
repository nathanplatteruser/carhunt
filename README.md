# CarHunt 🚗

**A personal vehicle deal-finding engine with a live public dashboard.**
Built by [Nathan Platter](https://github.com/nathanplatteruser) with Claude as an AI pair-programmer.

**Live dashboard → [nathanplatteruser.github.io/carhunt](https://nathanplatteruser.github.io/carhunt/)**

## What it does

CarHunt scans Facebook Marketplace for vehicles matching a configurable watch list (currently: three-row SUVs, 2015+, under $30k, under 150k miles, within 250 miles of Lincoln, NE), then prices every listing against private-party market value and publishes a ranked, sortable deal board.

The interesting part isn't finding cheap vehicles — it's explaining *why* they're cheap. Every listing that looks 15%+ under market gets its detail page checked for the three classic explanations:

- **Hidden mileage** — most "deals" die here
- **Rebuilt / salvage titles** — including sellers who bury "prior salvage" in the description while the listing field claims clean
- **Scam profiles** — brand-new seller accounts paired with too-good prices

The dashboard tags every listing (`NO FLAGS` / `REBUILT-SALVAGE` / `SCAM RISK`) with the research note explaining the verdict, so a viewer can filter to clean-title deals only — or browse the graveyard of trucks that looked great until someone read the odometer.

## Description recovery

Sellers routinely leave listing fields blank (or garbage: "1 mile", "$200") while stating the real facts in the description. A recovery layer ([`enrich_listing.py`](enrich_listing.py)) treats listing fields as the source of truth, invalidates obviously-bogus values (mileage < 1,000 or > 500,000; price < $4,000), then fuzzy-matches the description text to fill the gaps — model aliases ("chevy suburban" → Chevrolet Suburban), mileage ("167,000 miles", "167k"), year, trim, price, and title-status phrases. Recovered values are marked with a **°** on the dashboard so it's always visible which numbers came from the seller's fields versus their prose.

## FlipScore

Every listing gets a 0.0–10.0 FlipScore — a v1 composite for flip-hunting, sortable and range-filterable on the dashboard: discount vs market (30%) + cost per expected remaining mile using per-model lifespans (20%) + model quality-for-price (15%) + proximity to Lincoln (15%) + listing/seller validity (15%) + title status (5%). Probable scams are hard-capped at 4.9. Hover any score for its factor breakdown.

## How valuation works

Each asking price is compared against a market value triangulated from three signals: KBB fair-purchase data, Edmunds appraisal values by trim, and the median asking price of comparable listings in the same dataset. Values are mileage-adjusted (~$0.08–0.09/mile against typical), and rebuilt titles take a 25% haircut. Confidence is tracked per listing (high / medium / low) and shown in the UI.

## Architecture

```
collect (browser session, read-only)
   → data/listings.json  (the dataset — owned & updated by me)
   → build_dashboard.py  (renders a single-file HTML app)
   → GitHub Pages        (this repo → permanent public URL)
```

The dashboard is a **zero-dependency single HTML file**: inline CSS/JS, OKLCH color system, monospace tabular figures, client-side sorting/filtering/search. No framework, no build step, no tracking, works offline once loaded. The data updates on my schedule; the URL never changes.

Pages:

- [`index.html`](https://nathanplatteruser.github.io/carhunt/) — the deal board (sortable ledger, title-status filter, search)
- [`story.html`](https://nathanplatteruser.github.io/carhunt/story.html) — an editorial "field report" from the first hunt: 191 Ram 1500s scanned, 3 survived verification

## Disclaimers

Market values are estimates, not appraisals. Listings are point-in-time snapshots and go stale fast. Always inspect in person, verify VIN and title history, and never send a deposit for a vehicle you haven't seen. Listing collection is done through my own logged-in browser session, read-only, at human browsing rates; scraper internals are deliberately not published.

---

*Built in a series of working sessions with Claude (Anthropic) — search, valuation research, dashboard design, and QA were AI-assisted; direction, data ownership, and purchasing decisions are mine.*
