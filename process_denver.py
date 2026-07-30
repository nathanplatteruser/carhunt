#!/usr/bin/env python3
"""Denver board: full-size 3-row SUVs + Ram 1500, $20k-$50k, <=2024, 100mi of Denver."""
import json, re, glob, sys
sys.path.insert(0, "/root/carhunt/scripts")
from enrich_listing import enrich
import build_dashboard as bd

T = {
 "suburban":  ({2015:17000,2016:19000,2017:21000,2018:23000,2019:25500,2020:28000,2021:32000,2022:36000,2023:40000,2024:45000},
               {"ltz":2500,"premier":2500,"high country":4500,"z71":3000,"rst":2000,"ls":-1500}, ("Chevrolet","Suburban")),
 "tahoe":     ({2015:16000,2016:18000,2017:20000,2018:22000,2019:24500,2020:27500,2021:31000,2022:35000,2023:39000,2024:44000},
               {"ltz":2500,"premier":2500,"high country":4500,"z71":3000,"rst":2000,"ls":-1500}, ("Chevrolet","Tahoe")),
 "yukon":     ({2015:16500,2016:18500,2017:20500,2018:22500,2019:25000,2020:28000,2021:33000,2022:38000,2023:43000,2024:48000},
               {"denali":3000,"at4":2500,"slt":1000,"sle":-2000}, ("GMC","Yukon")),
 "expedition":({2015:13000,2016:14500,2017:16000,2018:21000,2019:23500,2020:26000,2021:29000,2022:32000,2023:37000,2024:41000},
               {"limited":3000,"platinum":5000,"king ranch":5000,"max":1000,"el":1000,"xl":-2000,"xlt":1000}, ("Ford","Expedition")),
 "sequoia":   ({2014:17000,2015:19000,2016:21000,2017:23000,2018:25000,2019:27000,2020:30000,2021:33000},
               {"limited":3000,"platinum":4000,"trd pro":6000,"trd sport":2500,"sr5":0}, ("Toyota","Sequoia")),
 "armada":    ({2015:11000,2016:13500,2017:14000,2018:16000,2019:18500,2020:21500,2021:23500,2022:26500,2023:30000,2024:34000},
               {"sl":1500,"platinum":2500,"reserve":3500}, ("Nissan","Armada")),
 "escalade":  ({2014:23000,2015:26000,2016:28500,2017:30000,2018:33000,2019:36000,2020:42000,2021:50000},
               {"esv":1500,"platinum":3000,"premium":1500,"luxury":1000,"sport":2000}, ("Cadillac","Escalade")),
 "navigator": ({2017:24000,2018:35000,2019:38000,2020:42000,2021:47000,2022:52000},
               {"reserve":2000,"black label":5000,"l":1000}, ("Lincoln","Navigator")),
 "qx80":      ({2019:26000,2020:29000,2021:33000,2022:37000}, {"luxe":500,"premium select":1500}, ("Infiniti","QX80")),
}
RAM_DT = {"tradesman": {2019:18500,2020:21000,2021:23000,2022:25000,2023:27000,2024:30000},
          "bighorn":   {2019:21000,2020:23500,2021:26000,2022:28500,2023:31000,2024:34000},
          "laramie":   {2019:24000,2020:26000,2021:28500,2022:31000,2023:34000,2024:37000},
          "longhorn":  {2019:28000,2020:30500,2021:33000,2022:35500,2023:38500},
          "rebel":     {2019:27000,2020:29500,2021:32000,2022:35000,2023:38000},
          "limited":   {2019:30000,2020:33000,2021:36000,2022:39000,2023:42000},
          "sport":     {2019:24000,2020:26500,2021:29000,2022:31500}}
RAM_CL = {"tradesman": {2015:13000,2016:15500,2017:16500,2018:17500,2019:18000,2020:19000,2021:20000,2022:21500},
          "bighorn":   {2015:16000,2016:18000,2017:19500,2018:20500,2019:19500,2020:20500,2021:21500,2022:22500},
          "laramie":   {2015:17500,2016:19500,2017:21500,2018:23000,2019:21000,2020:22000},
          "warlock":   {2019:20000,2020:21000,2021:22000,2022:23500},
          "sport":     {2015:15500,2016:18500,2017:20500,2018:21500}}
DETECT = [("suburban", r"suburban"), ("tahoe", r"tahoe"), ("yukon", r"yukon"),
          ("expedition", r"expedition"), ("sequoia", r"sequoia"), ("armada", r"armada"),
          ("escalade", r"escalade"), ("navigator", r"navigator"), ("qx80", r"qx80"), ("ram", r"\bram\b")]
