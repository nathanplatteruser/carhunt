# CarHunt 🚗

A personal vehicle deal-finding engine with live public dashboards. Built by [Nathan Platter](https://github.com/nathanplatteruser) with Claude as an AI pair-programmer.

**Live dashboards:**

* **Lincoln, NE** → [nathanplatteruser.github.io/carhunt](https://nathanplatteruser.github.io/carhunt/) — 3-row SUVs + Ram 1500, thru 2024, $20k–$50k band, 60-mile radius
* **Denver, CO** → [nathanplatteruser.github.io/carhunt/denver.html](https://nathanplatteruser.github.io/carhunt/denver.html) — full-size 3-row SUVs + Ram 1500, thru 2024, $20k–$50k, 100-mile radius

## What it does

CarHunt scans Facebook Marketplace for vehicles matching a configurable watch list, then prices every listing against private-party market value and publishes a ranked, sortable deal board — one per market.

The interesting part isn't finding cheap vehicles — it's explaining why they're cheap. Every listing that looks 15%+ under market gets its detail page checked for the three classic explanations:

* **Hidden mileage** — most "deals" die here
* **Rebuilt / salvage / branded titles** — including sellers who bury "prior salvage" in the description while the listing field claims clean
* **Scam profiles** — brand-new seller accounts paired with too-good prices

The dashboard tags every listing (`NO FLAGS` / `REBUILT-SALVAGE` / `SCAM RISK`) with the research note explaining the verdict, so a viewer can filter to clean-title deals only — or browse the graveyard of trucks that looked great until someone read the odometer.

## Description recovery

Sellers routinely leave listing fields blank (or garbage: "1 mile", "$200") while stating the real facts in the description. A recovery layer (`enrich_listing.py`) treats listing fields as the source of truth, invalidates obviously-bogus values (mileage < 1,000 or > 500,000; price < $4,000), then fuzzy-matches the description text to fill the gaps — model aliases ("chevy suburban" → Chevrolet Suburban), mileage ("167,000 miles", "167k"), year, trim, price, and title-status phrases. Recovered values are marked with a ° on the dashboard so it's always visible which numbers came from the seller's fields versus their prose.

## FlipScore

Every listing gets a 0.0–10.0 FlipScore — a v1 composite for flip-hunting, sortable and range-filterable on the dashboard: discount vs market (30%) + cost per expected remaining mile using per-model lifespans (20%) + model quality-for-price (15%) + proximity to the board's home market (15%) + listing/seller validity (15%) + title status (5%). Probable scams are hard-capped at 4.9. Hover any score for its factor breakdown.

## How valuation works

Each asking price is compared against an **estimated private-party (Facebook-style) resale value** triangulated from three signals: KBB private-party data, Edmunds appraisal values by trim, and the median asking price of comparable listings in the same dataset. Values are mileage-adjusted (~$0.08–0.09/mile against typical), and rebuilt/branded titles take a 25% haircut.

Two exit scenarios are computed per listing:

* **FB flip ROI** — margin if you buy at asking and resell privately at the estimated FB resale value.
* **Dealer exit** — margin if you buy at asking and sell to a dealer instead. The dealer trade-in estimate follows the KBB/Edmunds value ladder (trade-in runs below private party): FB resale × 0.88 (≤5 yrs) / 0.85 (6–9 yrs) / 0.82 (10+ yrs), −3 pts for luxury marques, ×0.60 for branded titles — many franchise dealers won't take those at all.

Confidence is tracked per listing (high / medium / low) and shown in the UI. Hover any column header for the exact formula.

## Architecture

```
collect (browser session, read-only)
   → data/listings.json + data/denver_listings.json   (the datasets — owned & updated by me)
   → data/listing_cache.json                          (persistent per-listing knowledge base)
   → build_dashboard.py                               (renders single-file HTML apps)
   → GitHub Pages                                     (this repo → permanent public URLs)
```

The dashboards are zero-dependency single HTML files: inline CSS/JS, OKLCH color system, monospace tabular figures, client-side sorting/filtering/search. No framework, no build step, no tracking, works offline once loaded. The data updates on my schedule; the URLs never change.

Pages:

* `index.html` — the Lincoln, NE deal board (sortable ledger, make/model + title-status filters, FlipScore slider, search)
* `denver.html` — the Denver, CO deal board (same engine, Denver-centered distance scoring)
* `story.html` — an editorial "field report" from the first hunt: 191 Ram 1500s scanned, 3 survived verification

## Disclaimers

Market values are estimates, not appraisals. Listings are point-in-time snapshots and go stale fast. Always inspect in person, verify VIN and title history, and never send a deposit for a vehicle you haven't seen. Listing collection is done through my own logged-in browser session, read-only, at human browsing rates; scraper internals are deliberately not published.

Built in a series of working sessions with Claude (Anthropic) — search, valuation research, dashboard design, and QA were AI-assisted; direction, data ownership, and purchasing decisions are mine.
