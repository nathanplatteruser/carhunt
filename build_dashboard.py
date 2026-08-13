#!/usr/bin/env python3
"""Build the CarHunt ledger dashboard from data/listings.json + data/config.json.

Design: product-register inventory ledger. Pure white bg, near-black ink,
amber brand accent (oklch 0.65 0.146 60), tabular-mono figures, sortable table.
No cards, no gradients, no emojis.

Usage: python3 build_dashboard.py [--data-dir DIR] [--out FILE]
"""
import argparse, json, html, os, datetime

RATINGS = [
    ("great", "Great deal", 15),
    ("good",  "Good deal",   8),
    ("fair",  "Fair price", -5),
    ("over",  "Overpriced", None),
]

def rating_for(deal_pct):
    if deal_pct is None:
        return ("unknown", "Unvalued")
    for key, label, floor in RATINGS:
        if floor is None or deal_pct >= floor:
            return (key, label)
    return ("over", "Overpriced")

# ── FlipScore v1 ─────────────────────────────────────────────────────
# Expected useful life (miles) and quality-for-price factor (0-1.5) per model
MODEL_META = {
    "Sequoia":    (300000, 1.5), "Tahoe":     (250000, 1.2), "Suburban": (250000, 1.2),
    "Yukon XL":   (250000, 1.2), "Expedition": (250000, 1.1), "Armada":  (250000, 1.0),
    "Durango":    (230000, 0.8), "Traverse":  (200000, 0.6), "Explorer": (200000, 0.7),
    "1500":       (250000, 1.0),
}
# Approx road miles from downtown Lincoln, NE (68508)
CITY_MI = {
    "Lincoln, NE": 0, "Denton, NE": 12, "Valparaiso, NE": 22, "Crete, NE": 25, "Seward, NE": 26,
    "Wahoo, NE": 32, "Waterloo, NE": 40, "Beatrice, NE": 42, "Gretna, NE": 42, "Springfield, NE": 45,
    "Elkhorn, NE": 47, "Papillion, NE": 50, "Omaha, NE": 55, "Bellevue, NE": 55, "York, NE": 50,
    "Council Bluffs, IA": 60, "Blair, NE": 75, "Fremont, NE": 55, "Missouri Valley, IA": 80,
    "Humphrey, NE": 95, "Grand Island, NE": 95, "South Sioux City, NE": 100, "Sioux City, IA": 100,
    "Denison, IA": 105, "Kearney, NE": 130, "Savannah, MO": 130, "Yankton, SD": 130,
    "Lawton, IA": 95, "Dante, SD": 150, "Storm Lake, IA": 150, "Glidden, IA": 150,
    "Tescott, KS": 165, "Salina, KS": 165, "Sheldon, IA": 175, "Sioux Falls, SD": 180,
    "Harrisburg, SD": 172, "Brandon, SD": 188, "Parkville, MO": 175, "Kansas City, KS": 180,
    "Mission, KS": 182, "Shawnee, KS": 182, "Olathe, KS": 185, "Overland Park, KS": 185,
    "Kansas City, MO": 185, "West Des Moines, IA": 185, "Clive, IA": 185, "Des Moines, IA": 190,
    "Ankeny, IA": 197, "Pleasant Hill, IA": 197, "Jackson, MN": 195, "Lee's Summit, MO": 200,
    "Grain Valley, MO": 200, "Wichita, KS": 220, "Derby, KS": 230, "Garnett, KS": 220,
    "Great Bend, KS": 225, "McCook, NE": 232, "Raymore, MO": 210, "Sedalia, MO": 250,
    "Fort Scott, KS": 250, "Chanute, KS": 255,
}
STATE_MI = {"NE": 70, "IA": 160, "KS": 200, "MO": 220, "SD": 175, "MN": 210, "IL": 300, "OK": 320, "CO": 400, "AR": 350, "WI": 350, "TX": 500, "ND": 400, "IN": 400, "TN": 450, "GA": 700, "LA": 600, "AL": 700, "KY": 500, "NC": 800, "SC": 800, "MS": 600, "UT": 700, "MI": 500}

def dist_from_lincoln(location):
    if not location: return 200
    if location in CITY_MI: return CITY_MI[location]
    st = location.rsplit(",", 1)[-1].strip()
    return STATE_MI.get(st, 300)

