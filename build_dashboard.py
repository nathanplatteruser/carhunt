#!/usr/bin/env python3
"""Build the CarHunt ledger dashboard from data/listings.json + data/config.json.

Design: product-register inventory ledger. Pure white bg, near-black ink,
amber brand accent (oklch 0.65 0.146 60), tabular-mono figures, sortable table.
No cards, no gradients, no emojis.

Usage: python3 build_dashboard.py [--data-dir DIR] [--out FILE]
"""
import argparse, json, html, os, re, datetime

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

def compose_dm(l):
    """Per-listing seller DM draft: interest + clarifying questions chosen from
    THIS listing's actual gaps and flags. Generated at build time; the dashboard
    only reveals it on click, and nothing is ever sent automatically."""
    name = " ".join(str(x) for x in [l.get("year"), l.get("make"), l.get("model")] if x)
    trim = f" {l['trim']}" if l.get("trim") else ""
    notes = (l.get("notes") or "").lower()
    qs = []
    if l.get("mileage") is None:
        qs.append("How many miles are on it?")
    elif l["mileage"] >= 100000:
        qs.append(f"At {l['mileage']:,} miles, has the regular maintenance been kept up (fluids, brakes, transmission service)?")
    if l.get("flag") == "salvage" or "rebuilt" in notes or "branded" in notes or "salvage" in notes:
        qs.append("I noticed the title is rebuilt/branded - what was the original damage, and do you have photos or repair documentation from the rebuild?")
    else:
        qs.append("Is the title clean and in your name, with no liens?")
    qs.append("Could you send me the VIN so I can run a Carfax/AutoCheck history report before we meet?")
    qs.append("Any accidents, warning lights, or mechanical issues I should know about?")
    if (l.get("deal_pct") or 0) >= 15:
        qs.append("The price looks very fair - is there anything about the condition that's reflected in it?")
    if "duplicate listing" in notes:
        qs.append("I've seen this vehicle posted more than once - are you the owner or selling on consignment?")
    body = "\n".join("- " + q for q in qs[:5])
    return (f"Hi! I saw your listing for the {name}{trim} and I'm interested - is it still available?\n\n"
            f"A few quick questions:\n{body}\n\n"
            "If everything checks out, I'd love to take a look and test drive it this week. "
            "Happy to meet somewhere public whenever works for you. Thanks!")

# ── 3rd-row seating classification ──────────────────────────────────────────
# GUARANTEED: the model ships with a 3rd row on essentially every config, or the
# seller's own description confirms one. SOMETIMES: trim/config dependent —
# verify with the seller. NEVER: physically no 3rd row (pickups).
ROW3_GUARANTEED = ("suburban", "tahoe", "yukon", "expedition", "sequoia", "armada",
                   "escalade", "navigator", "qx80", "traverse", "explorer", "telluride",
                   "palisade", "pilot", "highlander", "ascent", "atlas", "aviator",
                   "enclave", "pathfinder", "wagoneer", "cx-9", "cx9")
ROW3_SOMETIMES = ("durango", "acadia", "sorento", "santa fe", "outlander", "journey",
                  "grand cherokee")
ROW3_NEVER = re.compile(r"\b1500\b|f-?150|silverado|sierra|\bram\b|tundra|titan|ranger|"
                        r"colorado|canyon|frontier|maverick|ridgeline", re.I)
ROW3_DESC = re.compile(r"3rd[\s-]?row|third[\s-]?row|seats?\s*[78]\b|[78][\s-]?passenger|[78][\s-]?seater", re.I)

# ── One-time model spec table (data/model_specs.json) ───────────────────────
# Curated once from factory specs — never re-polled. Ordered match patterns
# (yukon xl before yukon, etc.) -> row3 status, length class, cargo cu-ft
# behind the 3rd row. The regex heuristics below survive only as a fallback
# for models not yet in the table.
_SPECS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "model_specs.json")
try:
    MODEL_SPECS = json.load(open(_SPECS_PATH))["specs"]
except Exception:
    MODEL_SPECS = []

def spec_for(l):
    m = ((l.get("model") or "") + " " + (l.get("title") or "") + " " +
         (l.get("trim") or "")).lower()
    for pat, spec in MODEL_SPECS:
        # word-boundary guard: "navigator l" must NOT match "navigator limited"
        if re.search(re.escape(pat) + r"(?![a-z0-9])", m):
            return spec
    return None

