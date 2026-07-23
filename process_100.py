#!/usr/bin/env python3
"""Build the 100-mile combined board (3-row SUVs + Ram 1500).

Reuses everything already known: archived processed listings (mileage, values,
notes from detail-page checks) and the sweep cache, so only genuinely-new
listings start from scratch. Also builds data/listing_cache.json - the
persistent per-listing knowledge base (descriptions, odometer, title status,
seller age) so future refreshes don't re-scrape what we already know.
"""
import json, re, glob, sys
sys.path.insert(0, "/root/carhunt/scripts")
from enrich_listing import enrich

SUV_T = {
 "suburban":  ({"base": {2015:17000,2016:19000,2017:21000,2018:23000,2019:25500,2020:28000,2021:32000}, "ltz":2500, "premier":2500, "ls":-1500}, ("Chevrolet","Suburban")),
 "tahoe":     ({"base": {2015:16000,2016:18000,2017:20000,2018:22000,2019:24500,2020:27500,2021:31000}, "ltz":2500, "premier":2500, "ls":-1500}, ("Chevrolet","Tahoe")),
 "yukon":     ({"base": {2015:16500,2016:18500,2017:20500,2018:22500,2019:25000,2020:28000}, "denali":3000, "sle":-2000}, ("GMC","Yukon XL")),
 "expedition":({"base": {2015:13000,2016:14500,2017:16000,2018:21000,2019:23500,2020:26000,2021:29000,2022:32000}, "limited":3000, "platinum":5000, "max":1000, "el":1000, "xl":-2000}, ("Ford","Expedition")),
 "sequoia":   ({"base": {2015:19000,2016:21000,2017:23000}, "limited":3000, "platinum":4000}, ("Toyota","Sequoia")),
 "armada":    ({"base": {2015:11000,2016:13500,2017:14000,2018:16000,2019:18500,2020:21500,2021:23500,2022:26500}, "sl":1500, "platinum":2500}, ("Nissan","Armada")),
 "durango":   ({"base": {2015:11000,2016:12500,2017:13500,2018:15000,2019:17000,2020:19000}, "gt":1500, "limited":1000, "citadel":3000, "r/t":4000, "srt":7000}, ("Dodge","Durango")),
 "traverse":  ({"base": {2015:10000,2016:11500,2017:13000,2018:15000,2019:17000,2020:19000,2021:21500,2022:24000,2023:27000}, "premier":3000, "rs":2000, "l ":-2000, "ls":-2000}, ("Chevrolet","Traverse")),
 "explorer":  ({"base": {2015:11000,2016:12500,2017:14000,2018:16000,2019:18000,2020:19500,2021:22000}, "limited":2000, "platinum":4000, "st":4000}, ("Ford","Explorer")),
}
RAM_DT = {"tradesman": {2019:18500,2020:21000,2021:23000,2022:25000,2023:27000}, "bighorn": {2019:21000,2020:23500,2021:26000,2022:28500,2023:31000}, "laramie": {2019:24000,2020:26000,2021:28500,2022:31000}}
RAM_CL = {"tradesman": {2016:15500,2017:16500,2018:17500,2019:18000,2020:19000,2021:20000,2022:21500}, "bighorn": {2016:18000,2017:19500,2018:20500,2019:19500,2020:20500,2021:21500,2022:22500}, "laramie": {2016:19500,2017:21500,2018:23000,2019:21000,2020:22000}, "warlock": {2019:20000,2020:21000,2021:22000,2022:23500}, "sport": {2016:18500,2017:20500,2018:21500}}
NEW_CITY = {"Seward, NE":26,"Palmyra, NE":20,"Bennington, NE":45,"Grand Island, NE":95,"Hastings, NE":100,
 "Nebraska City, NE":45,"Crete, NE":25,"Blair, NE":75,"Madison, NE":110,"Fremont, NE":55,"York, NE":50,
 "David City, NE":45,"Soldier, IA":120,"Seneca, KS":90,"Papillion, NE":50}

# knowledge already gathered this week
arch = {}
for p in ["/root/carhunt/data/listings_suv250_archive.json", "/root/carhunt/data/listings_ram_archive.json"]:
    for l in json.load(open(p)):
        arch[l["id"]] = l
sweep = {}
for p in glob.glob("/root/carhunt/raw/sweep*.json"):
    for r in json.load(open(p)):
        sweep[r["id"]] = r

EXCLUDE = re.compile(r"4runner|highlander|telluride|land cruiser|tundra|lexus|gx460|dogde durango srt", re.I)