def flip_score(l):
    """0.0 (skip) .. 10.0 (slam dunk). Six weighted components, sum <= 10."""
    parts = {}
    # 1. Deal margin vs market (0-3.0): 0% under -> 0, 25%+ under -> 3.0
    pct = l.get("deal_pct") or 0
    parts["margin"] = round(max(0, min(3.0, pct / 25 * 3)), 2)
    # 2. Cost per remaining mile (0-2.0): <=$0.10/mi -> 2.0, >=$0.40/mi -> 0
    life, quality = MODEL_META.get(l.get("model"), (230000, 0.9))
    if l.get("mileage") is not None and l.get("price"):
        remaining = max(20000, life - l["mileage"])
        cpm = l["price"] / remaining
        parts["cost_per_mile"] = round(max(0, min(2.0, (0.40 - cpm) / 0.30 * 2)), 2)
    else:
        parts["cost_per_mile"] = 0.6  # unknown mileage: below-average default
    # 3. Vehicle quality for the price point (0-1.5)
    parts["quality"] = quality
    # 4. Proximity to the board's home market (0-1.5): 0 mi -> 1.5, 250+ mi -> 0
    #    multi-market boards precompute _dist per listing from its own metro hub
    d = l.get("_dist") if l.get("_dist") is not None else dist_from_lincoln(l.get("location"))
    parts["proximity"] = round(max(0, min(1.5, (250 - d) / 250 * 1.5)), 2)
    l["distance_mi"] = d
    # 5. Listing/seller validity (0-1.5)
    notes = (l.get("notes") or "").lower()
    flag = l.get("flag", "valid")
    v = 1.0
    if flag == "suspect": v = 0.0
    elif flag == "salvage": v = 0.5
    if l.get("mileage") is not None: v += 0.3
    if l.get("value_confidence") == "high": v += 0.2
    if "account created" in notes or "seller account is new" in notes or "joined" in notes: v -= 0.3
    parts["validity"] = round(max(0, min(1.5, v)), 2)
    # 6. Title preference (0-0.5): clean 0.5, salvage 0.2, suspect 0
    parts["title"] = 0.5 if flag == "valid" else (0.2 if flag == "salvage" else 0.0)
    score = round(min(10.0, sum(parts.values())), 1)
    if flag == "suspect":
        score = min(score, 4.9)  # probable scams never crest the "worth a look" band
    l["flip_score"] = score
    l["score_parts"] = " · ".join(f"{k} {v:g}" for k, v in parts.items())
    return l

def enrich(listings, threshold):
    out = []
    for l in listings:
        l = dict(l)
        price, mv = l.get("price"), l.get("market_value")
        blob = ((l.get("notes") or "") + " " + (l.get("title") or "")).lower()
        if "salvage" in blob or "rebuilt" in blob or "branded" in blob:
            l["flag"] = "salvage"
        elif "scam" in blob or "rebuilder" in blob or "lemon" in blob or "implausible" in blob:
            l["flag"] = "suspect"
        else:
            l["flag"] = "valid"
        # rebuilt/salvage/branded titles are worth ~25% less than clean-title book -
        # applied at render time (idempotent per build) so listings.json stays clean-book
        if l["flag"] == "salvage" and mv and "haircut" not in (l.get("value_source") or ""):
            mv = int(round(mv * 0.75, -2))
            l["market_value"] = mv
            l["value_source"] = (l.get("value_source") or "") + " · 25% rebuilt-title haircut"
        if price and mv:
            l["deal_pct"] = round((mv - price) / mv * 100, 1)
            l["savings"] = int(mv - price)
            # dealer trade-in estimate: KBB/Edmunds ladder puts trade-in 12-18% below
            # private party (wider for older + luxury; near-wholesale for branded titles)
            age = 2026 - (l.get("year") or 2020)
            ratio = 0.88 if age <= 5 else 0.85 if age <= 9 else 0.82
            if (l.get("make") or "") in ("Cadillac", "Lincoln", "Infiniti"): ratio -= 0.03
            if l["flag"] == "salvage": ratio = 0.60  # most franchise dealers pass entirely on branded titles
            l["trade_value"] = int(round(mv * ratio, -2))
            l["fb_roi"] = round((mv - price) / price * 100, 1)
            l["dealer_roi"] = round((l["trade_value"] - price) / price * 100, 1)
        else:
            l["deal_pct"] = None
            l["savings"] = None
            l["trade_value"] = None
            l["fb_roi"] = None
            l["dealer_roi"] = None
        key, label = rating_for(l["deal_pct"])
        l["rating_key"], l["rating_label"] = key, label
        l["flagged"] = l["deal_pct"] is not None and l["deal_pct"] >= threshold
        flip_score(l)
        out.append(l)
    out.sort(key=lambda x: -x.get("flip_score", 0))
    return out

