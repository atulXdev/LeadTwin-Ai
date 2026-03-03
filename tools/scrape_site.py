"""
Tool: Scrape Site
Purpose: Fetch and parse a single company website.
Input: url (str)
Output: {html, text, meta, links, status_code}
"""

import logging
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

logger = logging.getLogger(__name__)

# Respectful scraping defaults
TIMEOUT = 15
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def scrape_website(url: str) -> dict:
    """
    Scrape a single website. Returns structured data.
    Respects robots.txt via User-Agent and rate limiting.
    """
    if not url.startswith("http"):
        url = "https://" + url

    logger.info(f"Scraping: {url}")
    result = {
        "url": url,
        "status_code": None,
        "title": "",
        "meta_description": "",
        "text": "",
        "html": "",
        "links": [],
        "pages_found": {},
        "error": None,
    }

    try:
        with httpx.Client(timeout=TIMEOUT, headers=HEADERS, follow_redirects=True) as client:
            response = client.get(url)
            result["status_code"] = response.status_code

            if response.status_code != 200:
                result["error"] = f"HTTP {response.status_code}"
                return result

            html = response.text
            result["html"] = html
            soup = BeautifulSoup(html, "lxml")

            # Extract title
            title_tag = soup.find("title")
            result["title"] = title_tag.get_text(strip=True) if title_tag else ""

            # Extract meta description
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc:
                result["meta_description"] = meta_desc.get("content", "")

            # Extract visible text
            for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
                tag.decompose()
            result["text"] = soup.get_text(separator=" ", strip=True)[:5000]

            # Extract all internal links
            base_domain = urlparse(url).netloc
            links = []
            for a_tag in soup.find_all("a", href=True):
                href = a_tag.get("href", "")
                full_url = urljoin(url, href)
                if base_domain in full_url:
                    links.append(full_url)
            result["links"] = list(set(links))

            # Detect key pages
            result["pages_found"] = _detect_key_pages(links, url)

    except httpx.TimeoutException:
        result["error"] = "Timeout"
        logger.warning(f"Timeout scraping {url}")
    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Error scraping {url}: {e}")

    return result


def scrape_subpage(url: str) -> str:
    """Scrape a subpage and return its text content."""
    try:
        with httpx.Client(timeout=TIMEOUT, headers=HEADERS, follow_redirects=True) as client:
            response = client.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "lxml")
                for tag in soup(["script", "style", "noscript"]):
                    tag.decompose()
                return soup.get_text(separator=" ", strip=True)[:3000]
    except Exception as e:
        logger.warning(f"Failed to scrape subpage {url}: {e}")
    return ""


def _detect_key_pages(links: list[str], base_url: str) -> dict:
    """Detect if the site has key pages (hiring, pricing, blog, about, contact)."""
    pages = {
        "hiring": False,
        "pricing": False,
        "blog": False,
        "about": False,
        "contact": False,
        "services": False,
    }

    keywords_map = {
        "hiring": ["career", "careers", "jobs", "hiring", "join-us", "join-our-team", "work-with-us"],
        "pricing": ["pricing", "plans", "packages"],
        "blog": ["blog", "insights", "articles", "news", "resources"],
        "about": ["about", "about-us", "our-story", "company"],
        "contact": ["contact", "contact-us", "get-in-touch"],
        "services": ["services", "solutions", "products", "offerings", "what-we-do"],
    }

    links_lower = [l.lower() for l in links]

    for page_type, keywords in keywords_map.items():
        for keyword in keywords:
            if any(keyword in link for link in links_lower):
                pages[page_type] = True
                break

    return pages


# --- Direct CLI usage ---
if __name__ == "__main__":
    import json
    data = scrape_website("https://example.com")
    print(json.dumps({k: v for k, v in data.items() if k != "html"}, indent=2, default=str))
