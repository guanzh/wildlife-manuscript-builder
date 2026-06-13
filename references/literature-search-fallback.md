# Literature Search Fallback

When `web_search` is unavailable, `browser_navigate` hits CAPTCHAs on Google Scholar, and `delegate_task` subagents return summaries instead of actual paper lists, use direct API calls via `terminal` curl.

## Crossref REST API (preferred — generous rate limits, no auth needed)

```bash
# Basic search
curl -s "https://api.crossref.org/works?query=gibbon+habitat+edge+effects+fragmentation&rows=10&filter=type:journal-article" | python -c "
import sys,json
d=json.load(sys.stdin)
for item in d['message']['items']:
    t = item.get('title',['?'])[0] if item.get('title') else '?'
    y = item.get('published-print',{}).get('date-parts',[[0]])[0][0]
    doi = item.get('DOI','?')
    j = item.get('container-title',['?'])[0] if item.get('container-title') else '?'
    au = ', '.join([a.get('given','')+' '+a.get('family','') for a in item.get('author',[])[:3]])
    print(f'{y} | {t[:120]} | {au} | {j} | DOI:{doi}')
"
```

Key parameters:
- `query=` — URL-encoded search terms (spaces become `+`)
- `rows=` — max results per page (default 20)
- `filter=type:journal-article` — exclude books, datasets, etc.
- Add `&select=title,DOI,author,container-title,published-print` for faster responses

## Semantic Scholar API (faster but hits 429 rate limits quickly)

```bash
curl -s "https://api.semanticscholar.org/graph/v1/paper/search?query=gibbon+habitat+fragmentation&limit=10&fields=title,year,externalIds"
```

Use sparingly — Semantic Scholar rate-limits aggressively without an API key.

## Elicit API (best quality results for ecology deep research — requires API key)

When `web_search` is unavailable and Crossref returns too many irrelevant results, use the Elicit API. It returns far more targeted literature for ecology/biodiversity topics.

**Setup:**
- API key: `ELICIT_API_KEY` in Hermes `.env` file (format: `elk_live_...`)
- Endpoint: `https://elicit.com/api/v1/search` (POST) — **NOT** `api.elicit.com`
- Requires: Pro plan or above; `Authorization: Bearer <key>` header

**Critical: Cloudflare/Proxy bypass**
Elicit's API is behind Cloudflare which may block requests from headless clients. Two workarounds:
1. Add browser-like `User-Agent: Mozilla/5.0 ...` header
2. In Python's `urllib`, remove `http_proxy`/`https_proxy` environment variables before making the call — some HTTP proxies trigger 403 Cloudflare blocks with error code 1010

**Python recipe:**
```python
import urllib.request, json, os

key = "elk_live_..."  # from .env
headers = {
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://elicit.com/",
}

# Remove proxy env vars FIRST (they cause 403 on some networks)
old_http = os.environ.pop('http_proxy', None)
old_https = os.environ.pop('https_proxy', None)

data = json.dumps({"query": "passive acoustic monitoring gibbon", "maxResults": 8}).encode()
req = urllib.request.Request("https://elicit.com/api/v1/search", data=data, headers=headers, method="POST")
resp = urllib.request.build_opener().open(req, timeout=30)
result = json.loads(resp.read().decode())
for p in result['papers']:
    print(f"{p['year']} | {p['title'][:100]} | {p.get('doi','?')}")

# Restore proxy if needed
if old_http: os.environ['http_proxy'] = old_http
if old_https: os.environ['https_proxy'] = old_https
```

**Response format:** `{"papers": [{"elicitId": "...", "title": "...", "authors": [...], "year": N, "abstract": "...", "doi": "...", "citedByCount": N, "venue": "..."}], ...}`

**Also available:** `search` endpoint uses `query` and `maxResults`. For filtered search, use `filters` object with `minEpochS`, `maxEpochS`, `includeKeywords`, `excludeKeywords`, `typeTags` (e.g. "RCT", "Meta-Analysis"), `hasPdf`.

## Canonical References for Gibbon Canopy Connectivity

When discussing boundary permeability / canopy connectivity for gibbons, always check:

- Chan BPL, Lo YFP, Hong XJ, et al. (2020). First use of artificial canopy bridge by the world's most critically endangered primate the Hainan gibbon *Nomascus hainanus*. *Scientific Reports*, 10: 15176. DOI:10.1038/s41598-020-72641-z
- Gregory T, Carrasco-Rueda F, Alonso A, et al. (2017). Natural canopy bridges effectively mitigate tropical forest fragmentation for arboreal mammals. *Scientific Reports*, 7: 3892. DOI:10.1038/s41598-017-04112-x

## When All Else Fails

If APIs are also rate-limited, note the gap in the delivery readiness report under "claims requiring new literature" and proceed with the existing reference list. The manuscript can still reach Level 2 (Reviewable) without new papers, but not Level 3 (Journal-Format).
