"""
Tool: Search Scraper
Purpose: Find company domains for a given industry keyword using SerpAPI Google Search.
Input: keyword (str), country (str), max_results (int)
Output: List of {url, title, snippet} dicts
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv
from serpapi import GoogleSearch

load_dotenv()
logger = logging.getLogger(__name__)

# Country code mapping for Google Search
COUNTRY_CODES = {
    "india": "in", "us": "us", "usa": "us", "uk": "uk",
    "united kingdom": "uk", "canada": "ca", "australia": "au",
    "germany": "de", "france": "fr", "singapore": "sg",
    "united states": "us", "uae": "ae", "dubai": "ae",
}


def search_companies(
    keyword: str,
    country: str = "India",
    max_results: int = 20,
    company_size: Optional[str] = None,
) -> list[dict]:
    """
    Search for companies matching the keyword in the specified country.
    Returns deduplicated list of company URLs with metadata.
    """
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        raise ValueError("SERPAPI_KEY not found in environment variables")

    # Build search query
    query_parts = [keyword, "companies"]
    if company_size:
        query_parts.append(company_size)
    query = " ".join(query_parts)

    gl_code = COUNTRY_CODES.get(country.lower(), "us")

    logger.info(f"Searching: '{query}' in country={country} (gl={gl_code}), max={max_results}")

    all_results = []
    seen_domains = set()
    page = 0
    per_page = min(max_results, 10)

    while len(all_results) < max_results:
        params = {
            "engine": "google",
            "q": query,
            "google_domain": "google.com",
            "gl": gl_code,
            "hl": "en",
            "num": per_page,
            "start": page * per_page,
            "api_key": api_key,
        }

        try:
            search = GoogleSearch(params)
            data = search.get_dict()
        except Exception as e:
            logger.error(f"SerpAPI error on page {page}: {e}")
            break

        organic = data.get("organic_results", [])
        if not organic:
            logger.info("No more results from SerpAPI")
            break

        for result in organic:
            url = result.get("link", "")
            domain = _extract_domain(url)

            # Deduplicate by domain
            if domain and domain not in seen_domains:
                seen_domains.add(domain)
                all_results.append({
                    "url": url,
                    "domain": domain,
                    "title": result.get("title", ""),
                    "snippet": result.get("snippet", ""),
                })

            if len(all_results) >= max_results:
                break

        page += 1

        # Safety: max 5 pages to avoid burning API credits
        if page >= 5:
            break

    logger.info(f"Found {len(all_results)} unique company domains")
    return all_results


def _extract_domain(url: str) -> str:
    """Extract clean domain from URL."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Remove www prefix
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return ""


# --- Direct CLI usage ---
if __name__ == "__main__":
    import json
    results = search_companies("SaaS companies", "India", max_results=5)
    print(json.dumps(results, indent=2))
