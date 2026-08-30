#!/usr/bin/env python3
"""Lincoln-Omaha full-size 3-row SUV refresh. Routes IA finds near Des Moines
to the Des Moines board. Cache-first; appends only new listings."""
import json, re, glob, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from enrich_listing import enrich
import build_dashboard as bd
from build_combined import DSM_MI, LINCOLN_EXTRA

T = {
 "suburban":  ({2015:17000,2016:19000,2017:21000,2018:23000,2019:25500,2020:28000,2021:32000,2022:36000,2023:40000,2024:45000},
               {"ltz":2500,"premier":2500,"high country":4500,"z71":3000,"rst":2000,"ls":-1500}, ("Chevrolet","Suburban")),
 "tahoe":     ({2015:16000,2016:18000,2017:20000,2018:22000,2019:24500,2020:27500,2021:31000,2022:35000,2023:39000,2024:44000},
               {"ltz":2500,"premier":2500,"high country":4500,"z71":3000,"rst":2000,"ls":-1500}, ("Chevrolet","Tahoe")),
 "yukon":     ({2015:16500,2016:18500,2017:20500,2018:22500,2019:25000,2020:28000,2021:33000,2022:38000,2023:43000,2024:48000},
               {"denali":3000,"at4":2500,"slt":1000,"sle":-2000,"xl":500}, ("GMC","Yukon")),
 "expedition":({2015:13000,2016:14500,2017:16000,2018:21000,2019:23500,2020:26000,2021:29000,2022:32000,2023:37000,2024:41000},
               {"limited":3000,"platinum":5000,"king ranch":5000,"timberline":3000,"max":1000,"xl ":-2000,"xlt":1000}, ("Ford","Expedition")),
 "sequoia":   ({2014:17000,2015:19000,2016:21000,2017:23000,2018:25000,2019:27000,2020:30000,2021:33000},
               {"limited":3000,"platinum":4000,"trd pro":6000,"sr5":0}, ("Toyota","Sequoia")),
 "armada":    ({2015:11000,2016:13500,2017:14000,2018:16000,2019:18500,2020:21500,2021:23500,2022:26500,2023:30000,2024:34000},
               {"sl":1500,"platinum":2500,"reserve":3500}, ("Nissan","Armada")),
 "escalade":  ({2014:23000,2015:26000,2016:28500,2017:30000,2018:33000,2019:36000,2020:42000,2021:50000},
               {"esv":1500,"platinum":3000,"premium":1500,"luxury":1000,"sport":2000}, ("Cadillac","Escalade")),
 "navigator": ({2017:24000,2018:35000,2019:38000,2020:42000,2021:47000,2022:52000},
               {"reserve":2000,"black label":5000,"l":1000}, ("Lincoln","Navigator")),
 "qx80":      ({2019:26000,2020:29000,2021:33000,2022:37000,2023:41000,2024:45000},
               {"luxe":500,"premium select":1500,"limited":2000,"sensory":1500}, ("Infiniti","QX80")),
}
DETECT = [("suburban", r"suburban"), ("tahoe", r"tahoe"), ("yukon", r"yukon"),
          ("expedition", r"expedition"), ("sequoia", r"sequoia"), ("armada", r"armada"),
          ("escalade", r"escalade"), ("navigator", r"navigator"), ("qx80", r"qx80")]
EXCLUDE = re.compile(r"wagoneer|traverse|explorer|silverado|sierra|terrain|canyon|colorado|tundra|2500|3500|\bhd\b|199\d|200[0-9]\b|201[0-3]\b|\b2025\b|\b2026\b", re.I)
EXTRA_MI = {"Norfolk, NE":95,"Columbus, NE":75,"Grand Island, NE":95,"Falls City, NE":90,
 "Wayne, NE":100,"Seneca, KS":90,"Harlan, IA":90,"Atlantic, IA":105,"Treynor, IA":65,
 "Neola, IA":70,"Elk Horn, IA":90,"Sioux City, IA":100,"South Sioux City, NE":100,
 "Dakota City, NE":100,"Red Oak, IA":75,"Blue Rapids, KS":95,"Plattsmouth, NE":55,
 "Bennington, NE":50,"Elkhorn, NE":47,"Papillion, NE":50,"Bellevue, NE":55,"Seward, NE":26,
 "St Paul, NE":110,"Nebraska City, NE":45}

