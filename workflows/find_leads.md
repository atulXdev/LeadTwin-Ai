# Workflow: Find Leads

## Objective
Discover company websites matching a target industry/keyword in a specific country.

## Required Inputs
- `keyword` (str): Industry or niche keyword (e.g., "SaaS companies", "IT services")
- `country` (str): Target country (e.g., "India", "US")
- `max_results` (int): Maximum number of leads to find (default: 20)
- `company_size` (str, optional): Filter like "startup", "enterprise"

## Tool to Execute
`tools/search_scraper.py` → `search_companies(keyword, country, max_results, company_size)`

## Process
1. Build a search query from keyword + filters
2. Call SerpAPI Google Search
3. Paginate through results (max 5 pages)
4. Deduplicate by domain
5. Return list of `{url, domain, title, snippet}`

## Expected Output
```json
[
  {"url": "https://acme.com", "domain": "acme.com", "title": "AcmeTech", "snippet": "..."},
  ...
]
```

## Edge Cases
- **SerpAPI rate limit**: Wait 2 seconds between pages. Max 5 pages per search.
- **No results**: Return empty list, log warning. Check keyword validity.
- **Duplicate domains**: Deduplicated by top-level domain automatically.

## Error Handling
- Retry up to 3 times on SerpAPI timeout
- If API key is invalid, raise clear error — do not retry

## Lessons Learned
(Agent updates this section as issues are discovered)
