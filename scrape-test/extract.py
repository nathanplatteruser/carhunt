import re, json, sys
from bs4 import BeautifulSoup

DEPT = [("Management", r"owner|president|general manager|manager|director|executive"),
        ("F&I", r"finance|f&i"),
        ("Sales", r"sales|consultant|internet|lease|leasing"),
        ("Service", r"service|technician|quick ?lane|advisor"),
        ("Parts", r"parts"),
        ("Office/Admin", r"office|reception|human resources|accounting|bookkeep|marketing")]

def infer_dept(title):
    t = title.lower()
    # specific first: F&I, Parts, Service before generic manager
    for name in ("F&I", "Parts", "Service", "Sales", "Office/Admin", "Management"):
        pat = dict(DEPT)[name]
        if re.search(pat, t): return name
    return None

def extract_vcards(html, url):
    s = BeautifulSoup(html, "lxml")
    out = []
    for c in s.select("[data-testid=vCard]"):
        name = c.find(["h3", "h2", "h4"])
        name = name.get_text(" ", strip=True) if name else None
        ps = [p.get_text(" ", strip=True) for p in c.find_all("p")]
        phone = next((p for p in ps if re.search(r"\d{3}\D{0,3}\d{3,4}|snuggles", p, re.I)), None)
        title = next((p for p in ps if p != phone), None)
        mail = next((a["href"][7:] for a in c.select('a[href^="mailto:"]')), None)
        bio = " ".join(p for p in ps if p not in (title, phone)) or None
        out.append({"name": name, "title": title, "department": infer_dept(title or ""),
                    "department_source": "inferred from title" if title else None,
                    "email": mail, "phone": phone, "bio": bio, "source_url": url})
    return out

if __name__ == "__main__":
    html, url, stem = sys.argv[1:4]
    rows = extract_vcards(open(html).read(), url)
    json.dump(rows, open(f"{stem}.json", "w"), indent=2)
    with open(f"{stem}.md", "w") as f:
        f.write(f"# Staff extracted from {url}\n\n{len(rows)} records\n\n| # | Name | Title | Dept (inferred) | Email | Phone | Bio |\n|---|---|---|---|---|---|---|\n")
        for i, r in enumerate(rows, 1):
            f.write(f"| {i} | {r['name']} | {r['title'] or ''} | {r['department'] or ''} | {r['email'] or ''} | {r['phone'] or ''} | {r['bio'] or ''} |\n")
    print(len(rows))
