"""
Agent: Orchestrator
Purpose: The brain of the WAT framework. Reads workflows, calls tools in sequence,
handles errors with retries, and produces final scored leads.
"""

import time
import logging
import asyncio
from typing import Optional
from datetime import datetime

from tools.search_scraper import search_companies
from tools.scrape_site import scrape_website, scrape_subpage
from tools.contact_extractor import extract_contacts
from tools.enrichment_engine import enrich_company, check_blog_freshness
from tools.scoring_engine import score_lead
from tools.ai_insights import generate_insights
from tools.sheets_export import export_to_csv, format_leads_for_export
from agent.workflow_parser import load_workflow, update_workflow_lessons

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("orchestrator")

# Constants
MAX_RETRIES = 3
SCRAPE_DELAY = 1.5  # seconds between scrapes (be respectful)


class LeadGenerationPipeline:
    """
    Main orchestration pipeline that runs the full lead generation workflow:
    1. Find Leads (search)
    2. Enrich Company (scrape + extract + enrich)
    3. Score Leads (score + insights)
    4. Export Data (CSV)
    """

    def __init__(self):
        self.stats = {
            "started_at": None,
            "completed_at": None,
            "total_found": 0,
            "total_enriched": 0,
            "total_scored": 0,
            "total_exported": 0,
            "errors": [],
        }

    def run(
        self,
        keyword: str,
        country: str = "India",
        max_results: int = 20,
        company_size: Optional[str] = None,
        project_name: str = "leads",
    ) -> dict:
        """
        Execute the full lead generation pipeline.
        Returns dict with leads, stats, and export filepath.
        """
        self.stats["started_at"] = datetime.now().isoformat()
        logger.info(f"🚀 Starting pipeline: keyword='{keyword}', country='{country}', max={max_results}")

        # ============================================
        # STEP 1: Find Leads
        # ============================================
        logger.info("=" * 60)
        logger.info("STEP 1: FIND LEADS")
        logger.info("=" * 60)

        try:
            workflow = load_workflow("find_leads")
            logger.info(f"Loaded workflow: {workflow['name']}")
        except Exception as e:
            logger.warning(f"Could not load workflow file (continuing anyway): {e}")

        search_results = self._retry(
            search_companies,
            keyword=keyword,
            country=country,
            max_results=max_results,
            company_size=company_size,
        )

        if not search_results:
            logger.error("No companies found. Pipeline aborted.")
            return {"leads": [], "stats": self.stats, "export_path": None}

        self.stats["total_found"] = len(search_results)
        logger.info(f"✅ Found {len(search_results)} companies")

        # ============================================
        # STEP 2: Enrich Companies
        # ============================================
        logger.info("=" * 60)
        logger.info("STEP 2: ENRICH COMPANIES")
        logger.info("=" * 60)

        try:
            workflow = load_workflow("enrich_company")
            logger.info(f"Loaded workflow: {workflow['name']}")
        except Exception:
            pass

        enriched_profiles = []
        contacts_list = []

        for i, company in enumerate(search_results):
            url = company.get("url", "")
            logger.info(f"[{i+1}/{len(search_results)}] Enriching: {url}")

            try:
                # Scrape
                scraped = self._retry(scrape_website, url=url)
                if not scraped or scraped.get("error"):
                    logger.warning(f"  ⚠️ Scrape failed for {url}: {scraped.get('error', 'unknown')}")
                    enriched_profiles.append({"company_name": company.get("title", url), "website": url})
                    contacts_list.append({"emails": [], "phones": [], "linkedin": []})
                    continue

                # Extract contacts
                contacts = extract_contacts(
                    html=scraped.get("html", ""),
                    text=scraped.get("text", ""),
                )

                # Enrich
                enriched = enrich_company(scraped)

                # Check blog freshness if blog detected
                if enriched.get("has_blog"):
                    pages = scraped.get("pages_found", {})
                    blog_links = [l for l in scraped.get("links", []) if "blog" in l.lower()]
                    if blog_links:
                        blog_text = scrape_subpage(blog_links[0])
                        if blog_text:
                            enriched["blog_updated_recently"] = check_blog_freshness(blog_text)

                enriched_profiles.append(enriched)
                contacts_list.append(contacts)
                self.stats["total_enriched"] += 1

                logger.info(f"  ✅ {enriched.get('company_name', 'Unknown')} — "
                          f"emails={len(contacts.get('emails', []))}, "
                          f"tech={len(enriched.get('tech_stack', []))}")

            except Exception as e:
                logger.error(f"  ❌ Error enriching {url}: {e}")
                self.stats["errors"].append({"step": "enrich", "url": url, "error": str(e)})
                enriched_profiles.append({"company_name": company.get("title", url), "website": url})
                contacts_list.append({"emails": [], "phones": [], "linkedin": []})

            # Rate limiting — be respectful
            time.sleep(SCRAPE_DELAY)

        # ============================================
        # STEP 3: Score Leads
        # ============================================
        logger.info("=" * 60)
        logger.info("STEP 3: SCORE LEADS")
        logger.info("=" * 60)

        try:
            workflow = load_workflow("score_leads")
            logger.info(f"Loaded workflow: {workflow['name']}")
        except Exception:
            pass

        scores = []
        insights_list = []

        for i, (profile, contacts) in enumerate(zip(enriched_profiles, contacts_list)):
            company_name = profile.get("company_name", "Unknown")
            logger.info(f"[{i+1}/{len(enriched_profiles)}] Scoring: {company_name}")

            try:
                # Score
                score_data = score_lead(profile, contacts)
                scores.append(score_data)

                # Generate AI insights
                insight = generate_insights(profile, score_data, contacts)
                insights_list.append(insight)

                self.stats["total_scored"] += 1
                logger.info(f"  ✅ {company_name}: {score_data['score']}/100 ({score_data['grade']})")

            except Exception as e:
                logger.error(f"  ❌ Error scoring {company_name}: {e}")
                self.stats["errors"].append({"step": "score", "company": company_name, "error": str(e)})
                scores.append({"score": 0, "grade": "Cold", "breakdown": {}})
                insights_list.append("Scoring failed for this lead.")

        # ============================================
        # STEP 4: Export
        # ============================================
        logger.info("=" * 60)
        logger.info("STEP 4: EXPORT DATA")
        logger.info("=" * 60)

        merged_leads = format_leads_for_export(enriched_profiles, contacts_list, scores, insights_list)

        export_path = None
        try:
            export_path = export_to_csv(merged_leads, project_name)
            self.stats["total_exported"] = len(merged_leads)
            logger.info(f"✅ Exported {len(merged_leads)} leads to {export_path}")
        except Exception as e:
            logger.error(f"❌ Export failed: {e}")
            self.stats["errors"].append({"step": "export", "error": str(e)})

        # ============================================
        # DONE
        # ============================================
        self.stats["completed_at"] = datetime.now().isoformat()

        # Sort leads by score descending
        merged_leads.sort(key=lambda x: x.get("score", 0), reverse=True)

        logger.info("=" * 60)
        logger.info("🏁 PIPELINE COMPLETE")
        logger.info(f"  Found: {self.stats['total_found']}")
        logger.info(f"  Enriched: {self.stats['total_enriched']}")
        logger.info(f"  Scored: {self.stats['total_scored']}")
        logger.info(f"  Errors: {len(self.stats['errors'])}")
        logger.info("=" * 60)

        return {
            "leads": merged_leads,
            "stats": self.stats,
            "export_path": export_path,
        }

    def _retry(self, func, max_retries: int = MAX_RETRIES, **kwargs):
        """Execute a function with retries."""
        for attempt in range(max_retries):
            try:
                return func(**kwargs)
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"All {max_retries} retries exhausted for {func.__name__}")
                    raise


# Convenience function for direct usage
def run_pipeline(
    keyword: str,
    country: str = "India",
    max_results: int = 20,
    company_size: Optional[str] = None,
    project_name: str = "leads",
) -> dict:
    """Run the full lead generation pipeline."""
    pipeline = LeadGenerationPipeline()
    return pipeline.run(keyword, country, max_results, company_size, project_name)


# --- Direct CLI usage ---
if __name__ == "__main__":
    import json
    result = run_pipeline(
        keyword="SaaS companies",
        country="India",
        max_results=5,
        project_name="test_run",
    )
    print(f"\n📊 Results: {len(result['leads'])} leads")
    for lead in result["leads"]:
        print(f"  {lead.get('grade', '?')} ({lead.get('score', 0)}) — {lead.get('company_name', '?')}")
