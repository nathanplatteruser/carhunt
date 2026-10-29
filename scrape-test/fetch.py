import asyncio, sys, json, time, datetime
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode

LOG = "scrape_log.md"
def log(msg):
    with open(LOG, "a") as f:
        f.write(f"- {datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')}Z {msg}\n")

async def fetch(urls, delay=2):
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as c:
        out = {}
        for i, (name, url) in enumerate(urls):
            if i: await asyncio.sleep(delay)
            cfg = CrawlerRunConfig(check_robots_txt=True, cache_mode=CacheMode.BYPASS,
                                   wait_until="domcontentloaded", delay_before_return_html=3, page_timeout=45000)
            r = await c.arun(url=url, config=cfg)
            if not r.success:
                log(f"FAIL {name} {url}: status={r.status_code} err={(r.error_message or "").splitlines()[0][:200] if r.error_message else None}")
                print("FAIL", name, url, r.status_code); continue
            md = r.markdown.raw_markdown if hasattr(r.markdown, "raw_markdown") else str(r.markdown)
            open(f"raw/{name}.html", "w").write(r.html or "")
            open(f"raw/{name}.md", "w").write(md)
            log(f"OK {name} {url}: status={r.status_code} final={r.redirected_url} html={len(r.html or '')}B md={len(md)}B")
            print("OK", name, url, r.status_code, len(r.html or ""), len(md))

if __name__ == "__main__":
    pairs = [a.split("=", 1) for a in sys.argv[1:]]
    asyncio.run(fetch(pairs))
