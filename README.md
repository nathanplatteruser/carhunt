# CarHunt 🚗

A personal vehicle deal-finding engine with live public dashboards. Built by [Nathan Platter](https://github.com/nathanplatteruser) with Claude as an AI pair-programmer.

**Live dashboards:**

* **All markets (flagship)** → [nathanplatteruser.github.io/carhunt](https://nathanplatteruser.github.io/carhunt/) — every tracked listing across all four metros on one board — 3-row SUVs plus Ram 1500 and GMC Sierra 1500 pickups — with a Market dropdown to slice by Lincoln–Omaha, Denver, Kansas City, or Des Moines Metro
* **Denver, CO** → [nathanplatteruser.github.io/carhunt/denver.html](https://nathanplatteruser.github.io/carhunt/denver.html) — full-size 3-row SUVs + Ram 1500 + Sierra 1500, thru 2024, $20k–$50k, 100-mile radius
* **Kansas City, MO/KS** → [nathanplatteruser.github.io/carhunt/kc.html](https://nathanplatteruser.github.io/carhunt/kc.html) — same scope, 100-mile radius covering both the Missouri and Kansas sides

FlipScore's proximity factor is computed per listing against its **own** metro hub, so a Denver truck isn't penalized for being far from Nebraska.

## What it does

CarHunt scans Facebook Marketplace for vehicles matching a configurable watch list, then prices every listing against private-party market value and publishes a ranked, sortable deal board — one per market.

The interesting part isn't finding cheap vehicles — it's explaining why they're cheap. Every listing that looks 15%+ under market gets its detail page checked for the three classic explanations:

* **Hidden mileage** — most "deals" die here
* **Rebuilt / salvage / branded titles** — including sellers who bury "prior salvage" in the description while the listing field claims clean
* **Scam profiles** — brand-new seller accounts paired with too-good prices

The dashboard tags every listing (`NO FLAGS` / `REBUILT-SALVAGE` / `SCAM RISK`) with the research note explaining the verdict, so a viewer can filter to clean-title deals only — or browse the graveyard of trucks that looked great until someone read the odometer.


**Personal pass list.** Every row has a small ✕ — click it when a listing turns out to be a dud (cosmetic damage in the photos, something a seller shared in DMs) and it disappears from the board permanently, surviving weekly re-scrapes. The list lives in the viewer's own browser (localStorage), so the shared data files stay untouched. The "Passed: N" button reviews the graveyard and restores anything with ↩.

**Trim column + cascading filters.** Every row shows its parsed trim package, and Make / Model / Trim are include-or-exclude dropdown filters that narrow each other: pick Ford and the Model and Trim menus shrink to Ford's; pick Platinum and only makes/models actually offering a Platinum row remain. Useful for space-hunting — e.g. keep only Expedition **Max** rows.

**Dual valuation for branded titles.** Every rebuilt/salvage/branded listing carries two numbers: the **clean-title comparable** (what the same vehicle would be worth with a clean title — the functional value of the machine itself) and the **as-titled value** (clean comp minus the 25% branded-title haircut — what it will actually resell for). The dashboard's "Clean-title comp" column shows both and the title gap, so a buyer can judge the vehicle on function while pricing the exit honestly.

**Sold re-audit for existing rows.** Sold status is 100% JS-rendered (the raw HTML title tag and embedded JSON carry no sold marker - verified empirically), so stale board rows are re-audited with full page loads via `scripts/sold_audit.py`: it queues rows great-deals-first, they get visited with the hardened detector (H1 "Sold" prefix, separator variants, tab title), and the apply step tags matches. A pilot audit of the top 18 deals found 7 already sold - deal lists rot fast. The first full-board audit (all 371 un-tagged Lincoln rows) found **69 more sold (19%)** and 5 dead links — 76 of the board's rows now carry the SOLD tag.

**3rd-row status filter.** Every listing is classified **GUARANTEED** (the model ships with a 3rd row on essentially every config — Suburban, Tahoe, Yukon, Expedition, Sequoia, Armada, Escalade, Navigator, QX80, Traverse, Explorer, and friends — or the seller's description confirms "3rd row" / "7-passenger"), **SOMETIMES** (trim-dependent: Durango, Acadia — ask the seller), or **NEVER** (pickups: no 3rd row possible). A three-checkbox dropdown filters on it: keep only GUARANTEED and 100% of visible rows have 3rd rows.

**Cargo / body-length filter.** Full-size 3-row SUVs split into two very different trunks: extended-wheelbase **XL** models (Suburban / Yukon XL ~41 cu ft behind the 3rd row, Expedition Max ~36, Escalade ESV ~39) swallow a car seat + stroller + team gear with all seats up, while **STANDARD**-length siblings (Tahoe/Yukon ~25, Expedition ~19, Armada/QX80 ~17) barely manage the stroller. A three-checkbox Cargo dropdown filters XL / STANDARD / MIDSIZE-OTHER, and XL rows wear an XL badge whose tooltip shows the cu-ft number. Classification comes from `data/model_specs.json` — a **one-time curated factory-spec table** (ordered match patterns → 3rd-row status, length class, cargo cu-ft) that is never re-polled: past-model-year specs don't change, so the table only grows when a new model enters the hunt. The old regex heuristics survive purely as a fallback for unlisted models.

**Auction-history links.** Non-clean rows (rebuilt / salvage / scam-risk / lemon-risk) that have a captured VIN get an **Auction history ↗** link to `{vin}.saleshistory.org` — the VIN-keyed auction record with pre-rebuild damage photos, so title-gap decisions are made on evidence instead of seller prose. Clean-title rows never get the link (nothing to look up), and rows without a VIN can't (nothing to key on) — DM the seller for the VIN first.

**Sold tagging.** Any listing whose title contains "Sold" (Facebook prefixes sold inventory like `Sold · 2019 Ford Expedition Max`) is kept in the data for transparency but flagged `sold: true`: the dashboard renders a bright red **SOLD** tag on the row, excludes it from deal ratings and counts, and offers a "Hide sold" toggle so active-deal hunters can filter it away with one click. No extra requests are spent enriching sold rows.

## Description recovery

Mileage extraction runs three plans in strict order. **Plan A** is always Facebook's structured mileage field ("Driven 158,868 miles"). **Plan B** is labeled text patterns ("Mileage - 141,512", "odometer: 158600", "has 90,000 miles"). **Plan C** is an exhaustive candidate scan of the full listing text that catches emoji-bulleted bare statements ("✅ 158,600 miles") and shorthand ("158.6k mi") while excluding years, VIN fragments, service intervals ("every 5,000 miles"), warranty figures ("up to 100,000 miles"), and "N miles ago" phrases — then keeps the largest surviving candidate. Every detail-page visit also persists the seller's description into the listing knowledge base, so parser upgrades re-run over stored data instead of re-scraping (`scripts/sweep_extract.js` is the canonical in-page extractor).

### Field recovery

Sellers routinely leave listing fields blank (or garbage: "1 mile", "$200") while stating the real facts in the description. A recovery layer (`enrich_listing.py`) treats listing fields as the source of truth, invalidates obviously-bogus values (mileage < 1,000 or > 500,000; price < $4,000), then fuzzy-matches the description text to fill the gaps — model aliases ("chevy suburban" → Chevrolet Suburban), mileage ("167,000 miles", "167k"), year, trim, price, and title-status phrases. Recovered values are marked with a ° on the dashboard so it's always visible which numbers came from the seller's fields versus their prose.

## FlipScore

Every listing gets a 0.0–10.0 FlipScore — a v1 composite for flip-hunting, sortable and range-filterable on the dashboard: discount vs market (30%) + cost per expected remaining mile using per-model lifespans (20%) + model quality-for-price (15%) + proximity to the board's home market (15%) + listing/seller validity (15%) + title status (5%). Probable scams are hard-capped at 4.9. Hover any score for its factor breakdown.

## Seller outreach drafts

Every listing row has a **✉ Draft DM** button. Clicking it opens an editable, per-listing message draft: an interest opener plus clarifying questions chosen from that listing's own data — missing odometer, rebuilt/branded title (asks for rebuild documentation), VIN for a Carfax/AutoCheck pull, service history, and a consignment check when the vehicle is posted under multiple accounts. Drafts are generated in the build pipeline, reviewed and edited by me in the dashboard, then copied and pasted into Messenger by hand. **Nothing is ever sent automatically.**

## How valuation works

Each asking price is compared against an **estimated private-party (Facebook-style) resale value** triangulated from three signals: KBB private-party data, Edmunds appraisal values by trim, and the median asking price of comparable listings in the same dataset. Values are mileage-adjusted (~$0.08–0.09/mile against typical), and rebuilt/branded titles take a 25% haircut.

Two exit scenarios are computed per listing:

* **FB flip ROI** — margin if you buy at asking and resell privately at the estimated FB resale value.
* **Dealer exit** — margin if you buy at asking and sell to a dealer instead. The dealer trade-in estimate follows the KBB/Edmunds value ladder (trade-in runs below private party): FB resale × 0.88 (≤5 yrs) / 0.85 (6–9 yrs) / 0.82 (10+ yrs), −3 pts for luxury marques, ×0.60 for branded titles — many franchise dealers won't take those at all.

Confidence is tracked per listing (high / medium / low) and shown in the UI. Hover any column header for the exact formula.

## Architecture

```
collect (browser session, read-only)
   → data/listings.json + denver_listings.json + kc_listings.json + desmoines_listings.json   (the datasets — owned & updated by me)
   → data/listing_cache.json                          (persistent per-listing knowledge base)
   → build_dashboard.py                               (renders single-file HTML apps)
   → GitHub Pages                                     (this repo → permanent public URLs)
```

The dashboards are zero-dependency single HTML files: inline CSS/JS, OKLCH color system, monospace tabular figures, client-side sorting/filtering/search. No framework, no build step, no tracking, works offline once loaded. The data updates on my schedule; the URLs never change.

Pages:

* `index.html` — the combined all-markets deal board (sortable ledger, market/make/model + title-status filters, FlipScore slider, search)
* `denver.html` — the Denver, CO deal board (same engine, Denver-centered distance scoring)
* `kc.html` — the Kansas City deal board (same engine, KC-centered, spans MO + KS)
* `story.html` — an editorial "field report" from the first hunt: 191 Ram 1500s scanned, 3 survived verification

## Disclaimers

Market values are estimates, not appraisals. Listings are point-in-time snapshots and go stale fast. Always inspect in person, verify VIN and title history, and never send a deposit for a vehicle you haven't seen. Listing collection is done through my own logged-in browser session, read-only, at human browsing rates; scraper internals are deliberately not published.

Built in a series of working sessions with Claude (Anthropic) — search, valuation research, dashboard design, and QA were AI-assisted; direction, data ownership, and purchasing decisions are mine.
