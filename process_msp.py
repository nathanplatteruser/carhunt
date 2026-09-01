#!/usr/bin/env python3
"""Minneapolis-St. Paul board: GUARANTEED-3rd-row full-size SUVs ONLY,
$20k-$50k, <=2024, within ~50 mi of Minneapolis.

Differences from the other markets by design (Nathan's spec):
- No pickups, no Ram/Sierra, no trim-dependent 3-rows (Durango/Acadia) -
  every model here ships with a 3rd row on every config.
- 50-mile radius enforced via the distance table (FB's metro search
  over-reaches, so rows beyond ~52 mi are dropped).
Value tables are shared with the KC processor (same KBB/Edmunds anchors).
"""
import json, re, glob, sys
sys.path.insert(0, "/root/carhunt/scripts")
from enrich_listing import enrich
import process_kc as kc  # reuse T value tables

DETECT = [(k, p) for k, p in kc.DETECT if k != "ram"]  # guaranteed-3rd-row models only
EXCLUDE = re.compile(kc.EXCLUDE.pattern + r"|\bram\b|tundra|4runner|qx60|durango|acadia|traverse|suburban hd|ppv", re.I)

# Distance from Minneapolis city center (miles). >52 = outside the 50-mi spec.
MSP_MI = {"Minneapolis, MN":0,"St Paul, MN":10,"Bloomington, MN":10,"Edina, MN":8,
 "Hopkins, MN":8,"Crystal, MN":8,"Roseville, MN":8,"Eden Prairie, MN":15,"Burnsville, MN":15,
 "Plymouth, MN":12,"Maple Grove, MN":15,"Brooklyn Park, MN":12,"Blaine, MN":15,"Osseo, MN":13,
 "Champlin, MN":15,"Coon Rapids, MN":17,"Anoka, MN":20,"Andover, MN":22,"Ramsey, MN":22,
 "Elk River, MN":30,"Otsego, MN":30,"St Michael, MN":25,"Rockford, MN":25,"Buffalo, MN":30,
 "Monticello, MN":40,"Big Lake, MN":38,"Princeton, MN":45,"Waconia, MN":30,"Chaska, MN":22,
 "Shakopee, MN":22,"Prior Lake, MN":25,"Savage, MN":18,"Jordan, MN":32,"Lakeville, MN":22,
 "Farmington, MN":27,"Rosemount, MN":20,"Apple Valley, MN":18,"Eagan, MN":12,
 "Inver Grove Heights, MN":12,"Hastings, MN":25,"Woodbury, MN":15,"Lake Elmo, MN":18,
 "Oakdale, MN":14,"Maplewood, MN":12,"White Bear Lake, MN":15,"Hugo, MN":22,
 "Stillwater, MN":22,"Forest Lake, MN":28,"Cottage Grove, MN":18,"Northfield, MN":40,
 "Faribault, MN":50,"Hudson, WI":22,"River Falls, WI":30,"New Richmond, WI":40,
 "Amery, WI":55,"Milaca, MN":60,"St Cloud, MN":65,"Zumbrota, MN":60,"Owatonna, MN":65,
 "Paynesville, MN":80,"Mankato, MN":80,"Rochester, MN":85,"New Ulm, MN":95,"Willmar, MN":95,
 "New London, MN":100,"Albert Lea, MN":95,"Austin, MN":100,"Askov, MN":100,
 "Chippewa Falls, WI":95,"Bloomer, WI":105,"Hayward, WI":140,"Pine River, MN":150,
 "Sarona, WI":120,"Morristown, MN":55,"Mason City, IA":130,"Iowa Falls, IA":200}

