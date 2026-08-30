#!/usr/bin/env python3
"""GMC Sierra 1500 expansion: appends Sierras to every market's dataset.

rawsierra/{lincoln,denver,kc,desmoines}.json -> data/{listings,denver_listings,
kc_listings,desmoines_listings}.json. Sierra 1500 only (HD/2500/3500 excluded),
$20k-$50k, years <= 2024, cache-first (never re-scrapes known listings).
"""
import json, re, glob, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from enrich_listing import enrich

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rawsierra")

# Sierra 1500 private-party anchors by trim/year (KBB/Edmunds-calibrated).
# 2019+ = current gen (T1); 2014-2018 = prior gen (K2) runs ~$3-6k lighter.
SIERRA = {
 "pro":      {2019:20000,2020:22000,2021:24500,2022:27000,2023:29500,2024:32500},
 "sle":      {2014:14000,2015:15500,2016:17000,2017:18500,2018:20500,2019:23000,2020:25000,2021:27500,2022:30000,2023:33000,2024:36000},
 "elevation":{2015:15000,2016:16500,2017:18000,2018:20000,2019:24000,2020:26000,2021:28500,2022:31000,2023:34000,2024:37000},
 "slt":      {2014:16000,2015:17500,2016:19000,2017:20500,2018:23000,2019:26000,2020:28500,2021:31000,2022:34000,2023:37000,2024:40000},
 "at4":      {2019:29000,2020:31500,2021:34000,2022:37000,2023:40000,2024:43500},
 "at4x":     {2022:44000,2023:48000},
 "denali":   {2014:18500,2015:20000,2016:22000,2017:24000,2018:26000,2019:31000,2020:33500,2021:36500,2022:40000,2023:43500,2024:47000},
 "sl":       {2019:21000,2020:23000,2021:25500,2022:28000,2023:30500,2024:33500},
}
TRIM_ORDER = ["denali ultimate","at4x","denali","at4","elevation","slt","sle","pro","sl"]
EXCLUDE = re.compile(r"2500|3500|\bhd\b|sierra hd|silverado|f-?150|ram\b|tundra|titan|dually|199\d|200[0-9]\b|201[0-3]\b|\b2025\b|\b2026\b", re.I)

MARKETS = [
    ("lincoln.json",   "listings.json",           None,      "2026-08-13"),
    ("denver.json",    "denver_listings.json",    "denver",  "2026-08-13"),
    ("kc.json",        "kc_listings.json",        "kc",      "2026-08-13"),
    ("desmoines.json", "desmoines_listings.json", "desmoines","2026-08-13"),
]
DSM_MI = {"Des Moines, IA":0,"West Des Moines, IA":8,"Clive, IA":8,"Urbandale, IA":8,
 "Johnston, IA":10,"Ankeny, IA":12,"Altoona, IA":12,"Pleasant Hill, IA":8,"Norwalk, IA":12,
 "Waukee, IA":12,"Grimes, IA":12,"Carlisle, IA":12,"Indianola, IA":20,"Adel, IA":20,
 "Perry, IA":30,"Winterset, IA":35,"Newton, IA":35,"Ames, IA":35,"Boone, IA":45,
 "Story City, IA":45,"Pella, IA":45,"Knoxville, IA":40,"Osceola, IA":45,"Marshalltown, IA":55,
 "Grinnell, IA":55,"Chariton, IA":55,"Oskaloosa, IA":60,"Albia, IA":70,"Creston, IA":75,
 "Carroll, IA":85,"Audubon, IA":75,"Ottumwa, IA":85,"Fort Dodge, IA":90}