out, cache = [], {}
for path in sorted(glob.glob("/root/carhunt/raw100/*.json")):
    key = re.search(r"raw100/(\w+)\.json", path).group(1)
    for it in json.load(open(path)):
        i = it["i"]
        parts = [x for x in it["t"].split("|") if x and x != "Just listed"]
        prices = [int(x.replace("$","").replace(",","")) for x in parts if re.fullmatch(r"\$[\d,]+", x)]
        price = prices[0] if prices else None
        old = prices[1] if len(prices) > 1 and prices[1] > (prices[0] or 0) else None
        txt = [x for x in parts if not re.fullmatch(r"\$[\d,]+", x)]
        title = txt[0] if txt else ""
        loc = txt[1] if len(txt) > 1 else ""
        if EXCLUDE.search(title) and "durango" not in key: continue
        if any(l["id"] == i for l in out): continue
        ym = re.search(r"\b(20[0-2]\d)\b", title)
        year = int(ym.group(0)) if ym else None
        a = arch.get(i)
        if a:  # reuse everything known; refresh price
            l = dict(a)
            if price and price != l["price"]:
                l["notes"] = f"price changed ${l['price']:,} -> ${price:,}; " + (l["notes"] or "")
                l["price"] = price
            out.append(l)
        else:
            if not (price and year and year >= 2015 and 8000 <= price <= 30000): continue
            if key == "ram" and price < 20000: continue
            mm = re.search(r"([\d,]{4,7})\s*miles", title, re.I)
            mi = int(mm.group(1).replace(",","")) if mm else None
            if key == "ram":
                tl = title.lower()
                is_cl = "classic" in tl or year <= 2018
                trim = next((t for t in ["warlock","laramie","big horn","bighorn","tradesman","sport"] if t in tl), "bighorn")
                trim = "bighorn" if trim in ("big horn","bighorn") else trim
                tbl = (RAM_CL if is_cl else RAM_DT)
                base = tbl.get(trim, tbl["bighorn"])
                ys = sorted(base); y0 = min(ys, key=lambda x: abs(x-year))
                mv = base[y0] + (year-y0)*2000
                mk, model, trim_lbl = "Ram", "1500", trim.title()
            else:
                tbl, (mk, model) = SUV_T[key]
                tl = title.lower()
                trim = next((t for t in tbl if t != "base" and t.strip() in tl), None)
                base = tbl["base"]
                ys = sorted(base); y0 = min(ys, key=lambda x: abs(x-year))
                mv = base.get(year, base[y0] + (year-y0)*2500)
                if trim: mv += tbl[trim]
                trim_lbl = (trim or "").strip().title() or None
            conf = "medium" if trim else "low"
            notes = []
            if old: notes.append(f"price drop from ${old:,}")
            l = {"id": i, "title": title, "price": price, "year": year, "make": mk, "model": model,
                 "trim": trim_lbl, "mileage": mi, "category": "truck" if key == "ram" else "suv",
                 "location": loc, "url": f"https://www.facebook.com/marketplace/item/{i}/",
                 "image": None, "first_seen": "2026-07-24",
                 "market_value": int(round(mv, -2)), "value_source": "trim/year value table (KBB/Edmunds-anchored)",
                 "value_confidence": conf, "notes": "; ".join(notes)}
            # apply sweep cache if we have it
            r = sweep.get(i)
            if r:
                if r["mi"] and l["mileage"] is None:
                    l["mileage"] = int(r["mi"].replace(",",""))
                    l["recovered"] = ["mileage:fb-field"]
                ttl = (r["ttl"] or "").lower()
                if "rebuilt" in ttl: l["notes"] = "REBUILT TITLE (FB listing field); " + l["notes"]
                elif "salvage" in ttl: l["notes"] = "SALVAGE TITLE (FB listing field); " + l["notes"]
            if l["mileage"] is not None and year:
                typical = (2026.5 - year) * 13000
                adj = max(-l["market_value"]*0.25, min(l["market_value"]*0.25, (typical - l["mileage"]) * 0.08))
                l["market_value"] = int(round(l["market_value"] + adj, -100 and -2))
            enrich(l)
            out.append(l)

# filters: distance <= 120 (100-mile ask + fuzz), mileage cap
sys.path.insert(0, "/root/carhunt/scripts")
import build_dashboard as bd
bd.CITY_MI.update(NEW_CITY)
final, drop_d, drop_m = [], 0, 0
for l in out:
    d = bd.dist_from_lincoln(l.get("location"))
    if d > 120: drop_d += 1; continue
    if l.get("mileage") is not None and l["mileage"] > 150000: drop_m += 1; continue
    final.append(l)
    cache[l["id"]] = {"title": l["title"], "mileage": l.get("mileage"), "notes": l.get("notes"),
                      "market_value": l.get("market_value"), "last_seen": "2026-07-24",
                      "description": l.get("description")}
json.dump(final, open("/root/carhunt/data/listings.json", "w"), indent=1)
# persistent knowledge base (merge, never overwrite blindly)
try: kb = json.load(open("/root/carhunt/data/listing_cache.json"))
except Exception: kb = {}
kb.update(cache)
json.dump(kb, open("/root/carhunt/data/listing_cache.json", "w"), indent=1)
print(f"final board: {len(final)} (dropped {drop_d} beyond ~100mi, {drop_m} over mileage cap); cache: {len(kb)} entries")