EXCLUDE = re.compile(r"4runner|pathfinder|telluride|aviator|excursion|dually|3500|2500\b|199\d|200[0-9]\b|201[0-3]\b", re.I)
DENVER_MI = {"Denver, CO":0,"Aurora, CO":10,"Lakewood, CO":8,"Thornton, CO":10,"Arvada, CO":10,
 "Westminster, CO":10,"Centennial, CO":15,"Englewood, CO":8,"Littleton, CO":12,"Lone Tree, CO":18,
 "Parker, CO":22,"Castle Rock, CO":30,"Golden, CO":15,"Commerce City, CO":10,"Brighton, CO":22,
 "Broomfield, CO":18,"Boulder, CO":27,"Louisville, CO":22,"Longmont, CO":35,"Berthoud, CO":45,
 "Loveland, CO":50,"Fort Collins, CO":62,"Windsor, CO":60,"Greeley, CO":55,"Johnstown, CO":48,
 "Dacono, CO":30,"Erie, CO":25,"Fort Lupton, CO":30,"Monument, CO":50,"Colorado Springs, CO":70,
 "Penrose, CO":105,"Strasburg, CO":40,"Franktown, CO":30,"Kremmling, CO":90,"Avon, CO":100,
 "Limon, CO":75,"Cheyenne, WY":100,"Golden, CO":15}

cache = json.load(open("/root/carhunt/data/listing_cache.json"))
seen, out, skipped = set(), [], {"dupe":0,"excl":0,"year":0,"price":0,"nomatch":0,"dist":0}
for path in sorted(glob.glob("/root/carhunt/rawdenver/*.json")):
    for it in json.load(open(path)):
        i = it["i"]
        if i in seen: skipped["dupe"] += 1; continue
        seen.add(i)
        parts = [x for x in it["t"].split("|") if x and x != "Just listed"]
        prices = [int(x.replace("$","").replace(",","")) for x in parts if re.fullmatch(r"\$[\d,]+", x)]
        price = prices[0] if prices else None
        old = prices[1] if len(prices) > 1 and prices[1] > (prices[0] or 0) else None
        txt = [x for x in parts if not re.fullmatch(r"\$[\d,]+", x)]
        title = txt[0] if txt else ""
        loc = txt[1] if len(txt) > 1 else ""
        tl = title.lower()
        if EXCLUDE.search(tl): skipped["excl"] += 1; continue
        ym = re.search(r"\b(20[0-2]\d)\b", title)
        year = int(ym.group(0)) if ym else None
        if not year or year > 2024: skipped["year"] += 1; continue
        if not price or not (20000 <= price <= 50000): skipped["price"] += 1; continue
        key = next((k for k, pat in DETECT if re.search(pat, tl)), None)
        if not key: skipped["nomatch"] += 1; continue
        d = DENVER_MI.get(loc, 60 if loc.endswith("CO") else 999)
        if d > 105: skipped["dist"] += 1; continue
        if key == "ram":
            is_cl = "classic" in tl or "warlock" in tl or year <= 2018
            trim = next((t for t in ["longhorn","warlock","laramie","big horn","bighorn","tradesman","rebel","limited","sport"] if t in tl), "bighorn")
            trim = "bighorn" if trim in ("big horn","bighorn") else trim
            tbl = RAM_CL if is_cl else RAM_DT
            base = tbl.get(trim, tbl["bighorn"])
            ys = sorted(base); y0 = min(ys, key=lambda x: abs(x-year))
            mv = base.get(year, base[y0] + (year-y0)*2000)
            mk, model, trim_lbl = "Ram", "1500", trim.title()
            cat = "truck"
        else:
            base, trims, (mk, model) = T[key]
            trim = next((t for t in sorted(trims, key=len, reverse=True) if t in tl), None)
            ys = sorted(base); y0 = min(ys, key=lambda x: abs(x-year))
            mv = base.get(year, base[y0] + (year-y0)*2500)
            if trim: mv += trims[trim]
            trim_lbl = (trim or "").strip().title() or None
            cat = "suv"
        mm = re.search(r"([\d,]{4,7})\s*miles", title, re.I)
        mi = int(mm.group(1).replace(",","")) if mm else None
        notes = []
        if old and old < 200000: notes.append(f"price drop from ${old:,}")
        l = {"id": i, "title": title, "price": price, "year": year, "make": mk, "model": model,
             "trim": trim_lbl, "mileage": mi, "category": cat, "location": loc,
             "url": f"https://www.facebook.com/marketplace/item/{i}/",
             "image": None, "first_seen": "2026-07-30", "region": "denver",
             "market_value": int(round(mv, -2)),
             "value_source": "trim/year value table (KBB/Edmunds-anchored)",
             "value_confidence": "medium" if trim_lbl else "low", "notes": "; ".join(notes)}
        if l["mileage"] is not None:
            typical = (2026.5 - year) * 13000
            adj = max(-l["market_value"]*0.25, min(l["market_value"]*0.25, (typical - l["mileage"]) * 0.08))
            l["market_value"] = int(round(l["market_value"] + adj, -2))
        if l["mileage"] is not None and l["mileage"] > 150000: continue
        enrich(l)
        out.append(l)

json.dump(out, open("/root/carhunt/data/denver_listings.json","w"), indent=1)
for l in out:
    cache[l["id"]] = {"title": l["title"], "mileage": l.get("mileage"), "notes": l.get("notes"),
                      "market_value": l.get("market_value"), "last_seen": "2026-07-30",
                      "region": "denver", "description": l.get("description")}
json.dump(cache, open("/root/carhunt/data/listing_cache.json","w"), indent=1)
nulls = [l["id"] for l in out if l.get("mileage") is None]
json.dump(nulls, open("/root/carhunt/data/denver_sweep_queue.json","w"), indent=1)
print(f"denver board: {len(out)} | skipped {skipped} | need sweep: {len(nulls)}")
