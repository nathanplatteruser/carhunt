# probe test
#!/usr/bin/env python3
"""Description-recovery layer for CarHunt.

Sellers often skip listing fields (mileage, trim, model, title status) but state
them in the free-text description. This module fills gaps:

  1. Listing fields are the source of truth - unless null or obviously invalid.
     Invalid v1 rules: mileage < 1,000 or > 500,000 ("1 mile", "999999 miles"),
     price < $4,000 ("$200 trucks" are scams or typos).
  2. When a field is null/invalid, fuzzy-match the description and recover it.
  3. Every recovered field is recorded in listing["recovered"] so the dashboard
     can mark it as description-derived rather than seller-entered.

Run directly to self-test and enrich data/listings.json:
    python3 enrich_listing.py [--apply]
"""
import json, re, sys

MAKE_ALIASES = {
    "chevy": "Chevrolet", "chevrolet": "Chevrolet", "gmc": "GMC", "ford": "Ford",
    "toyota": "Toyota", "nissan": "Nissan", "dodge": "Dodge", "ram": "Ram",
    "honda": "Honda", "jeep": "Jeep",
}
MODEL_ALIASES = {
    "suburban": ("Chevrolet", "Suburban"), "tahoe": ("Chevrolet", "Tahoe"),
    "yukon xl": ("GMC", "Yukon XL"), "yukon": ("GMC", "Yukon XL"),
    "expedition": ("Ford", "Expedition"), "sequoia": ("Toyota", "Sequoia"),
    "armada": ("Nissan", "Armada"), "durango": ("Dodge", "Durango"),
    "traverse": ("Chevrolet", "Traverse"), "explorer": ("Ford", "Explorer"),
    "1500": ("Ram", "1500"),
}
TRIMS = ["laramie limited", "big horn", "lone star", "laramie", "denali", "premier",
         "platinum", "limited", "citadel", "tradesman", "warlock", "rebel", "ltz",
         "slt", "sle", "xlt", "lt", "ls", "sr5", "r/t", "gt", "sxt", "sv", "sl"]

def invalid_mileage(v):
    return v is not None and (v < 1000 or v > 500000)

def invalid_price(v):
    return v is not None and v < 4000

def extract_from_text(text):
    """Pull every recoverable field candidate out of free text."""
    t = " " + (text or "").lower().replace("\n", " ") + " "
    out = {}
    # mileage: "167,000 miles", "167k miles", "mileage: 167000"
    m = (re.search(r"([\d]{1,3}(?:,\d{3})+|\d{4,6})\s*(?:miles|mi\b)", t)
         or re.search(r"(\d{2,3})\s*k\s*(?:miles|mi\b)", t)
         or re.search(r"mileage\s*[:\-]?\s*([\d,]{4,7})", t))
    if m:
        v = m.group(1).replace(",", "")
        out["mileage"] = int(v) * (1000 if len(v) <= 3 else 1)
    # price: "asking $12,800", "price: 12800", "$12,800 obo"
    m = re.search(r"(?:asking|price)[^$\d]{0,12}\$?\s*([\d]{1,3}(?:,\d{3})+|\d{4,6})", t) \
        or re.search(r"\$\s*([\d]{1,3}(?:,\d{3})+|\d{4,6})\b", t)
    if m:
        out["price"] = int(m.group(1).replace(",", ""))
    # year: standalone 1995-2026, also trailing ("Suburban LT 2017")
    m = re.search(r"\b(19[89]\d|20[0-2]\d)\b", t)
    if m:
        out["year"] = int(m.group(1))
    # make/model: model wins (implies make); longest alias first
    for alias in sorted(MODEL_ALIASES, key=len, reverse=True):
        if re.search(r"\b" + re.escape(alias) + r"\b", t):
            out["make"], out["model"] = MODEL_ALIASES[alias]
            break
    if "make" not in out:
        for alias, make in MAKE_ALIASES.items():
            if re.search(r"\b" + alias + r"\b", t):
                out["make"] = make
                break
    # trim: longest first so "laramie limited" beats "limited", "ltz" beats "lt"
    for trim in TRIMS:
        if re.search(r"\b" + re.escape(trim) + r"\b", t):
            out["trim"] = trim.title().replace("Ltz", "LTZ").replace("Slt", "SLT") \
                              .replace("Sle", "SLE").replace("Xlt", "XLT") \
                              .replace("Ls", "LS").replace("Lt", "LT").replace("Sr5", "SR5") \
                              .replace("Sxt", "SXT").replace("Sv", "SV").replace("Sl", "SL")
            break
    # title status
    if re.search(r"\brebuilt\b", t): out["title_status"] = "rebuilt"
    elif re.search(r"\bsalvage\b", t): out["title_status"] = "salvage"
    elif re.search(r"\bclean title\b", t): out["title_status"] = "clean"
    if re.search(r"\blien\b", t): out["title_status"] = out.get("title_status", "") + " lien"
    return out

