#!/usr/bin/env python3
"""Build the combined all-markets CarHunt board (index.html).

Merges the Lincoln-Omaha, Denver, and Kansas City datasets into one list,
tags each listing with its metro market, precomputes distance from each
listing's OWN metro hub (so FlipScore proximity stays fair per market),
and renders one dashboard with a Market dropdown filter.
"""
import json, os, shutil, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_dashboard as bd

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

DENVER_MI = {"Denver, CO":0,"Aurora, CO":10,"Lakewood, CO":8,"Thornton, CO":10,"Arvada, CO":10,
 "Westminster, CO":10,"Centennial, CO":15,"Englewood, CO":8,"Littleton, CO":12,"Lone Tree, CO":18,
 "Parker, CO":22,"Castle Rock, CO":30,"Golden, CO":15,"Commerce City, CO":10,"Brighton, CO":22,
 "Broomfield, CO":18,"Boulder, CO":27,"Louisville, CO":22,"Longmont, CO":35,"Berthoud, CO":45,
 "Loveland, CO":50,"Fort Collins, CO":62,"Windsor, CO":60,"Greeley, CO":55,"Johnstown, CO":48,
 "Dacono, CO":30,"Erie, CO":25,"Fort Lupton, CO":30,"Monument, CO":50,"Colorado Springs, CO":70,
 "Penrose, CO":105,"Strasburg, CO":40,"Franktown, CO":30,"Kremmling, CO":90,"Avon, CO":100,
 "Limon, CO":75,"Cheyenne, WY":100}
KC_MI = {"Kansas City, MO":0,"Kansas City, KS":5,"Overland Park, KS":12,"Olathe, KS":20,
 "Lenexa, KS":15,"Shawnee, KS":12,"Mission, KS":10,"Leawood, KS":12,"Stilwell, KS":25,
 "Paola, KS":40,"De Soto, KS":30,"Ottawa, KS":55,"Lawrence, KS":40,"Topeka, KS":60,
 "Leavenworth, KS":30,"Lansing, KS":28,"Bonner Springs, KS":20,"Atchison, KS":45,
 "Emporia, KS":95,"Independence, MO":12,"Blue Springs, MO":20,"Lee's Summit, MO":18,
 "Grain Valley, MO":25,"Oak Grove, MO":30,"Raytown, MO":10,"Grandview, MO":12,"Belton, MO":17,
 "Peculiar, MO":30,"Pleasant Hill, MO":32,"Harrisonville, MO":35,"Butler, MO":65,"Odessa, MO":40,
 "Higginsville, MO":50,"Sedalia, MO":90,"La Monte, MO":80,"Marshall, MO":80,"Warsaw, MO":90,
 "Clinton, MO":75,"Appleton City, MO":75,"Liberty, MO":15,"Kearney, MO":25,"Gower, MO":35,
 "Platte City, MO":25,"St Joseph, MO":55,"Savannah, MO":65,"Osborn, MO":55,"Cameron, MO":50,
 "Kingston, MO":60,"Chillicothe, MO":85,"Nevada, MO":100}
LINCOLN_EXTRA = {"Beatrice, NE":40,"Fairbury, NE":65,"Sutton, NE":75,"Missouri Valley, IA":85,
 "Council Bluffs, IA":60,"Carter Lake, IA":60,"South Bend, NE":35,"Bennington, NE":50,
 "Waverly, NE":12,"Mead, NE":30,"Waterloo, NE":42,"Adams, NE":25,"Marysville, KS":62,
 "Fremont, NE":55,"Columbus, NE":75,"Plattsmouth, NE":55,"La Vista, NE":50,
 "Springfield, NE":50,"Valparaiso, NE":20,"Wahoo, NE":30,"Denton, NE":10,"Gretna, NE":45,
 "Geneva, NE":55,"Albion, NE":110,"Crete, NE":25,"Norfolk, NE":95}
DSM_MI = {"Des Moines, IA":0,"West Des Moines, IA":8,"Clive, IA":8,"Urbandale, IA":8,
 "Johnston, IA":10,"Ankeny, IA":12,"Altoona, IA":12,"Pleasant Hill, IA":8,"Norwalk, IA":12,
 "Waukee, IA":12,"Grimes, IA":12,"Carlisle, IA":12,"Indianola, IA":20,"Adel, IA":20,
 "Perry, IA":30,"Winterset, IA":35,"Newton, IA":35,"Ames, IA":35,"Boone, IA":45,
 "Story City, IA":45,"Pella, IA":45,"Knoxville, IA":40,"Osceola, IA":45,"Marshalltown, IA":55,
 "Grinnell, IA":55,"Chariton, IA":55,"Oskaloosa, IA":60,"Albia, IA":70,"Creston, IA":75,
 "Carroll, IA":85,"Audubon, IA":75,"Ottumwa, IA":85,"Fort Dodge, IA":90}

MARKETS = [
    ("listings.json",           "Lincoln–Omaha Metro",  dict(list(bd.CITY_MI.items()) + list(LINCOLN_EXTRA.items())),
     {"NE":70,"IA":120,"KS":200,"MO":220,"SD":175}),
    ("denver_listings.json",    "Denver Metro",         DENVER_MI, {"CO":60,"WY":110}),
    ("kc_listings.json",        "Kansas City Metro",    KC_MI,     {"MO":60,"KS":60}),
    ("desmoines_listings.json", "Des Moines Metro",     DSM_MI,    {"IA":60}),
]

def main():
    combined, seen = [], set()
    counts = {}
    for fname, label, city_mi, state_mi in MARKETS:
        path = os.path.join(DATA, fname)
        if not os.path.exists(path):
            print(f"WARNING: {fname} missing, skipping"); continue
        n = 0
        for l in json.load(open(path)):
            if l["id"] in seen: continue
            seen.add(l["id"])
            l = dict(l)
            l["market"] = label
            loc = l.get("location") or ""
            if loc in city_mi:
                l["_dist"] = city_mi[loc]
            else:
                st = loc.rsplit(",", 1)[-1].strip()
                l["_dist"] = state_mi.get(st, 150)
            combined.append(l); n += 1
        counts[label] = n
    json.dump(combined, open(os.path.join(DATA, "all_listings.json"), "w"), indent=1)

    # distance scoring inside build() falls back to CITY_MI only when _dist is
    # missing; every combined listing carries _dist, so leave bd tables alone.
    tmp = tempfile.mkdtemp(prefix="carhunt_all")
    cfg = json.load(open(os.path.join(DATA, "config.json")))
    cfg["location"] = dict(cfg.get("location") or {})
    cfg["location"]["city"] = "Lincoln–Omaha · Denver · Kansas City · Des Moines"
    cfg["location"]["radius_miles"] = 100
    cfg["scope_label"] = "All markets — 3-row SUVs + Ram 1500 + Sierra 1500 · thru 2024 · $20k–$50k"
    json.dump(cfg, open(os.path.join(tmp, "config.json"), "w"))
    shutil.copy(os.path.join(DATA, "all_listings.json"), os.path.join(tmp, "listings.json"))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.html")
    bd.build(tmp, out)
    print("per-market:", counts)

if __name__ == "__main__":
    main()
