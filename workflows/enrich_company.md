# Workflow: Enrich Company

## Objective
For each company URL found by Find Leads, scrape the website and extract detailed company + contact information.

## Required Inputs
- `company_url` (str): The company website URL to enrich
- `domain` (str): The company domain

## Tools to Execute (in sequence)
1. `tools/scrape_site.py` → `scrape_website(url)` — Fetch HTML and detect key pages
2. `tools/contact_extractor.py` → `extract_contacts(html, text)` — Extract emails, phones, LinkedIn
3. `tools/enrichment_engine.py` → `enrich_company(scraped_data)` — Detect tech stack, SaaS signals, services
4. (Optional) `tools/scrape_site.py` → `scrape_subpage(blog_url)` — Check blog freshness if blog page detected

## Process
1. Scrape the main website page
2. Extract contacts from the page content
3. Analyze the site for tech stack, hiring signals, SaaS keywords
4. If a blog page is detected, scrape it to check freshness
5. Merge all data into a single enriched profile

## Expected Output
```json
{
  "company_name": "AcmeTech",
  "website": "https://acme.com",
  "emails": ["info@acme.com"],
  "phones": ["+91-98765-43210"],
  "linkedin": ["https://linkedin.com/company/acme"],
  "has_hiring_page": true,
  "has_pricing_page": true,
  "tech_stack": ["React", "Node.js", "AWS"],
  "services_detected": ["web development"]
}
```

## Edge Cases
- **Site blocks scraping**: Log warning, return partial data (title + URL only)
- **Timeout**: Retry once after 5 seconds. If still failing, skip this lead.
- **No contacts found**: Still enrich other signals — score will be lower naturally
- **JavaScript-heavy sites**: Our basic scraper won't get dynamic content. Accept partial data for MVP.

## Error Handling
- Catch HTTPX timeouts — retry once
- Catch parsing errors from BeautifulSoup — return empty fields
- Never let one company failure block the entire pipeline

## Lessons Learned
(Agent updates this section as issues are discovered)