def enrich(listing, description=None):
    """Fill null/invalid listing fields from title + notes + description text."""
    text = " | ".join(filter(None, [listing.get("title"), listing.get("notes"), description]))
    found = extract_from_text(text)
    recovered = list(listing.get("recovered") or [])

    def fill(field, bad_check=None):
        cur = listing.get(field)
        bad = bad_check(cur) if bad_check else False
        if bad:
            listing[field] = None
            cur = None
            if field not in recovered:
                recovered.append(field + ":invalidated")
        if cur in (None, "") and found.get(field) is not None:
            cand = found[field]
            if bad_check and bad_check(cand):
                return  # description value is garbage too
            listing[field] = cand
            if field not in recovered:
                recovered.append(field)

    fill("mileage", invalid_mileage)
    fill("price", invalid_price)
    fill("year")
    fill("make")
    fill("model")
    fill("trim")
    if found.get("title_status") and "title_status" not in (listing.get("notes") or "").lower():
        listing["title_status_desc"] = found["title_status"]
    if recovered:
        listing["recovered"] = recovered
    return listing

# self-test
SAMPLE = ("Chevrolet suburban LT 2017, 167,000 miles. One owner most highway miles "
          "going to Lake of the Ozarks. Leather interior is in very very good condition "
          "custom rubber mats throughout the three rows of seats plus the trunk new tires "
          "August 2025 New battery and new transmission October 2025.")

def selftest():
    ok = True
    l = {"title": None, "make": "Chevrolet", "model": None, "mileage": None,
         "year": None, "trim": None, "price": 14000, "notes": ""}
    enrich(l, SAMPLE)
    exp = {"model": "Suburban", "mileage": 167000, "year": 2017, "trim": "LT"}
    for k, v in exp.items():
        if l.get(k) != v: print(f"FAIL sample: {k}={l.get(k)} want {v}"); ok = False
    l2 = {"title": "2016 Chevy Tahoe", "make": "Chevrolet", "model": "Tahoe",
          "mileage": 1, "price": 200, "year": 2016, "trim": None, "notes": ""}
    enrich(l2, "Runs great, 142,000 miles, asking $13,500 obo, clean title")
    if l2["mileage"] != 142000: print(f"FAIL invalid-mileage: {l2['mileage']}"); ok = False
    if l2["price"] != 13500: print(f"FAIL invalid-price: {l2['price']}"); ok = False
    l3 = {"title": "2018 Ford Expedition", "make": "Ford", "model": "Expedition",
          "mileage": 999999, "price": 15000, "year": 2018, "trim": None, "notes": ""}
    enrich(l3, "Nice truck, must sell")
    if l3["mileage"] is not None: print(f"FAIL 999999: {l3['mileage']}"); ok = False
    l4 = {"title": "2019 GMC Yukon XL Denali", "make": "GMC", "model": "Yukon XL",
          "mileage": 88000, "price": 24000, "year": 2019, "trim": "Denali", "notes": ""}
    enrich(l4, "actually has 150,000 miles")
    if l4["mileage"] != 88000: print("FAIL precedence"); ok = False
    print("SELFTEST", "PASSED" if ok else "FAILED")
    return ok

if __name__ == "__main__":
    if not selftest():
        sys.exit(1)
    if "--apply" in sys.argv:
        path = "data/listings.json"
        ls = json.load(open(path))
        n = 0
        for l in ls:
            before = dict(l)
            enrich(l)
            if l.get("recovered") and l != before:
                n += 1
        json.dump(ls, open(path, "w"), indent=1)
        print(f"enriched {n}/{len(ls)} listings from title/notes text")