def build(data_dir, out_path):
    with open(os.path.join(data_dir, "config.json")) as f:
        config = json.load(f)
    lpath = os.path.join(data_dir, "listings.json")
    listings = []
    if os.path.exists(lpath):
        with open(lpath) as f:
            listings = json.load(f)
    threshold = config.get("deal_threshold_pct", 15)
    listings = enrich(listings, threshold)

    n = len(listings)
    great = sum(1 for l in listings if l["rating_key"] == "great")
    valued = [l for l in listings if l["deal_pct"] is not None]
    best = max((l["deal_pct"] for l in valued), default=0)
    clean_flagged = sum(1 for l in listings if l["flagged"] and l["flag"] == "valid")
    updated = datetime.datetime.now().strftime("%b %-d, %Y · %-I:%M %p")
    loc = config["location"]["city"]
    scope = config.get("scope_label", "")
    radius = config["location"]["radius_miles"]

    makes = sorted({l.get("make") for l in listings if l.get("make")})
    models = sorted({l.get("model") for l in listings if l.get("model")})
    markets = sorted({l.get("market") for l in listings if l.get("market")})
    page = TEMPLATE
    page = page.replace("__MAKES__", json.dumps(makes))
    page = page.replace("__MODELS__", json.dumps(models))
    page = page.replace("__MARKETS__", json.dumps(markets))
    page = page.replace("__DATA__", json.dumps(listings))
    page = page.replace("__THRESHOLD__", str(threshold))
    for k, v in {
        "__N__": str(n), "__GREAT__": str(great), "__BEST__": f"{best:.0f}",
        "__CLEANGREAT__": str(clean_flagged), "__UPDATED__": html.escape(updated),
        "__LOC__": html.escape(loc), "__SCOPE__": html.escape(scope), "__RADIUS__": str(radius),
    }.items():
        page = page.replace(k, v)
    with open(out_path, "w") as f:
        f.write(page)
    print(f"Wrote {out_path}: {n} listings, {great} great deals, best {best:.0f}% under market")

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CarHunt — __SCOPE__</title>
<style>
  :root {
    --bg: oklch(1 0 0);
    --ink: oklch(0.21 0.012 60);
    --muted: oklch(0.44 0.018 60);
    --faint: oklch(0.60 0.015 60);
    --line: oklch(0.90 0.006 60);
    --line-strong: oklch(0.78 0.01 60);
    --surface: oklch(0.974 0.004 75);
    --brand: oklch(0.65 0.146 60);
    --brand-ink: oklch(0.49 0.125 60);
    --pos: oklch(0.47 0.115 155);
    --neg: oklch(0.50 0.135 27);
    --warn-bg: oklch(0.955 0.028 78);
    --warn-ink: oklch(0.42 0.085 65);
    --danger-bg: oklch(0.955 0.024 27);
    --danger-ink: oklch(0.44 0.14 27);
    --ok-ink: oklch(0.44 0.02 60);
    --mono: ui-monospace, "SF Mono", "Cascadia Mono", Menlo, Consolas, monospace;
    --z-pop: 30; --z-head: 20;
  }
  * { box-sizing: border-box; margin: 0; }
  html { -webkit-text-size-adjust: 100%; }
  body { background: var(--bg); color: var(--ink); font: 14px/1.45 -apple-system, "Segoe UI", system-ui, Roboto, Helvetica, Arial, sans-serif; }
  a { color: var(--brand-ink); text-decoration: none; }
  a:hover { text-decoration: underline; }

  .masthead { border-bottom: 2px solid var(--ink); }
  .masthead .wrap { display: flex; align-items: baseline; gap: 14px; padding: 18px 24px 14px; }
  .wrap { max-width: 1240px; margin: 0 auto; }
  .wordmark { font-size: 17px; font-weight: 800; letter-spacing: .01em; white-space: nowrap; }
  .wordmark .tick { color: var(--brand); }
  .scope { color: var(--muted); font-size: 13px; }
  .updated { margin-left: auto; color: var(--faint); font-size: 12.5px; font-variant-numeric: tabular-nums; white-space: nowrap; }

  .digest { border-bottom: 1px solid var(--line); }
  .digest .wrap { display: flex; flex-wrap: wrap; gap: 6px 28px; padding: 10px 24px; font-size: 13px; color: var(--muted); }
  .digest b { color: var(--ink); font-family: var(--mono); font-size: 13px; font-weight: 600; }

  .toolbar { position: sticky; top: 0; background: var(--bg); border-bottom: 1px solid var(--line); z-index: var(--z-head); }
  .toolbar .wrap { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; padding: 10px 24px; }
  .toolbar input[type=search], .toolbar input[type=number], .toolbar select, .toolbar .dd > button {
    border: 1px solid var(--line-strong); background: var(--bg); color: var(--ink);
    border-radius: 3px; padding: 6px 9px; font-size: 13px; font-family: inherit;
  }
  .toolbar input[type=search] { width: 210px; }
  .toolbar input[type=number] { width: 100px; }
  .toolbar :is(input, select, button):focus-visible { outline: 2px solid var(--brand); outline-offset: 1px; }
  .dd { position: relative; }
  .dd > button { cursor: pointer; font-weight: 500; }
  .dd .menu { display: none; position: absolute; left: 0; top: calc(100% + 4px); background: var(--bg); border: 1px solid var(--line-strong); border-radius: 3px; box-shadow: 0 6px 24px oklch(0.2 0.01 60 / .14); padding: 8px 10px; z-index: var(--z-pop); min-width: 210px; }
  .dd.open .menu { display: block; }
  .dd .menu label { display: flex; align-items: center; gap: 8px; padding: 5px 2px; font-size: 13px; cursor: pointer; }
  .dd .menu input { accent-color: var(--brand-ink); width: 14px; height: 14px; }
  .count { margin-left: auto; color: var(--faint); font-size: 12.5px; font-variant-numeric: tabular-nums; }
  .dd .mode { display: flex; gap: 4px; margin-bottom: 6px; border-bottom: 1px solid var(--line); padding-bottom: 6px; }
  .dd .mode button { flex: 1; border: 1px solid var(--line-strong); background: var(--bg); border-radius: 3px; padding: 4px 6px; font-size: 12px; font-weight: 600; cursor: pointer; color: var(--muted); }
  .dd .mode button.on { background: var(--brand-ink); border-color: var(--brand-ink); color: #fff; }
  .dd .menu .row-links { display: flex; gap: 10px; font-size: 12px; padding: 4px 2px 2px; }
  .dd .menu .row-links a { cursor: pointer; }
  .score { font-family: var(--mono); font-size: 15px; font-weight: 700; }
  .score.hi { color: var(--pos); } .score.mid { color: var(--brand-ink); } .score.lo { color: var(--faint); }
  .rangewrap { display: flex; align-items: center; gap: 6px; }
  .rangewrap .lbl { font-size: 12px; color: var(--muted); font-weight: 600; white-space: nowrap; }
  .rangewrap input[type=number] { width: 58px; }
  .dualslider { position: relative; width: 130px; height: 22px; }
  .dualslider input[type=range] { position: absolute; left: 0; top: 0; width: 100%; margin: 0; height: 22px; background: none; pointer-events: none; -webkit-appearance: none; appearance: none; }
  .dualslider input[type=range]::-webkit-slider-runnable-track { height: 3px; background: transparent; }
  .dualslider input[type=range]::-webkit-slider-thumb { -webkit-appearance: none; appearance: none; pointer-events: auto; width: 14px; height: 14px; border-radius: 50%; background: var(--brand-ink); border: 2px solid var(--bg); box-shadow: 0 0 0 1px var(--line-strong); margin-top: -6px; cursor: pointer; }
  .dualslider input[type=range]::-moz-range-thumb { pointer-events: auto; width: 12px; height: 12px; border-radius: 50%; background: var(--brand-ink); border: 2px solid var(--bg); cursor: pointer; }
  .dualslider .track { position: absolute; top: 10px; left: 0; right: 0; height: 3px; background: var(--line); }
  .dualslider .fill { position: absolute; top: 10px; height: 3px; background: var(--brand-ink); }

  main { padding: 0 24px 48px; }
  table { width: 100%; border-collapse: collapse; }
  thead th { text-align: left; font-size: 11.5px; font-weight: 600; color: var(--muted); letter-spacing: .02em; padding: 10px 10px 7px; border-bottom: 1px solid var(--line-strong); white-space: nowrap; cursor: pointer; user-select: none; }
  thead th:hover { color: var(--ink); }
  thead th .dir { color: var(--brand-ink); }
  tbody td { padding: 11px 10px; border-bottom: 1px solid var(--line); vertical-align: top; }
  tbody tr { transition: background .15s ease; }
  tbody tr:hover { background: var(--surface); }
  .truck { max-width: 430px; }
  .truck .name { font-weight: 650; font-size: 13.5px; line-height: 1.35; }
  .truck .name a { color: var(--ink); }
  .truck .name a:hover { color: var(--brand-ink); text-decoration: none; }
  .truck .sub { color: var(--muted); font-size: 12.5px; margin-top: 1px; }
  .truck .note { color: var(--faint); font-size: 12px; margin-top: 3px; line-height: 1.4; max-width: 62ch; }
  .truck .note.alert { color: var(--danger-ink); }
  .num { font-family: var(--mono); font-variant-numeric: tabular-nums; font-size: 13px; white-space: nowrap; }
  td.right, th.right { text-align: right; }
  .delta { font-family: var(--mono); font-size: 13px; font-weight: 600; white-space: nowrap; }
  .delta.pos { color: var(--pos); } .delta.neg { color: var(--neg); } .delta.zero { color: var(--faint); }
  .bar { height: 3px; width: 84px; background: var(--line); margin-top: 5px; position: relative; }
  .bar i { position: absolute; top: 0; bottom: 0; }
  .status { font-size: 11px; font-weight: 700; letter-spacing: .04em; padding: 2px 7px; border-radius: 2px; white-space: nowrap; }
  .status.valid { color: var(--ok-ink); border: 1px solid var(--line-strong); }
  .status.salvage { background: var(--warn-bg); color: var(--warn-ink); }
  .status.suspect { background: var(--danger-bg); color: var(--danger-ink); }
  .conf { display: block; margin-top: 4px; color: var(--faint); font-size: 11px; }
  .rec { color: var(--brand-ink); font-weight: 700; cursor: help; }
  .open { font-size: 12.5px; font-weight: 600; white-space: nowrap; }
  .empty { padding: 56px 10px; color: var(--muted); }
  .empty b { display: block; color: var(--ink); font-size: 15px; margin-bottom: 4px; }
  footer { border-top: 1px solid var(--line); color: var(--faint); font-size: 12px; padding: 14px 24px 28px; }
  footer .wrap { padding: 0; max-width: 1240px; }

  @media (max-width: 880px) {
    .masthead .wrap { flex-wrap: wrap; row-gap: 2px; padding: 14px 16px 10px; }
    .masthead .scope { flex-basis: 100%; order: 3; }
    .digest .wrap, .toolbar .wrap { padding-left: 16px; padding-right: 16px; }
    main { padding: 0 8px 40px; }
    thead { display: none; }
    table, tbody, tr, td { display: block; }
    tbody tr { border-bottom: 1px solid var(--line-strong); padding: 12px 8px; }
    tbody td { border: none; padding: 3px 0; }
    tbody td:empty { display: none; }
    .truck { max-width: none; padding-bottom: 6px; }
    td.right { text-align: left; }
    td[data-l] { display: inline-block; margin-right: 16px; }
    td[data-l]::before { content: attr(data-l); display: block; color: var(--faint); font-size: 10.5px; letter-spacing: .03em; }
    .mrow { display: inline-block; }
    .bar { display: none; }
    .conf { display: none; }
    td.statuscell, td.opencell { display: inline-block; margin-right: 16px; vertical-align: bottom; }
  }
  @media (prefers-reduced-motion: reduce) {
    tbody tr { transition: none; }
  }
</style>
</head>
<body>
<header class="masthead"><div class="wrap">
  <span class="wordmark">CARHUNT<span class="tick">▮</span> <span style="font-weight:500;color:var(--muted)">Cornhusker</span></span>
  <span class="scope">__SCOPE__ · __LOC__ · __RADIUS__ mi</span>
  <span class="updated">updated __UPDATED__</span>
</div></header>

<div class="digest"><div class="wrap">
  <span><b>__N__</b> tracked</span>
  <span><b>__GREAT__</b> at ≥__THRESHOLD__% under market</span>
  <span><b>__CLEANGREAT__</b> of those with no red flags</span>
  <span>best discount <b>−__BEST__%</b></span>
</div></div>

<div class="toolbar"><div class="wrap">
  <input type="search" id="q" placeholder="Search trim, city, note…" aria-label="Search listings">
  <select id="marketF" aria-label="Market filter" style="display:none"></select>
  <div class="dd" id="makeDD">
    <button id="makeBtn" type="button" aria-haspopup="true">Make: all</button>
    <div class="menu" id="makeMenu"></div>
  </div>
  <div class="dd" id="modelDD">
    <button id="modelBtn" type="button" aria-haspopup="true">Model: all</button>
    <div class="menu" id="modelMenu"></div>
  </div>
  <div class="dd" id="flagDD">
    <button id="flagBtn" type="button" aria-haspopup="true">Title status: all</button>
    <div class="menu" id="flagMenu">
      <label><input type="checkbox" value="valid" checked> No red flags</label>
      <label><input type="checkbox" value="salvage" checked> Rebuilt / salvage title</label>
      <label><input type="checkbox" value="suspect" checked> Scam / lemon risk</label>
    </div>
  </div>
  <div class="rangewrap" title="FlipScore range filter">
    <span class="lbl">Score</span>
    <input type="number" id="scoreMin" min="0" max="10" step="0.1" value="0.0" aria-label="Minimum FlipScore">
    <div class="dualslider">
      <div class="track"></div><div class="fill" id="sliderFill"></div>
      <input type="range" id="rangeMin" min="0" max="10" step="0.1" value="0">
      <input type="range" id="rangeMax" min="0" max="10" step="0.1" value="10">
    </div>
    <input type="number" id="scoreMax" min="0" max="10" step="0.1" value="10.0" aria-label="Maximum FlipScore">
  </div>
  <select id="ratingF" aria-label="Deal rating filter">
    <option value="all">All ratings</option>
    <option value="great">Great deals only</option>
    <option value="goodplus">Good &amp; better</option>
  </select>
  <input type="number" id="maxP" placeholder="Max $" step="500" min="0" aria-label="Maximum price">
  <span class="count" id="count"></span>
</div></div>

<main><div class="wrap">
  <table id="tbl">
    <thead><tr>
      <th data-k="title">Truck <span class="dir"></span></th>
      <th data-k="flip_score" class="right" title="FlipScore 0-10: margin vs market + cost per remaining mile + model quality + proximity to its metro hub + listing validity + title status">Score <span class="dir"></span></th>
      <th data-k="mileage" class="right">Miles <span class="dir"></span></th>
      <th data-k="price" class="right">Asking <span class="dir"></span></th>
      <th data-k="market_value" class="right" title="Estimated private-party (Facebook-style) resale value: model/year/trim tables calibrated to KBB private-party + Edmunds appraisal ranges, mileage-adjusted, 25% haircut on rebuilt/branded titles">Est. FB resale <span class="dir"></span></th>
      <th data-k="fb_roi" class="right" title="Margin if you buy at asking and resell privately on Marketplace at est. FB resale: (FB resale − asking) ÷ asking">FB flip ROI <span class="dir"></span></th>
      <th data-k="dealer_roi" class="right" title="Margin if you buy at asking and sell to a dealer. Dealer trade-in est. = FB resale × 0.82–0.88 (KBB/Edmunds trade-in vs private-party ladder; luxury −3pts; branded titles ×0.60 — many dealers won't take them)">Dealer exit <span class="dir"></span></th>
      <th data-k="flag">Status <span class="dir"></span></th>
      <th></th>
    </tr></thead>
    <tbody id="rows"></tbody>
  </table>
  <div class="empty" id="empty" style="display:none"><b>No listings match</b>Clear a filter, or run a fresh Marketplace sweep to add inventory.</div>
</div></main>

<footer><div class="wrap">Estimated market values: KBB / Edmunds private-party anchors adjusted for mileage and title status, cross-checked against local asking-price comps. FlipScore (0.0–10.0) is an internal v1 index: discount vs market (30%) + cost per expected remaining mile (20%) + model quality-for-price (15%) + proximity to the board's home metro (15%) + listing/seller validity (15%) + title status (5%). Hover a score for its breakdown. 10 = slam dunk, 0 = seller wins. Estimates are approximate — inspect in person and verify VIN, title, and history before buying. Never send deposits for a truck you haven't seen.</div></footer>

<script>
const DATA = __DATA__;
const MAKES = __MAKES__;
const MODELS = __MODELS__;
const MARKETS = __MARKETS__;
const STATUS = { valid: "NO FLAGS", salvage: "REBUILT/SALVAGE", suspect: "SCAM RISK" };
const state = { q: "", market: "all", flags: new Set(["valid","salvage","suspect"]), rating: "all", maxP: null,
  sort: { k: "flip_score", d: -1 },
  makeMode: "include", makeSel: new Set(MAKES),
  modelMode: "include", modelSel: new Set(MODELS),
  sMin: 0, sMax: 10 };
const fmt = n => n == null ? "—" : "$" + n.toLocaleString();
const fmtMi = n => n == null ? "—" : (n/1000).toFixed(0) + "k";

function row(l) {
  const pct = l.deal_pct;
  const dcls = pct == null ? "zero" : pct >= 3 ? "pos" : pct <= -3 ? "neg" : "zero";
  const dtxt = pct == null ? "—" : (pct > 0 ? "−" : pct < 0 ? "+" : "") + Math.abs(pct).toFixed(0) + "%";
  const w = pct == null ? 0 : Math.min(42, Math.abs(pct) * 1.6);
  const bar = pct == null ? "" :
    `<div class="bar"><i style="${pct >= 0 ? "right:50%" : "left:50%"};width:${w}px;background:${pct >= 0 ? "var(--pos)" : "var(--neg)"}"></i></div>`;
  const alert = l.flag !== "valid";
  const rec = f => (l.recovered || []).includes(f) ? `<span class="rec" title="Recovered from the listing's description text - seller left the field blank or invalid">°</span>` : "";
  const conf = l.value_confidence ? `<span class="conf">${l.value_confidence} confidence</span>` : "";
  const sav = l.savings != null && l.savings > 0 ? ` <span class="num" style="color:var(--pos)">(${fmt(l.savings)})</span>` : "";
  return `<tr>
    <td class="truck">
      <div class="name"><a href="${l.url}" target="_blank" rel="noopener">${l.title}</a></div>
      <div class="sub">${l.location || "—"}${l.market ? " · " + l.market : ""}${l.trim ? " · " + l.trim + rec("trim") : ""}${l.title_status_desc ? " · desc: " + l.title_status_desc + " title" : ""}</div>
      ${l.notes ? `<div class="note${alert ? " alert" : ""}">${l.notes}</div>` : ""}
    </td>
    <td class="right" data-l="SCORE"><span class="mrow"><span class="score ${l.flip_score >= 7 ? "hi" : l.flip_score >= 4 ? "mid" : "lo"}" title="${l.score_parts || ""}">${l.flip_score.toFixed(1)}</span></span></td>
    <td class="right" data-l="MILES"><span class="mrow"><span class="num">${fmtMi(l.mileage)}${rec("mileage")}</span></span></td>
    <td class="right" data-l="ASKING"><span class="mrow"><span class="num" style="font-weight:650">${fmt(l.price)}</span></span></td>
    <td class="right" data-l="EST. FB RESALE"><span class="mrow"><span class="num" style="color:var(--muted)">${fmt(l.market_value)}</span>${conf}</span></td>
    <td class="right" data-l="FB FLIP ROI"><span class="mrow"><span class="delta ${l.fb_roi == null ? "zero" : l.fb_roi >= 3 ? "pos" : l.fb_roi <= -3 ? "neg" : "zero"}" title="resell privately at ${fmt(l.market_value)}">${l.fb_roi == null ? "—" : (l.fb_roi > 0 ? "+" : "") + l.fb_roi.toFixed(0) + "%"}</span>${sav}${bar}</span></td>
    <td class="right" data-l="DEALER EXIT"><span class="mrow"><span class="delta ${l.dealer_roi == null ? "zero" : l.dealer_roi >= 3 ? "pos" : l.dealer_roi <= -3 ? "neg" : "zero"}" title="dealer trade-in est. ${fmt(l.trade_value)}">${l.dealer_roi == null ? "—" : (l.dealer_roi > 0 ? "+" : "") + l.dealer_roi.toFixed(0) + "%"}</span></span></td>
    <td class="statuscell"><span class="status ${l.flag}">${STATUS[l.flag]}</span></td>
    <td class="right opencell"><a class="open" href="${l.url}" target="_blank" rel="noopener">Open ↗</a></td>
  </tr>`;
}

function render() {
  const q = state.q.toLowerCase();
  const makeOK = l => state.makeMode === "include" ? state.makeSel.has(l.make) : !state.makeSel.has(l.make);
  const modelOK = l => state.modelMode === "include" ? state.modelSel.has(l.model) : !state.modelSel.has(l.model);
  let rows = DATA.filter(l =>
    (state.market === "all" || l.market === state.market)
    && state.flags.has(l.flag)
    && makeOK(l) && modelOK(l)
    && l.flip_score >= state.sMin - 1e-9 && l.flip_score <= state.sMax + 1e-9
    && (state.rating === "all" || (state.rating === "great" ? l.rating_key === "great" : ["great","good"].includes(l.rating_key)))
    && (state.maxP == null || (l.price ?? 0) <= state.maxP)
    && (!q || [l.title, l.location, l.trim, l.notes].join(" ").toLowerCase().includes(q)));
  const { k, d } = state.sort;
  rows.sort((a, b) => {
    let x = a[k], y = b[k];
    if (k === "title") { x = a.year ?? 0; y = b.year ?? 0; }
    if (k === "flag") { x = a.flag; y = b.flag; return x < y ? -d : x > y ? d : 0; }
    if (x == null) return 1; if (y == null) return -1;
    return (x - y) * d || (b.flip_score - a.flip_score);
  });
  document.getElementById("rows").innerHTML = rows.map(row).join("");
  document.getElementById("empty").style.display = rows.length ? "none" : "block";
  document.getElementById("count").textContent = rows.length + " of " + DATA.length;
  document.querySelectorAll("thead th").forEach(th => {
    th.querySelector(".dir") && (th.querySelector(".dir").textContent = th.dataset.k === k ? (d === -1 ? "↓" : "↑") : "");
  });
}

document.getElementById("q").oninput = e => { state.q = e.target.value; render(); };
// ── Market dropdown (only shown on multi-market boards) ──
const marketF = document.getElementById("marketF");
if (MARKETS.length > 1) {
  marketF.style.display = "";
  marketF.innerHTML = `<option value="all">All markets</option>` +
    MARKETS.map(m => `<option value="${m}">${m}</option>`).join("");
  marketF.onchange = e => { state.market = e.target.value; render(); };
}
document.getElementById("ratingF").onchange = e => { state.rating = e.target.value; render(); };
document.getElementById("maxP").oninput = e => { state.maxP = e.target.value ? +e.target.value : null; render(); };
document.querySelectorAll("thead th[data-k]").forEach(th => th.onclick = () => {
  const k = th.dataset.k;
  state.sort = state.sort.k === k ? { k, d: -state.sort.d } : { k, d: k === "title" || k === "flag" ? 1 : -1 };
  if (k === "deal_pct" || k === "market_value" || k === "price" ) state.sort.d = state.sort.k === k && state.sort.d ? state.sort.d : state.sort.d;
  render();
});
// ── Generic include/exclude multi-select dropdowns (Make, Model) ──
function buildPicker(kind, items, btnId, menuId) {
  const menu = document.getElementById(menuId);
  const btn = document.getElementById(btnId);
  menu.innerHTML = `
    <div class="mode">
      <button type="button" data-m="include" class="on">Include</button>
      <button type="button" data-m="exclude">Exclude</button>
    </div>
    <div class="row-links"><a data-a="all">select all</a><a data-a="none">clear</a></div>
    ${items.map(v => `<label><input type="checkbox" value="${v}" checked> ${v}</label>`).join("")}`;
  const label = () => {
    const sel = state[kind + "Sel"], mode = state[kind + "Mode"];
    const name = kind === "make" ? "Make" : "Model";
    if (mode === "include" && sel.size === items.length) { btn.textContent = name + ": all"; return; }
    if (sel.size === 0) { btn.textContent = name + ": " + (mode === "include" ? "none" : "all"); return; }
    const list = [...sel].slice(0, 2).join(", ") + (sel.size > 2 ? ` +${sel.size - 2}` : "");
    btn.textContent = `${name}: ${mode === "include" ? "" : "not "}${list}`;
  };
  menu.querySelectorAll(".mode button").forEach(b => b.onclick = e => {
    e.stopPropagation();
    state[kind + "Mode"] = b.dataset.m;
    menu.querySelectorAll(".mode button").forEach(x => x.classList.toggle("on", x === b));
    label(); render();
  });
  menu.querySelectorAll(".row-links a").forEach(a => a.onclick = e => {
    e.stopPropagation();
    const on = a.dataset.a === "all";
    menu.querySelectorAll("input[type=checkbox]").forEach(c => c.checked = on);
    state[kind + "Sel"] = new Set(on ? items : []);
    label(); render();
  });
  menu.addEventListener("change", () => {
    state[kind + "Sel"] = new Set([...menu.querySelectorAll("input[type=checkbox]")].filter(c => c.checked).map(c => c.value));
    label(); render();
  });
}
buildPicker("make", MAKES, "makeBtn", "makeMenu");
buildPicker("model", MODELS, "modelBtn", "modelMenu");

// ── FlipScore range: dual slider + number boxes, kept in sync ──
const rMin = document.getElementById("rangeMin"), rMax = document.getElementById("rangeMax");
const nMin = document.getElementById("scoreMin"), nMax = document.getElementById("scoreMax");
const fill = document.getElementById("sliderFill");
function setRange(lo, hi, src) {
  lo = Math.max(0, Math.min(10, isNaN(lo) ? 0 : lo));
  hi = Math.max(0, Math.min(10, isNaN(hi) ? 10 : hi));
  if (lo > hi) { if (src === "min") hi = lo; else lo = hi; }
  state.sMin = Math.round(lo * 10) / 10; state.sMax = Math.round(hi * 10) / 10;
  rMin.value = state.sMin; rMax.value = state.sMax;
  if (src !== "numMin") nMin.value = state.sMin.toFixed(1);
  if (src !== "numMax") nMax.value = state.sMax.toFixed(1);
  fill.style.left = (state.sMin / 10 * 100) + "%";
  fill.style.width = ((state.sMax - state.sMin) / 10 * 100) + "%";
  render();
}
rMin.oninput = () => setRange(+rMin.value, +rMax.value, "min");
rMax.oninput = () => setRange(+rMin.value, +rMax.value, "max");
nMin.oninput = () => setRange(+nMin.value, state.sMax, "numMin");
nMax.oninput = () => setRange(state.sMin, +nMax.value, "numMax");
setRange(0, 10);

const allDDs = ["makeDD", "modelDD", "flagDD"].map(id => document.getElementById(id));
allDDs.forEach(dd => {
  dd.querySelector("button").onclick = e => {
    e.stopPropagation();
    allDDs.forEach(x => { if (x !== dd) x.classList.remove("open"); });
    dd.classList.toggle("open");
  };
});
document.addEventListener("click", e => { allDDs.forEach(dd => { if (!dd.contains(e.target)) dd.classList.remove("open"); }); });
const dd = document.getElementById("flagDD");
document.getElementById("flagMenu").addEventListener("change", () => {
  const on = [...document.querySelectorAll("#flagMenu input")].filter(b => b.checked).map(b => b.value);
  state.flags = new Set(on);
  const names = { valid: "no flags", salvage: "rebuilt", suspect: "scam risk" };
  document.getElementById("flagBtn").textContent = "Title status: " +
    (on.length === 3 ? "all" : on.length === 0 ? "none" : on.map(v => names[v]).join(", "));
  render();
});
render();
</script>
</body>
</html>"""

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=os.path.join(os.path.dirname(__file__), "..", "data"))
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "dashboard.html"))
    a = ap.parse_args()
    build(a.data_dir, a.out)
