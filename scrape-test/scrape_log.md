# Scrape log (UTC)

Settings: Crawl4AI, check_robots_txt=True, 2s delay between requests, public pages only.

- 2026-10-29T13:35:57+00:00Z OK zoellner_staff https://www.zoellnerfordofbeatrice.com/dealership/staff.htm: status=200 final=https://www.zoellnerfordofbeatrice.com/dealership/staff.htm html=479838B md=441B
- 2026-10-29T13:36:03+00:00Z BLOCKED site_siddillon https://www.siddillon.com/: status=307 final=https://www.siddillon.com/ html=240828B md=1445B -- Cloudflare managed challenge ('Just a moment...'); not bypassed per rules
- 2026-10-29T13:36:10+00:00Z BLOCKED site_lutherauto https://www.lutherauto.com/: status=307 final=https://www.lutherauto.com/ html=240810B md=1450B -- Cloudflare managed challenge ('Just a moment...'); not bypassed per rules
- 2026-10-29T13:36:16+00:00Z BLOCKED site_verneide https://www.verneide.com/: status=307 final=https://www.verneide.com/ html=240802B md=1440B -- Cloudflare managed challenge ('Just a moment...'); not bypassed per rules

## Notes
- robots.txt (fetched via curl): all 4 hosts allow generic crawling of the staff/home paths. siddillon/lutherauto/verneide: Crawl-delay 1 (we used 2s). Zoellner: `User-agent: *` disallows only /api/, /mycars/, etc.
- Zoellner: Crawl4AI fetch OK (200) but its Markdown converter failed ('Invalid tag name', 441B output). Rendered HTML was complete; staff extracted from HTML with BeautifulSoup.
- First attempt used wait_until=networkidle and timed out/errored on the 3 other sites (trackers never idle); switched to domcontentloaded + 3s delay.
- Playwright in .venv wanted chromium build 1248; used preinstalled 1243 via symlinks in ./pw (PLAYWRIGHT_BROWSERS_PATH).
- Anderson Auto (Sioux Falls / Des Moines) and Morrie's: no verified URL, not attempted.