def main():
    cache = json.load(open(os.path.join(DATA, "listing_cache.json")))
    summary = {}
    for raw_name, data_name, region, today in MARKETS:
        raw_path = os.path.join(RAW, raw_name)
        if not os.path.exists(raw_path): continue
        data_path = os.path.join(DATA, data_name)
        board = json.load(open(data_path)) if os.path.exists(data_path) else []
        have = {l["id"] for l in board}
        new, skipped = [], 0
        for it in json.load(open(raw_path)):
            i = it["i"]
            if i in have: skipped += 1; continue
            parts = [x for x in it["t"].split("|") if x and x != "Just listed"]
            prices = [int(x.replace("$","").replace(",","")) for x in parts if re.fullmatch(r"\$[\d,]+", x)]
            price = prices[0] if prices else None
            old = prices[1] if len(prices) > 1 and prices[1] > (prices[0] or 0) else None
            txt = [x for x in parts if not re.fullmatch(r"\$[\d,]+", x)]
            title = txt[0] if txt else ""
            loc = txt[1] if len(txt) > 1 else ""
            tl = title.lower()
            if EXCLUDE.search(tl): skipped += 1; continue
            ym = re.search(r"\b(20[0-2]\d)\b", title)
            year = int(ym.group(0)) if ym else None
            if not year or year > 2024: skipped += 1; continue
            if not price or not (20000 <= price <= 50000): skipped += 1; continue
            if "sierra" not in tl and "denali" not in tl: skipped += 1; continue
            trim = next((t for t in TRIM_ORDER if t in tl), None)
            key = (trim or "sle")
            key = "denali" if key == "denali ultimate" else key
            base = SIERRA.get(key, SIERRA["sle"])
            ys = sorted(base); y0 = min(ys, key=lambda x: abs(x-year))
            mv = base.get(year, base[y0] + (year-y0)*2200)
            mm = re.search(r"([\d,]{4,7})\s*(?:miles|mi\b)", title, re.I) or re.search(r"(\d{2,3})k\s*mi", title, re.I)
            mi = None
            if mm:
                v = mm.group(1).replace(",","")
                mi = int(v) * (1000 if len(v) <= 3 else 1)
            notes = []
            if old and old < 200000: notes.append(f"price drop from ${old:,}")
            l = {"id": i, "title": title, "price": price, "year": year, "make": "GMC", "model": "Sierra 1500",
                 "trim": (trim or "").title().replace("At4","AT4").replace("Slt","SLT").replace("Sle","SLE").replace("Sl","SL") or None,
                 "mileage": mi, "category": "truck", "location": loc,
                 "url": f"https://www.facebook.com/marketplace/item/{i}/",
                 "image": None, "first_seen": today,
                 "market_value": int(round(mv, -2)),
                 "value_source": "trim/year value table (KBB/Edmunds-anchored)",
                 "value_confidence": "medium" if trim else "low", "notes": "; ".join(notes)}
            if region: l["region"] = region
            c = cache.get(i)
            if c:
                if c.get("mileage") is not None and l["mileage"] is None: l["mileage"] = c["mileage"]
                if c.get("notes"): l["notes"] = (c["notes"] + ("; " + l["notes"] if l["notes"] else ""))
                if c.get("description"): l["description"] = c["description"]
            if l["mileage"] is not None:
                typical = (2026.5 - year) * 13000
                adj = max(-l["market_value"]*0.25, min(l["market_value"]*0.25, (typical - l["mileage"]) * 0.08))
                l["market_value"] = int(round(l["market_value"] + adj, -2))
            if l["mileage"] is not None and l["mileage"] > 150000: skipped += 1; continue
            enrich(l, l.get("description"))
            new.append(l); have.add(i)
        # duplicate tagging within the new batch + against board
        seen = {(x["title"].lower(), x["price"], x.get("mileage")): x["id"] for x in board}
        for l in new:
            k = (l["title"].lower(), l["price"], l.get("mileage"))
            if k in seen:
                l["notes"] = (l.get("notes") or "") + ("; " if l.get("notes") else "") + f"duplicate listing of {seen[k]}"
            else:
                seen[k] = l["id"]
        board.extend(new)
        json.dump(board, open(data_path, "w"), indent=1)
        for l in new:
            cache[l["id"]] = {"title": l["title"], "mileage": l.get("mileage"), "notes": l.get("notes"),
                              "market_value": l.get("market_value"), "last_seen": today,
                              "region": region or "lincoln", "description": l.get("description")}
        summary[data_name] = (len(new), skipped, len(board))
    json.dump(cache, open(os.path.join(DATA, "listing_cache.json"), "w"), indent=1)
    for k, (n, s, tot) in summary.items():
        print(f"{k}: +{n} sierras (skipped {s}) -> {tot} total")
    # priority sweep list: null-mileage sierras priced <= 0.92x book
    pri = []
    for _, data_name, _, _ in MARKETS:
        p = os.path.join(DATA, data_name)
        if not os.path.exists(p): continue
        for l in json.load(open(p)):
            if l.get("model") == "Sierra 1500" and l.get("mileage") is None and l["price"] <= 0.92*l["market_value"]:
                pri.append((l["id"], round(l["price"]/l["market_value"],2), l["title"][:50], l["location"]))
    json.dump(pri, open("/tmp/sierra_pri.json", "w"), indent=1)
    print(f"priority sweep (deals w/o mileage): {len(pri)}")
    for x in sorted(pri, key=lambda x: x[1]): print(" ", x)

if __name__ == "__main__":
    main()