def main():
    cache = json.load(open("/root/carhunt/data/listing_cache.json"))
    lin = json.load(open("/root/carhunt/data/listings.json"))
    dsm = json.load(open("/root/carhunt/data/desmoines_listings.json"))
    have = {l["id"] for l in lin} | {l["id"] for l in dsm} | set(cache.keys())
    lin_city = dict(list(bd.CITY_MI.items()) + list(LINCOLN_EXTRA.items()) + list(EXTRA_MI.items()))
    seen, new_lin, new_dsm, skipped = set(), [], [], {"dupe":0,"excl":0,"year":0,"price":0,"nomatch":0,"dist":0,"known":0}
    for path in sorted(glob.glob("/root/carhunt/rawrefresh/*.json")):
        for it in json.load(open(path)):
            i = it["i"]
            if i in seen: skipped["dupe"] += 1; continue
            seen.add(i)
            if i in have: skipped["known"] += 1; continue
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
            if not year or year > 2024:
                if year is None and price and 20000 <= price <= 50000: year = None
                skipped["year"] += 1; continue
            if not price or not (20000 <= price <= 50000): skipped["price"] += 1; continue
            key = next((k for k, pat in DETECT if re.search(pat, tl)), None)
            if not key: skipped["nomatch"] += 1; continue
            d_lin = lin_city.get(loc, 60 if loc.endswith("NE") else None)
            d_dsm = DSM_MI.get(loc)
            if d_lin is not None and d_lin <= 105: dest, region, first = new_lin, None, "lincoln"
            elif d_dsm is not None and d_dsm <= 105: dest, region, first = new_dsm, "desmoines", "desmoines"
            else: skipped["dist"] += 1; continue
            base, trims, (mk, model) = T[key]
            trim = next((t for t in sorted(trims, key=len, reverse=True) if t.strip() in tl), None)
            ys = sorted(base); y0 = min(ys, key=lambda x: abs(x-year))
            mv = base.get(year, base[y0] + (year-y0)*2500)
            if trim: mv += trims[trim]
            if key == "yukon" and "xl" in tl: model = "Yukon XL"
            mm = re.search(r"([\d,]{4,7})\s*(?:miles|mi\b)", title, re.I)
            mi = int(mm.group(1).replace(",","")) if mm else None
            notes = []
            if old and old < 200000: notes.append(f"price drop from ${old:,}")
            l = {"id": i, "title": title, "price": price, "year": year, "make": mk, "model": model,
                 "trim": (trim or "").strip().title() or None, "mileage": mi, "category": "suv",
                 "location": loc, "url": f"https://www.facebook.com/marketplace/item/{i}/",
                 "image": None, "first_seen": "2026-08-30",
                 "market_value": int(round(mv, -2)),
                 "value_source": "trim/year value table (KBB/Edmunds-anchored)",
                 "value_confidence": "medium" if trim else "low", "notes": "; ".join(notes)}
            if region: l["region"] = region
            if l["mileage"] is not None:
                typical = (2026.5 - year) * 13000
                adj = max(-l["market_value"]*0.25, min(l["market_value"]*0.25, (typical - l["mileage"]) * 0.08))
                l["market_value"] = int(round(l["market_value"] + adj, -2))
            if l["mileage"] is not None and l["mileage"] > 150000: continue
            enrich(l)
            dest.append(l)
    # dupe tagging within new batches
    for board, new in [(lin, new_lin), (dsm, new_dsm)]:
        seen2 = {(x["title"].lower(), x["price"], x.get("mileage")): x["id"] for x in board}
        for l in new:
            k = (l["title"].lower(), l["price"], l.get("mileage"))
            if k in seen2:
                l["notes"] = (l.get("notes") or "") + ("; " if l.get("notes") else "") + f"duplicate listing of {seen2[k]}"
            else: seen2[k] = l["id"]
        board.extend(new)
    json.dump(lin, open("/root/carhunt/data/listings.json","w"), indent=1)
    json.dump(dsm, open("/root/carhunt/data/desmoines_listings.json","w"), indent=1)
    for l in new_lin + new_dsm:
        cache[l["id"]] = {"title": l["title"], "mileage": l.get("mileage"), "notes": l.get("notes"),
                          "market_value": l.get("market_value"), "last_seen": "2026-08-30",
                          "region": l.get("region","lincoln"), "description": l.get("description")}
    json.dump(cache, open("/root/carhunt/data/listing_cache.json","w"), indent=1)
    print(f"lincoln +{len(new_lin)} -> {len(lin)} | desmoines +{len(new_dsm)} -> {len(dsm)} | skipped {skipped}")
    pri = [(l["id"], round(l["price"]/l["market_value"],2), l["title"][:45], l["location"])
           for l in new_lin + new_dsm if l.get("mileage") is None and l["price"] <= 0.92*l["market_value"]]
    json.dump(pri, open("/tmp/refresh_pri.json","w"), indent=1)
    print(f"priority sweep: {len(pri)}")
    for x in sorted(pri, key=lambda x: x[1]): print(" ", x)

if __name__ == "__main__":
    main()
