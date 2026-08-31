#!/usr/bin/env python3
"""Sold-status audit for existing CarHunt board rows.

WHY THIS EXISTS: sold status on Facebook Marketplace is 100% JS-rendered -
the raw HTML <title> and embedded JSON carry no sold marker (verified), so a
cheap fetch probe CANNOT detect it. Detecting "Sold" requires a full rendered
page load per listing. Existing board rows therefore go stale: a listing
scraped three weeks ago that sold yesterday still looks alive.

FLOW (run alongside the weekly scrape):
  1. python3 sold_audit.py queue [board.json] -> prints ids to audit, priority
     order: great deals first, then good, then by last_seen age (staleness).
  2. Visit each id with the in-page snippet from sweep_extract.js (the
     hardened sold check: H1 "Sold" prefix / separator variants / tab title).
     Batch 6 per browser_batch round; bank {"id":..,"sold":true|false} lines
     to a jsonl file.
  3. python3 sold_audit.py apply results.jsonl [board.json] -> sets sold=true
     on matches (rows are KEPT and tagged red on the dashboard, excluded from
     deal counts), refreshes last_seen, and reports how many flipped.

Dead listings (redirect to unavailable_product) should be recorded as
{"id":..,"dead":true} and are removed entirely - a deleted listing has no
transparency value.
"""
import json, sys, datetime

def load(path):
    return json.load(open(path))

def cmd_queue(board="/root/carhunt/data/listings.json", limit=60):
    limit = int(limit)
    ls = load(board)
    def key(l):
        mv, p = l.get("market_value"), l.get("price")
        deal = (mv - p) / mv * 100 if mv and p else -99
        return (-(deal >= 15), -(deal >= 5), l.get("first_seen") or "9999")
    ids = [l["id"] for l in sorted([l for l in ls if not l.get("sold")], key=key)][:limit]
    print(json.dumps(ids))

def cmd_apply(results, board="/root/carhunt/data/listings.json"):
    ls = load(board)
    res = {}
    for line in open(results):
        if line.strip():
            r = json.loads(line); res[r["id"]] = r
    today = datetime.date.today().isoformat()
    sold = dead = live = 0
    out = []
    for l in ls:
        r = res.get(l["id"])
        if r:
            if r.get("dead"): dead += 1; continue
            if r.get("sold"): l["sold"] = True; sold += 1
            else: live += 1
            l["last_seen"] = today
        out.append(l)
    json.dump(out, open(board, "w"), indent=1)
    print(f"audited {len(res)}: {sold} newly SOLD, {dead} dead (removed), {live} confirmed live | board {len(ls)} -> {len(out)}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "queue":
        cmd_queue(*sys.argv[2:])
    elif len(sys.argv) > 1 and sys.argv[1] == "apply":
        cmd_apply(*sys.argv[2:])
    else:
        print(__doc__)