def main():
    cache = json.load(open("/root/carhunt/data/listing_cache.json"))
    seen, out, skipped = set(), [], {"dupe":0,"sold":0,"excl":0,"year":0,"price":0,"nomatch":0,"dist":0}
    for path in sorted(glob.glob("/root/carhunt/rawmsp/*.json")):
        for it in json.load(open(path)):
            i = it["i"]
            if i in seen: skipped["dupe"] += 1; continue
            seen.add(i)
            parts = [x for x in it["t"].split("|") if x and x != "Just listed"]
            is_sold = False
            while parts and re.fullmatch(r"(?i)\s*sold\s*[·•\-]?\s*", parts[0]):
                is_sold = True; parts = parts[1:]
            prices = [int(x.replace("$","").replace(",","")) for x in parts if re.fullmatch(r"\$[\d,]+", x)]
            price = prices[0] if prices else None
            old = prices[1] if len(prices) > 1 and prices[1] > (prices[0] or 0) else None
            txt = [x for x in parts if not re.fullmatch(r"\$[\d,]+", x)]
            title = txt[0] if txt else ""
            loc = txt[1] if len(txt) > 1 else ""
            tl = title.lower()
            is_sold = is_sold or bool(re.search(r"^\s*sold\b", tl))
            if is_sold: skipped["sold"] += 1  # kept on board, tagged SOLD
            if EXCLUDE.search(tl): skipped["excl"] += 1; continue
            ym = re.search(r"\b(20[0-2]\d)\b", title)
            year = int(ym.group(0)) if ym else None
            if not year or year > 2024: skipped["year"] += 1; continue
            if not price or not (20000 <= price <= 50000): skipped["price"] += 1; continue
            key = next((k for k, pat in DETECT if re.search(pat, tl)), None)
            if not key: skipped["nomatch"] += 1; continue
            d = MSP_MI.get(loc, 999)
            if d > 52: skipped["dist"] += 1; continue  # hard 50-mile spec
            base, trims, (mk, model) = kc.T[key]
            trim = next((t for t in sorted(trims, key=len, reverse=True) if t in tl), None)
            ys = sorted(base); y0 = min(ys, key=lambda x: abs(x-year))
            mv = base.get(year, base[y0] + (year-y0)*2500)
            if trim: mv += trims[trim]
            trim_lbl = (trim or "").strip().title() or None
            mm = re.search(r"([\d,]{4,7})\s*(?:miles|mi\b)", title, re.I) or re.search(r"(\d{2,3})k\s*mi", title, re.I)
            mi = None
            if mm:
                v = mm.group(1).replace(",","")
                mi = int(v) * (1000 if len(v) <= 3 else 1)
            notes = []
            if old and old < 200000: notes.append(f"price drop from ${old:,}")
            title = re.sub(r"^\s*sold\s*[·\-:]*\s*", "", title, flags=2)
            l = {"id": i, "title": title, "sold": is_sold, "price": price, "year": year, "make": mk, "model": model,
                 "trim": trim_lbl, "mileage": mi, "category": "suv", "location": loc,
                 "url": f"https://www.facebook.com/marketplace/item/{i}/",
                 "image": None, "first_seen": "2026-09-01", "region": "msp",
                 "market_value": int(round(mv, -2)),
                 "value_source": "trim/year value table (KBB/Edmunds-anchored)",
                 "value_confidence": "medium" if trim_lbl else "low", "notes": "; ".join(notes)}
            c = cache.get(i)
            if c:
                if c.get("mileage") is not None and l["mileage"] is None: l["mileage"] = c["mileage"]
                if c.get("notes"): l["notes"] = (c["notes"] + ("; " + l["notes"] if l["notes"] else ""))
                if c.get("description"): l["description"] = c["description"]
            if l["mileage"] is not None:
                typical = (2026.5 - year) * 13000
                adj = max(-l["market_value"]*0.25, min(l["market_value"]*0.25, (typical - l["mileage"]) * 0.08))
                l["market_value"] = int(round(l["market_value"] + adj, -2))
            if l["mileage"] is not None and l["mileage"] > 150000: continue
            enrich(l, l.get("description"))
            out.append(l)

    json.dump(out, open("/root/carhunt/data/msp_listings.json","w"), indent=1)
    for l in out:
        cache[l["id"]] = {"title": l["title"], "mileage": l.get("mileage"), "notes": l.get("notes"),
                          "market_value": l.get("market_value"), "last_seen": "2026-09-01",
                          "region": "msp", "description": l.get("description")}
    json.dump(cache, open("/root/carhunt/data/listing_cache.json","w"), indent=1)
    nulls = [l["id"] for l in out if l.get("mileage") is None]
    json.dump(nulls, open("/root/carhunt/data/msp_sweep_queue.json","w"), indent=1)
    print(f"msp board: {len(out)} | skipped {skipped} | need sweep: {len(nulls)}")

if __name__ == "__main__":
    main()
