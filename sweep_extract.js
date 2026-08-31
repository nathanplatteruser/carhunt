// CarHunt detail-page extractor — canonical snippet run in-page during sweeps.
// Three plans, strict order (mileage field is ALWAYS Plan A):
//   A (field):   "Driven 158,868 miles" — FB's structured mileage field
//   B (labeled): "Mileage - 141,512", "odometer: 158600", "has 90,000 miles"
//   C (scan):    exhaustive candidate scan of ALL text — catches emoji-bulleted
//                bare statements like "✅ 158,600 miles" and "158.6k mi", while
//                excluding years, intervals ("every 5,000 miles"), warranties
//                ("up to 100,000 miles"), and "N miles ago" phrases; picks the
//                largest surviving candidate (intervals skew small).
// ALSO captures: title status, seller join year, VIN, and the seller's
// description (first 900 chars) so the ETL can be re-run later on stored data
// without re-opening a single listing. Read-only; never messages anyone.
//
// SOLD DETECTION: if "Sold" appears in the listing title (FB prefixes sold
// listings like "Sold · 2019 Ford Expedition Max"), the record is flagged
// sold:true. Sold listings are KEPT on the board for raw-data transparency
// but rendered with a bright red SOLD tag and excluded from deal ratings —
// a "Hide sold" toggle lets deal-hunters filter them out.
//
// Usage: substitute LISTING_ID; run after navigation + a See-more click.

const s = ms => new Promise(r => setTimeout(r, ms));
[...document.querySelectorAll('span')].find(e => /^See more$/.test(e.innerText))?.click();
await s(720);
const t = document.body.innerText;

// SOLD check first. Sold status is 100% JS-rendered (verified: the raw HTML
// title tag and embedded JSON carry NO sold marker), so this must run on the
// rendered page. FB puts the red "Sold" at the start of the listing H1
// ("Sold · 2015 Dodge durango...") but the separator varies (· • - or a line
// break), so check the H1 prefix first and fall back to separator patterns.
const h1 = [...document.querySelectorAll('h1')].map(e => e.innerText).join(' ');
const sold = /^\s*Sold\b/i.test(h1)
          || /(^|\n)\s*Sold\s*[·•∙⋅\-–—]/m.test(t.slice(0, 600))
          || /(^|\s)Sold\s*[·•\-]/.test(document.title);
if (sold) JSON.stringify({ id: 'LISTING_ID', sold: true });
const g = re => { const m = t.match(re); return m ? m[1].replace(/,/g, '') : null; };

// Plans A + B
let mi = g(/Driven\s+([\d,]+)\s*miles/i)
      || g(/Mileage\s*[-–·:]*\s*([\d,]{4,7})/i)
      || g(/odometer\s*(?:reads|reading|shows|at|is)?\s*[-–·:]*\s*([\d,]{4,7})/i)
      || g(/(?:has|with|only|@|at)\s+([\d,]{4,7})\s+(?:miles|mi\b)/i);
let plan = mi ? 'AB' : null;

// Plan C
if (!mi) {
  const cs = [];
  const re2 = /([\d]{1,3}(?:,\d{3})+|\d{4,6})\s*(?:miles|mi\b)|(\d{2,3}(?:\.\d)?)\s*k\s*(?:miles|mi\b)/gi;
  let m2;
  while (m2 = re2.exec(t)) {
    let v = m2[1] ? parseInt(m2[1].replace(/,/g, '')) : Math.round(parseFloat(m2[2]) * 1000);
    if (v < 1000 || v > 400000) continue;
    if (v >= 1990 && v <= 2026 && !(m2[1] || '').includes(',')) continue; // bare year
    const b = t.slice(Math.max(0, m2.index - 28), m2.index);
    if (/(?:every|per|each|up\s*to|warranty|next|within|last|added|towing|tow|range)\s*[\d,\.]*\s*$/i.test(b)) continue;
    if (/^\s*(?:miles?|mi)\s*ago/i.test(t.slice(m2.index + m2[0].length - 6, m2.index + m2[0].length + 8))) continue;
    cs.push(v);
  }
  if (cs.length) { mi = String(Math.max(...cs)); plan = 'C'; }
}

// description capture — persisted to listing_cache.json so future parser
// upgrades replay over stored data instead of re-opening listings
const dm = t.match(/Seller's description\n([\s\S]{0,900}?)(?:\n(?:See less|Seller information|Location|Message)|$)/);
const desc = dm ? dm[1].trim().slice(0, 900) : null;

JSON.stringify({
  id: 'LISTING_ID',
  mi, plan,
  tt: (t.match(/clean title|rebuilt|salvage[d]?|branded/i) || [null])[0],
  jn: (t.match(/Joined Facebook in (\d{4})/) || [null])[1],
  vin: (t.match(/VIN[:\s#]*([A-HJ-NPR-Z0-9]{17})/i) || [null])[1],
  desc
});