def classify_row3(l):
    if l.get("category") == "truck":
        return "never"
    m = ((l.get("model") or "") + " " + (l.get("title") or "")).lower()
    spec = spec_for(l)
    if spec:
        r = spec["row3"]
        if r == "sometimes":
            desc = (l.get("description") or "") + " " + (l.get("notes") or "") + " " + m
            if ROW3_DESC.search(desc):
                return "guaranteed"  # trim-dependent model, but seller confirms
        return r
    # fallback heuristics for models not in the spec table
    # guaranteed-model check BEFORE the pickup pattern: "Suburban 1500" is a
    # real 3-row SUV name and must not be caught by the bare-1500 pickup match
    if any(g in m for g in ROW3_GUARANTEED):
        return "guaranteed"
    if ROW3_NEVER.search(m):
        return "never"
    desc = (l.get("description") or "") + " " + (l.get("notes") or "") + " " + m
    if ROW3_DESC.search(desc):
        return "guaranteed"  # seller explicitly confirms a 3rd row / 7-8 seats
    return "sometimes"

# ── Body-length / cargo classification ──────────────────────────────────────
# XL: extended-wheelbase full-size — massive cargo BEHIND the 3rd row
# (Suburban ~41 cu ft, Yukon XL ~41, Expedition Max/EL ~36, Escalade ESV ~39,
# Navigator L ~36). STANDARD: full-size with a 3rd row but tight cargo behind
# it (Tahoe/Yukon ~25, Expedition ~19, Escalade ~15, Armada/QX80 ~17,
# Sequoia ~19, Navigator ~19 — a car seat + stroller barely fit). OTHER:
# midsize 3-rows and pickups, where the comparison doesn't apply.
XL_PAT = re.compile(r"suburban|yukon\s*xl|expedition\s*(?:max|el)\b|escalade\s*esv|"
                    r"navigator\s*l\b|extended\s*(?:length|wheelbase)", re.I)
FULLSIZE = ("tahoe", "yukon", "expedition", "escalade", "navigator", "armada",
            "qx80", "sequoia")

def classify_length(l):
    m = ((l.get("model") or "") + " " + (l.get("title") or "") + " " +
         (l.get("trim") or "")).lower()
    spec = spec_for(l)
    if spec:
        # seller text like "extended length" still upgrades a standard row
        if spec["len"] != "xl" and XL_PAT.search(m):
            return "xl", spec.get("cargo3")
        return spec["len"], spec.get("cargo3")
    if XL_PAT.search(m):
        return "xl", None
    if any(f in m for f in FULLSIZE):
        return "standard", None
    return "other", None

