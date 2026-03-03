"""
Tool: Enrichment Engine
Purpose: Enrich company data with hiring detection, tech stack, blog freshness, etc.
Input: scraped site data dict
Output: enriched company profile dict
"""

import re
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Tech stack detection keywords
TECH_KEYWORDS = {
    "react": "React", "angular": "Angular", "vue": "Vue.js",
    "next.js": "Next.js", "nextjs": "Next.js", "nuxt": "Nuxt.js",
    "node.js": "Node.js", "nodejs": "Node.js", "django": "Django",
    "flask": "Flask", "fastapi": "FastAPI", "laravel": "Laravel",
    "ruby on rails": "Ruby on Rails", "rails": "Ruby on Rails",
    "aws": "AWS", "azure": "Azure", "gcp": "Google Cloud",
    "google cloud": "Google Cloud", "docker": "Docker",
    "kubernetes": "Kubernetes", "k8s": "Kubernetes",
    "terraform": "Terraform", "python": "Python",
    "typescript": "TypeScript", "golang": "Go",
    "postgresql": "PostgreSQL", "mongodb": "MongoDB",
    "redis": "Redis", "graphql": "GraphQL",
    "tailwind": "Tailwind CSS", "shopify": "Shopify",
    "wordpress": "WordPress", "hubspot": "HubSpot",
    "salesforce": "Salesforce", "stripe": "Stripe",
}

# SaaS-related keywords
SAAS_KEYWORDS = [
    "saas", "software as a service", "cloud platform", "subscription",
    "api", "platform", "dashboard", "analytics", "automation",
    "crm", "erp", "b2b", "enterprise", "startup", "scale",
    "monthly plan", "annual plan", "free trial", "demo",
]


def enrich_company(scraped_data: dict) -> dict:
    """
    Enrich a company profile from scraped website data.
    Analyzes text content for signals used in lead scoring.
    """
    text = scraped_data.get("text", "").lower()
    html = scraped_data.get("html", "").lower()
    pages_found = scraped_data.get("pages_found", {})
    links = scraped_data.get("links", [])

    company_name = _extract_company_name(scraped_data)

    profile = {
        "company_name": company_name,
        "website": scraped_data.get("url", ""),
        "title": scraped_data.get("title", ""),
        "meta_description": scraped_data.get("meta_description", ""),

        # Key page detection
        "has_hiring_page": pages_found.get("hiring", False),
        "has_pricing_page": pages_found.get("pricing", False),
        "has_blog": pages_found.get("blog", False),
        "has_about_page": pages_found.get("about", False),
        "has_contact_page": pages_found.get("contact", False),
        "has_services_page": pages_found.get("services", False),

        # Content signals
        "has_saas_keywords": _detect_saas_keywords(text),
        "blog_updated_recently": False,  # Requires subpage scrape
        "uses_modern_stack": False,
        "tech_stack": [],
        "services_detected": [],

        # Raw link count as a proxy for site maturity
        "total_internal_links": len(links),
    }

    # Detect tech stack
    detected_tech = _detect_tech_stack(text + " " + html)
    profile["tech_stack"] = detected_tech
    profile["uses_modern_stack"] = len(detected_tech) >= 2

    # Detect services
    profile["services_detected"] = _detect_services(text)

    logger.info(f"Enriched: {company_name} — tech={detected_tech}, saas={profile['has_saas_keywords']}")

    return profile


def _extract_company_name(scraped_data: dict) -> str:
    """Extract company name from site title."""
    title = scraped_data.get("title", "")
    if not title:
        return scraped_data.get("url", "Unknown")

    # Common patterns: "Company Name | Tagline" or "Company Name - Tagline"
    for sep in [" | ", " - ", " – ", " — ", " : "]:
        if sep in title:
            return title.split(sep)[0].strip()

    return title.strip()


def _detect_saas_keywords(text: str) -> bool:
    """Check if the site contains SaaS-related keywords."""
    count = sum(1 for kw in SAAS_KEYWORDS if kw in text)
    return count >= 3  # At least 3 SaaS keywords


def _detect_tech_stack(content: str) -> list[str]:
    """Detect technologies mentioned on the site."""
    detected = set()
    for keyword, tech_name in TECH_KEYWORDS.items():
        if keyword in content:
            detected.add(tech_name)
    return sorted(list(detected))


def _detect_services(text: str) -> list[str]:
    """Extract service-related phrases from text."""
    service_patterns = [
        "web development", "mobile development", "app development",
        "cloud consulting", "digital marketing", "seo services",
        "data analytics", "machine learning", "artificial intelligence",
        "devops", "ui/ux design", "product design", "consulting",
        "managed services", "staff augmentation", "qa testing",
        "cybersecurity", "blockchain", "iot", "e-commerce",
    ]
    found = [s for s in service_patterns if s in text]
    return found


def check_blog_freshness(blog_text: str) -> bool:
    """
    Check if a blog page has recent content (within 30 days).
    Called separately after scraping the blog subpage.
    """
    # Look for date patterns
    date_patterns = [
        r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{4}\b',
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4}\b',
        r'\b\d{4}-\d{2}-\d{2}\b',
    ]

    thirty_days_ago = datetime.now() - timedelta(days=30)

    for pattern in date_patterns:
        matches = re.findall(pattern, blog_text, re.IGNORECASE)
        for match in matches:
            try:
                for fmt in ["%d %B %Y", "%B %d, %Y", "%B %d %Y", "%Y-%m-%d"]:
                    try:
                        date = datetime.strptime(match.replace(",", ""), fmt)
                        if date >= thirty_days_ago:
                            return True
                    except ValueError:
                        continue
            except Exception:
                continue

    return False


# --- Direct CLI usage ---
if __name__ == "__main__":
    import json
    mock_data = {
        "url": "https://example-saas.com",
        "title": "AcmeTech | Cloud Platform for Teams",
        "meta_description": "Enterprise SaaS platform",
        "text": "We build saas cloud platform with react and node.js. Free trial available. Dashboard analytics.",
        "html": "<html>react nextjs aws docker</html>",
        "links": ["/careers", "/pricing", "/blog", "/about"],
        "pages_found": {"hiring": True, "pricing": True, "blog": True, "about": True, "contact": False, "services": False},
    }
    result = enrich_company(mock_data)
    print(json.dumps(result, indent=2))