# VIN capture: prefer the swept vin field; fall back to a 17-char VIN pattern in
# the stored description/notes (I excludes, O excludes, Q excludes per VIN spec).
VIN_RE = re.compile(r"\b([A-HJ-NPR-Z0-9]{17})\b")
def find_vin(l):
    v = (l.get("vin") or "").strip().upper()
    if len(v) == 17 and not v.isdigit():
        return v
    for src in (l.get("description"), l.get("notes")):
        if not src:
            continue
        m = VIN_RE.search(src.upper())
        if m and not m.group(1).isdigit():
            return m.group(1)
    return None

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
        l["row3"] = classify_row3(l)
        l["len"], l["cargo3"] = classify_length(l)
        # Auction-history link: VIN-keyed saleshistory.org page, generated ONLY
        # for non-clean rows (rebuilt/salvage/scam/lemon) where a VIN was
        # captured — that's where pre-rebuild damage photos change decisions.
        if l["flag"] in ("salvage", "suspect"):
            vin = find_vin(l)
            if vin:
                l["auction_url"] = "https://" + vin.lower() + ".saleshistory.org/"
        # rebuilt/salvage/branded titles are worth ~25% less than clean-title book -
        # applied at render time (idempotent per build) so listings.json stays clean-book.
        # BOTH values are kept: clean_value = what the same vehicle would be worth with a
        # clean title (the functional/comparable value), market_value = as-titled resale.
        if l["flag"] == "salvage" and mv:
            if "haircut" in (l.get("value_source") or ""):
                l["clean_value"] = int(round(mv / 0.75, -2))  # reconstruct pre-haircut book
            else:
                l["clean_value"] = mv
                mv = int(round(mv * 0.75, -2))
                l["market_value"] = mv
                l["value_source"] = (l.get("value_source") or "") + " · 25% rebuilt-title haircut"
        else:
            l["clean_value"] = mv  # clean title: comparable == as-titled
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
        l["dm"] = compose_dm(l)
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

    # SOLD listings stay on the board (raw data transparency) but are tagged in
    # bright red and excluded from deal ratings/counts - they can't be pursued.
    for l in listings:
        if l.get("sold"):
            l["rating_key"], l["rating_label"] = "sold", "SOLD"

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
    trims = sorted({l.get("trim") or "(none)" for l in listings})
    markets = sorted({l.get("market") for l in listings if l.get("market")})
    page = TEMPLATE
    page = page.replace("__MAKES__", json.dumps(makes))
    page = page.replace("__MODELS__", json.dumps(models))
    page = page.replace("__TRIMS__", json.dumps(trims))
    page = page.replace("__MARKETS__", json.dumps(markets))
    page = page.replace("__DATA__", json.dumps(listings))
    page = page.replace("__THRESHOLD__", str(threshold))
    for k, v in {
        "__N__": str(n), "__GREAT__": str(great), "__BEST__": f"{best:.0f}",
        "__SOLDN__": str(sum(1 for l in listings if l.get("sold"))),
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
  .soldtag { display:inline-block; background:#d1242f; color:#fff; font-weight:800; font-size:11px;
    letter-spacing:.6px; padding:1px 8px; border-radius:4px; vertical-align:middle; }
  .xltag { display:inline-block; background:var(--brand-ink); color:#fff; font-weight:800; font-size:10px;
    letter-spacing:.5px; padding:1px 6px; border-radius:4px; vertical-align:middle; cursor:help; }
  .soldhide { display:inline-flex; align-items:center; gap:5px; font-size:13px; color:var(--muted);
    white-space:nowrap; cursor:pointer; }
  .trimcell { font-size:13px; white-space:nowrap; }
  .passbtn { background:none; border:1px solid var(--line, #ccc); color:var(--muted); border-radius:5px;
    cursor:pointer; font-size:12px; line-height:1; padding:3px 7px; margin-left:6px; vertical-align:middle; }
  .passbtn:hover { border-color:#d1242f; color:#d1242f; }
  .passbtn.restoring:hover { border-color:var(--pos, #1a7f37); color:var(--pos, #1a7f37); }
  .msgbtn { background:none; border:1px solid var(--line, #ccc); color:var(--muted); border-radius:5px;
    cursor:pointer; font-size:12px; padding:2px 7px; margin-left:5px; line-height:1.4; }
  .msgbtn:hover { border-color:var(--brand-ink); color:var(--brand-ink); }
  .msgbtn.restoring:hover { border-color:var(--pos, #1a7f37); color:var(--pos, #1a7f37); }
  .passedtoggle.msgtoggle.on { border-color:var(--brand-ink); color:var(--brand-ink); font-weight:650; }
  .passedtoggle { background:none; border:1px solid var(--line, #ccc); color:var(--muted); border-radius:6px;
    cursor:pointer; font-size:13px; padding:5px 10px; white-space:nowrap; }
  .passedtoggle.on { border-color:#d1242f; color:#d1242f; font-weight:650; }
  .status.suspect { background: var(--danger-bg); color: var(--danger-ink); }
  .conf { display: block; margin-top: 4px; color: var(--faint); font-size: 11px; }
  .rec { color: var(--brand-ink); font-weight: 700; cursor: help; }
  .open { font-size: 12.5px; font-weight: 600; white-space: nowrap; }
  .dmbtn { border: 1px solid var(--line-strong); background: var(--bg); color: var(--brand-ink); border-radius: 3px; padding: 4px 8px; font-size: 12px; font-weight: 600; cursor: pointer; white-space: nowrap; }
  .dmbtn:hover { border-color: var(--brand-ink); }
  .dmoverlay { display: none; position: fixed; inset: 0; background: oklch(0.2 0.01 60 / .45); z-index: 40; }
  .dmoverlay.on { display: flex; align-items: center; justify-content: center; padding: 18px; }
  .dmbox { background: var(--bg); border: 1px solid var(--line-strong); border-radius: 6px; width: min(640px, 100%); max-height: 90vh; display: flex; flex-direction: column; box-shadow: 0 12px 40px oklch(0.2 0.01 60 / .25); }
  .dmbox header { display: flex; align-items: center; gap: 10px; padding: 12px 16px; border-bottom: 1px solid var(--line); font-weight: 700; font-size: 14px; }
  .dmbox header .x { margin-left: auto; cursor: pointer; border: none; background: none; font-size: 18px; color: var(--muted); }
  .dmbox .hint { padding: 8px 16px 0; font-size: 12px; color: var(--faint); }
  .dmbox textarea { margin: 10px 16px; min-height: 260px; resize: vertical; border: 1px solid var(--line-strong); border-radius: 4px; padding: 10px; font: 13px/1.5 inherit; color: var(--ink); background: var(--bg); }
  .dmbox .row { display: flex; flex-wrap: wrap; gap: 8px; padding: 0 16px 14px; }
  .dmbox .row button, .dmbox .row a { border: 1px solid var(--line-strong); border-radius: 4px; padding: 8px 14px; font-size: 13px; font-weight: 600; cursor: pointer; text-decoration: none; }
  .dmbox .row .primary { background: var(--brand-ink); border-color: var(--brand-ink); color: #fff; }
  .dmbox .row a { color: var(--brand-ink); background: var(--bg); }
  .dmbox .row .dmyes { background: var(--bg); color: var(--ok-ink); }
  .dmbox .row .dmyes:hover { border-color: var(--pos); color: var(--pos); }
  .dmbox .row .dmno { background: var(--bg); color: var(--muted); }
  .dmbox .row .dmno:hover { border-color: #d1242f; color: #d1242f; }
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
    td.statuscell, td.opencell, td.dmcell { display: inline-block; margin-right: 16px; vertical-align: bottom; }
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
  <span><b>__SOLDN__</b> tagged SOLD</span>
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
  <div class="dd" id="trimDD">
    <button id="trimBtn" type="button" aria-haspopup="true">Trim: all</button>
    <div class="menu" id="trimMenu"></div>
  </div>
  <label class="soldhide" title="Sold listings stay in the data for transparency; check to hide them while hunting active deals"><input type="checkbox" id="hideSold"> Hide sold</label>
  <button type="button" id="passedBtn" class="passedtoggle" title="Listings you've passed on (via the ✕ button on a row). Stored in this browser only - they stay hidden across weekly re-scrapes. Click to review or restore.">Passed: 0</button>
  <button type="button" id="messagedBtn" class="passedtoggle msgtoggle" title="Listings where you've already DM'd the seller (via the ✓ next to Draft DM). Hidden from the main hunt so the board only shows untouched prospects - stored in this browser only, survives weekly re-scrapes. Click to review the sellers you're waiting on, or un-mark one.">Messaged: 0</button>
  <div class="dd" id="flagDD">
    <button id="flagBtn" type="button" aria-haspopup="true">Title status: all</button>
    <div class="menu" id="flagMenu">
      <label><input type="checkbox" value="valid" checked> No red flags</label>
      <label><input type="checkbox" value="salvage" checked> Rebuilt / salvage title</label>
      <label><input type="checkbox" value="suspect" checked> Scam / lemon risk</label>
    </div>
  </div>
  <div class="dd" id="row3DD" title="3rd-row seating status. GUARANTEED = the model always ships with a 3rd row (or the seller's description confirms one) — check only this box and 100% of results have 3rd rows. SOMETIMES = trim/config dependent, verify with the seller. NEVER = physically impossible (pickups).">
    <button id="row3Btn" type="button" aria-haspopup="true">3rd row: all</button>
    <div class="menu" id="row3Menu">
      <label><input type="checkbox" value="guaranteed" checked> GUARANTEED — always has a 3rd row</label>
      <label><input type="checkbox" value="sometimes" checked> SOMETIMES — trim-dependent, ask seller</label>
      <label><input type="checkbox" value="never" checked> NEVER — no 3rd row possible</label>
    </div>
  </div>
  <div class="dd" id="lenDD" title="Cargo space BEHIND the 3rd row — the car-seat-and-stroller (and team-gear) test. XL = extended wheelbase: Suburban / Yukon XL ~41 cu ft, Expedition Max ~36, Escalade ESV ~39 — massive trunk even with all seats up. STANDARD = full-size but tight behind row 3: Tahoe/Yukon ~25, Expedition ~19, Armada/QX80 ~17. MIDSIZE/OTHER = smaller 3-rows and pickups, where the comparison doesn't apply. From a one-time factory-spec table (data/model_specs.json), never re-polled.">
    <button id="lenBtn" type="button" aria-haspopup="true">Cargo: all</button>
    <div class="menu" id="lenMenu">
      <label><input type="checkbox" value="xl" checked> XL — extended length, massive trunk (~36–42 cu ft behind row 3)</label>
      <label><input type="checkbox" value="standard" checked> STANDARD full-size — 3rd row but tight trunk (~15–25 cu ft)</label>
      <label><input type="checkbox" value="other" checked> MIDSIZE / OTHER — smaller 3-rows &amp; pickups</label>
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
      <th data-k="trim" title="Trim package as parsed from the listing (filter with the Trim dropdown above - e.g. keep only Max / Platinum / XL for maximum space)">Trim <span class="dir"></span></th>
      <th data-k="flip_score" class="right" title="FlipScore 0-10: margin vs market + cost per remaining mile + model quality + proximity to its metro hub + listing validity + title status">Score <span class="dir"></span></th>
      <th data-k="mileage" class="right">Miles <span class="dir"></span></th>
      <th data-k="price" class="right">Asking <span class="dir"></span></th>
      <th data-k="market_value" class="right" title="Estimated private-party (Facebook-style) resale value AS TITLED: model/year/trim tables calibrated to KBB private-party + Edmunds appraisal ranges, mileage-adjusted, 25% haircut on rebuilt/branded titles">Est. FB resale <span class="dir"></span></th>
      <th data-k="clean_value" class="right" title="What the SAME vehicle would be worth with a clean title (the functional/comparable value). For rebuilt/salvage rows this shows the clean-title comp and the gap vs the as-titled value; for clean-title rows it equals Est. FB resale.">Clean-title comp <span class="dir"></span></th>
      <th data-k="fb_roi" class="right" title="Margin if you buy at asking and resell privately on Marketplace at est. FB resale: (FB resale − asking) ÷ asking">FB flip ROI <span class="dir"></span></th>
      <th data-k="dealer_roi" class="right" title="Margin if you buy at asking and sell to a dealer. Dealer trade-in est. = FB resale × 0.82–0.88 (KBB/Edmunds trade-in vs private-party ladder; luxury −3pts; branded titles ×0.60 — many dealers won't take them)">Dealer exit <span class="dir"></span></th>
      <th data-k="flag">Status <span class="dir"></span></th>
      <th title="Per-listing seller message draft: interest + clarifying questions (title, VIN for Carfax, mileage, service history) generated from this listing's own data. You review, edit, copy, and send it yourself - nothing is sent automatically.">Reach out</th>
      <th></th>
    </tr></thead>
    <tbody id="rows"></tbody>
  </table>
  <div class="empty" id="empty" style="display:none"><b>No listings match</b>Clear a filter, or run a fresh Marketplace sweep to add inventory.</div>
</div></main>

<div class="dmoverlay" id="dmOverlay" role="dialog" aria-modal="true" aria-label="Seller message draft">
  <div class="dmbox">
    <header><span id="dmTitle">Seller message draft</span><button type="button" class="x" id="dmClose" aria-label="Close">✕</button></header>
    <div class="hint">Drafted from this listing's own data (title status, mileage gaps, VIN check). Edit anything below, then copy and paste it into Facebook Messenger yourself - nothing is sent for you.</div>
    <textarea id="dmText" spellcheck="true"></textarea>
    <div class="row">
      <button type="button" class="primary" id="dmCopy">Copy message</button>
      <a id="dmOpen" href="#" target="_blank" rel="noopener">Open listing ↗</a>
      <span style="flex:1"></span>
      <button type="button" id="dmMessaged" class="dmyes" title="Marks this listing Messaged and closes - it leaves the main hunt and waits under the Messaged button while you wait on the seller's reply.">✓ Yes, messaged seller</button>
      <button type="button" id="dmPass" class="dmno" title="Marks this listing Passed and closes - it leaves the main hunt for good (restore anytime under the Passed button).">✕ No, move to trash</button>
    </div>
  </div>
</div>

<footer><div class="wrap">Estimated market values: KBB / Edmunds private-party anchors adjusted for mileage and title status, cross-checked against local asking-price comps. FlipScore (0.0–10.0) is an internal v1 index: discount vs market (30%) + cost per expected remaining mile (20%) + model quality-for-price (15%) + proximity to the board's home metro (15%) + listing/seller validity (15%) + title status (5%). Hover a score for its breakdown. 10 = slam dunk, 0 = seller wins. Estimates are approximate — inspect in person and verify VIN, title, and history before buying. Never send deposits for a truck you haven't seen.</div></footer>

<script>
const DATA = __DATA__;
const MAKES = __MAKES__;
const MODELS = __MODELS__;
const MARKETS = __MARKETS__;
const STATUS = { valid: "NO FLAGS", salvage: "REBUILT/SALVAGE", suspect: "SCAM RISK" };
const TRIMS = __TRIMS__;
const state = { q: "", market: "all", flags: new Set(["valid","salvage","suspect"]),
  row3: new Set(["guaranteed","sometimes","never"]),
  len: new Set(["xl","standard","other"]), rating: "all", maxP: null,
  sort: { k: "flip_score", d: -1 },
  makeMode: "include", makeSel: new Set(MAKES),
  modelMode: "include", modelSel: new Set(MODELS),
  trimMode: "include", trimSel: new Set(TRIMS),
  hideSold: false, showPassed: false, showMessaged: false,
  sMin: 0, sMax: 10 };

// ── Personal pass list: listing ids the user has dismissed (✕ on a row).
// Stored in localStorage so it survives weekly re-scrapes and republishes;
// per-browser (desktop and phone each keep their own list).
let passed = new Set();
try { passed = new Set(JSON.parse(localStorage.getItem("carhunt_passed") || "[]")); } catch (e) {}
function savePassed() { try { localStorage.setItem("carhunt_passed", JSON.stringify([...passed])); } catch (e) {} }
// ── Messaged list: listing ids where you've already DM'd the seller (✓ next to
// Draft DM). Same mechanics as the pass list — localStorage, survives weekly
// re-scrapes, per-browser — but a separate bucket: passed = "not interested",
// messaged = "in play, waiting on the seller". Both hide from the main hunt.
let messaged = new Set();
try { messaged = new Set(JSON.parse(localStorage.getItem("carhunt_messaged") || "[]")); } catch (e) {}
function saveMessaged() { try { localStorage.setItem("carhunt_messaged", JSON.stringify([...messaged])); } catch (e) {} }
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
      <div class="name"><a href="${l.url}" target="_blank" rel="noopener">${l.sold ? `<span class="soldtag">SOLD</span> ` : ""}${l.title}</a></div>
      <div class="sub">${l.location || "—"}${l.market ? " · " + l.market : ""}${l.title_status_desc ? " · desc: " + l.title_status_desc + " title" : ""}${l.auction_url ? ` · <a href="${l.auction_url}" target="_blank" rel="noopener" title="VIN-keyed auction sale history — pre-rebuild damage photos and sale records for this exact vehicle">Auction history ↗</a>` : ""}</div>
      ${l.notes ? `<div class="note${alert ? " alert" : ""}">${l.notes}</div>` : ""}
    </td>
    <td class="trimcell" data-l="TRIM">${l.trim ? l.trim + rec("trim") : `<span style="color:var(--muted)">—</span>`}${l.len === "xl" ? ` <span class="xltag" title="Extended wheelbase — ~${l.cargo3 || 36} cu ft behind the 3rd row (vs ~15–25 in standard full-size). Massive trunk with all seats up.">XL</span>` : ""}</td>
    <td class="right" data-l="SCORE"><span class="mrow"><span class="score ${l.flip_score >= 7 ? "hi" : l.flip_score >= 4 ? "mid" : "lo"}" title="${l.score_parts || ""}">${l.flip_score.toFixed(1)}</span></span></td>
    <td class="right" data-l="MILES"><span class="mrow"><span class="num">${fmtMi(l.mileage)}${rec("mileage")}</span></span></td>
    <td class="right" data-l="ASKING"><span class="mrow"><span class="num" style="font-weight:650">${fmt(l.price)}</span></span></td>
    <td class="right" data-l="EST. FB RESALE"><span class="mrow"><span class="num" style="color:var(--muted)">${fmt(l.market_value)}</span>${conf}</span></td>
    <td class="right" data-l="CLEAN-TITLE COMP">${l.flag === "salvage" && l.clean_value ? `<span class="mrow"><span class="num" title="clean-title comparable ${fmt(l.clean_value)} vs as-titled ${fmt(l.market_value)}">${fmt(l.clean_value)}</span></span><div class="sub" style="font-size:11px;color:var(--warn-ink)">title gap −${fmt(l.clean_value - l.market_value)}</div>` : `<span class="mrow"><span class="num" style="color:var(--muted)">${l.clean_value ? "=" : "—"}</span></span>`}</td>
    <td class="right" data-l="FB FLIP ROI"><span class="mrow"><span class="delta ${l.fb_roi == null ? "zero" : l.fb_roi >= 3 ? "pos" : l.fb_roi <= -3 ? "neg" : "zero"}" title="resell privately at ${fmt(l.market_value)}">${l.fb_roi == null ? "—" : (l.fb_roi > 0 ? "+" : "") + l.fb_roi.toFixed(0) + "%"}</span>${sav}${bar}</span></td>
    <td class="right" data-l="DEALER EXIT"><span class="mrow"><span class="delta ${l.dealer_roi == null ? "zero" : l.dealer_roi >= 3 ? "pos" : l.dealer_roi <= -3 ? "neg" : "zero"}" title="dealer trade-in est. ${fmt(l.trade_value)}">${l.dealer_roi == null ? "—" : (l.dealer_roi > 0 ? "+" : "") + l.dealer_roi.toFixed(0) + "%"}</span></span></td>
    <td class="statuscell"><span class="status ${l.flag}">${STATUS[l.flag]}</span></td>
    <td class="dmcell"><button type="button" class="dmbtn" data-id="${l.id}">✉ Draft DM</button><button type="button" class="msgbtn${messaged.has(l.id) ? " restoring" : ""}" data-id="${l.id}" title="${messaged.has(l.id) ? "Un-mark messaged - bring this listing back to the main hunt" : "Mark as messaged - you've DM'd this seller, so hide the row from the main hunt (this browser only, survives re-scrapes). Review anytime via the Messaged button above."}">${messaged.has(l.id) ? "↩" : "✓"}</button></td>
    <td class="right opencell"><a class="open" href="${l.url}" target="_blank" rel="noopener">Open ↗</a>
      <button type="button" class="passbtn${passed.has(l.id) ? " restoring" : ""}" data-id="${l.id}" title="${passed.has(l.id) ? "Restore this listing to your hunt" : "Pass on this listing - hides it permanently in this browser, even after weekly re-scrapes"}">${passed.has(l.id) ? "↩" : "✕"}</button></td>
  </tr>`;
}

function render() {
  const q = state.q.toLowerCase();
  const makeOK = l => state.makeMode === "include" ? state.makeSel.has(l.make) : !state.makeSel.has(l.make);
  const modelOK = l => state.modelMode === "include" ? state.modelSel.has(l.model) : !state.modelSel.has(l.model);
  const trimOK = l => { const t = l.trim || "(none)"; return state.trimMode === "include" ? state.trimSel.has(t) : !state.trimSel.has(t); };
  let rows = DATA.filter(l =>
    (state.market === "all" || l.market === state.market)
    && state.flags.has(l.flag)
    && state.row3.has(l.row3 || "sometimes")
    && state.len.has(l.len || "other")
    && makeOK(l) && modelOK(l) && trimOK(l)
    && (!state.hideSold || !l.sold)
    && (state.showPassed ? passed.has(l.id)
        : state.showMessaged ? messaged.has(l.id)
        : (!passed.has(l.id) && !messaged.has(l.id)))
    && l.flip_score >= state.sMin - 1e-9 && l.flip_score <= state.sMax + 1e-9
    && (state.rating === "all" || (state.rating === "great" ? l.rating_key === "great" : ["great","good"].includes(l.rating_key)))
    && (state.maxP == null || (l.price ?? 0) <= state.maxP)
    && (!q || [l.title, l.location, l.trim, l.notes].join(" ").toLowerCase().includes(q)));
  const { k, d } = state.sort;
  rows.sort((a, b) => {
    let x = a[k], y = b[k];
    if (k === "title") { x = a.year ?? 0; y = b.year ?? 0; }
    if (k === "flag" || k === "trim") { x = a[k] || "~"; y = b[k] || "~"; return x < y ? -d : x > y ? d : 0; }
    if (x == null) return 1; if (y == null) return -1;
    return (x - y) * d || (b.flip_score - a.flip_score);
  });
  document.getElementById("rows").innerHTML = rows.map(row).join("");
  document.getElementById("empty").style.display = rows.length ? "none" : "block";
  document.getElementById("count").textContent = rows.length + " of " + DATA.length;
  refreshFacets();
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
    const name = kind === "make" ? "Make" : kind === "model" ? "Model" : "Trim";
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
buildPicker("trim", TRIMS, "trimBtn", "trimMenu");

document.getElementById("hideSold").addEventListener("change", e => { state.hideSold = e.target.checked; render(); });

// pass / restore buttons (event delegation on the table body)
document.getElementById("rows").addEventListener("click", e => {
  const mb = e.target.closest(".msgbtn");
  if (mb) {
    const id = mb.dataset.id;
    if (messaged.has(id)) messaged.delete(id); else messaged.add(id);
    saveMessaged(); updateMessagedBtn(); render();
    return;
  }
  const b = e.target.closest(".passbtn");
  if (!b) return;
  const id = b.dataset.id;
  if (passed.has(id)) passed.delete(id); else passed.add(id);
  savePassed(); updatePassedBtn(); render();
});
const passedBtn = document.getElementById("passedBtn");
function updatePassedBtn() {
  passedBtn.textContent = (state.showPassed ? "← Back to hunt (" : "Passed: ") + passed.size + (state.showPassed ? ")" : "");
  passedBtn.classList.toggle("on", state.showPassed);
}
passedBtn.addEventListener("click", () => {
  state.showPassed = !state.showPassed;
  if (state.showPassed) state.showMessaged = false;  // one review view at a time
  updatePassedBtn(); updateMessagedBtn(); render();
});
const messagedBtn = document.getElementById("messagedBtn");
function updateMessagedBtn() {
  messagedBtn.textContent = (state.showMessaged ? "← Back to hunt (" : "Messaged: ") + messaged.size + (state.showMessaged ? ")" : "");
  messagedBtn.classList.toggle("on", state.showMessaged);
}
messagedBtn.addEventListener("click", () => {
  state.showMessaged = !state.showMessaged;
  if (state.showMessaged) state.showPassed = false;
  updatePassedBtn(); updateMessagedBtn(); render();
});
updatePassedBtn();
updateMessagedBtn();

// ── Cascading facets: a dropdown's options only narrow when ANOTHER facet has
// been ACTIVELY filtered (pick Ford -> models/trims shrink to Ford's; pick
// Platinum -> makes/models shrink to those offering a Platinum row). A facet
// left in its default state (everything included / nothing excluded) imposes
// no constraint, so nothing is gate-kept - you can start filtering at make,
// model, OR trim, in any order.
const FACET_ALL = { make: MAKES, model: MODELS, trim: TRIMS };
function facetVal(l, kind) { return kind === "trim" ? (l.trim || "(none)") : l[kind]; }
function facetOK(l, kind) {
  const sel = state[kind + "Sel"], mode = state[kind + "Mode"], v = facetVal(l, kind);
  return mode === "include" ? sel.has(v) : !sel.has(v);
}
function facetActive(kind) {
  const sel = state[kind + "Sel"], mode = state[kind + "Mode"];
  return mode === "include" ? sel.size < FACET_ALL[kind].length : sel.size > 0;
}
function refreshFacets() {
  const kinds = ["make", "model", "trim"];
  kinds.forEach(kind => {
    const others = kinds.filter(k => k !== kind && facetActive(k));
    const marketOn = state.market !== "all";
    if (!others.length && !marketOn) {  // nothing actively filtered: show every option
      document.querySelectorAll(`#${kind}Menu label`).forEach(lb => lb.style.display = "");
      return;
    }
    const avail = new Set();
    DATA.forEach(l => {
      if ((!marketOn || l.market === state.market) && others.every(k => facetOK(l, k)))
        avail.add(facetVal(l, kind));
    });
    document.querySelectorAll(`#${kind}Menu label`).forEach(lb => {
      const cb = lb.querySelector("input[type=checkbox]");
      if (cb) lb.style.display = avail.has(cb.value) ? "" : "none";
    });
  });
}

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

const allDDs = ["makeDD", "modelDD", "trimDD", "flagDD", "row3DD", "lenDD"].map(id => document.getElementById(id));
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
// ── 3rd-row status filter: NEVER / SOMETIMES / GUARANTEED ──
document.getElementById("row3Menu").addEventListener("change", () => {
  const on = [...document.querySelectorAll("#row3Menu input")].filter(b => b.checked).map(b => b.value);
  state.row3 = new Set(on);
  const names = { guaranteed: "GUARANTEED", sometimes: "SOMETIMES", never: "NEVER" };
  document.getElementById("row3Btn").textContent = "3rd row: " +
    (on.length === 3 ? "all" : on.length === 0 ? "none" : on.map(v => names[v]).join(", "));
  render();
});
// ── Cargo/length filter: XL extended wheelbase vs standard full-size ──
document.getElementById("lenMenu").addEventListener("change", () => {
  const on = [...document.querySelectorAll("#lenMenu input")].filter(b => b.checked).map(b => b.value);
  state.len = new Set(on);
  const names = { xl: "XL", standard: "STANDARD", other: "MIDSIZE/OTHER" };
  document.getElementById("lenBtn").textContent = "Cargo: " +
    (on.length === 3 ? "all" : on.length === 0 ? "none" : on.map(v => names[v]).join(", "));
  render();
});
// ── Seller DM drafts: reveal on click, copy manually - never auto-sent ──
const dmOverlay = document.getElementById("dmOverlay");
const dmText = document.getElementById("dmText");
const dmOpen = document.getElementById("dmOpen");
const dmTitle = document.getElementById("dmTitle");
const dmCopy = document.getElementById("dmCopy");
let dmCurrentId = null;  // listing the open modal belongs to
document.getElementById("rows").addEventListener("click", e => {
  const btn = e.target.closest(".dmbtn");
  if (!btn) return;
  const l = DATA.find(x => String(x.id) === btn.dataset.id);
  if (!l) return;
  dmCurrentId = String(l.id);
  dmTitle.textContent = "Message draft — " + (l.title || "").slice(0, 48);
  dmText.value = l.dm || "";
  dmOpen.href = l.url;
  dmCopy.textContent = "Copy message";
  dmOverlay.classList.add("on");
  dmText.focus();
});
// ── Close the loop from inside the popup: after copy → paste → send on FB,
// come back and answer "did you message them?" without hunting for the row.
document.getElementById("dmMessaged").onclick = () => {
  if (!dmCurrentId) return;
  messaged.add(dmCurrentId); passed.delete(dmCurrentId);
  saveMessaged(); savePassed(); updateMessagedBtn(); updatePassedBtn();
  dmOverlay.classList.remove("on"); render();
};
document.getElementById("dmPass").onclick = () => {
  if (!dmCurrentId) return;
  passed.add(dmCurrentId); messaged.delete(dmCurrentId);
  savePassed(); saveMessaged(); updatePassedBtn(); updateMessagedBtn();
  dmOverlay.classList.remove("on"); render();
};
document.getElementById("dmClose").onclick = () => dmOverlay.classList.remove("on");
dmOverlay.addEventListener("click", e => { if (e.target === dmOverlay) dmOverlay.classList.remove("on"); });
document.addEventListener("keydown", e => { if (e.key === "Escape") dmOverlay.classList.remove("on"); });
dmCopy.onclick = async () => {
  try { await navigator.clipboard.writeText(dmText.value); }
  catch (err) { dmText.select(); document.execCommand("copy"); }
  dmCopy.textContent = "Copied ✓";
  setTimeout(() => dmCopy.textContent = "Copy message", 1600);
};
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
