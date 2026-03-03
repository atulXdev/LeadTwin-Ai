"""
Database Layer — Supabase client + CRUD helpers for LeadTwin AI
"""

import os
import logging
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
logger = logging.getLogger(__name__)

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.warning("Supabase credentials not set. Database operations will fail.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None


# ============================
# Project CRUD
# ============================

def create_project(user_id: str, name: str, keyword: str, country: str = "India", company_size: str = None) -> dict:
    """Create a new project in the database."""
    data = {
        "user_id": user_id,
        "name": name,
        "keyword": keyword,
        "country": country,
        "status": "pending",
    }
    if company_size:
        data["company_size"] = company_size

    result = supabase.table("projects").insert(data).execute()
    logger.info(f"Created project: {result.data[0]['id'] if result.data else 'unknown'}")
    return result.data[0] if result.data else {}


def get_project(project_id: str) -> dict:
    """Get a project by ID."""
    result = supabase.table("projects").select("*").eq("id", project_id).single().execute()
    return result.data if result.data else {}


def get_user_projects(user_id: str) -> list[dict]:
    """Get all projects for a user."""
    result = supabase.table("projects").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    return result.data or []


def update_project_status(project_id: str, status: str, total_leads: int = None):
    """Update project status and optionally total lead count."""
    data = {"status": status}
    if total_leads is not None:
        data["total_leads"] = total_leads
    supabase.table("projects").update(data).eq("id", project_id).execute()


# ============================
# Lead CRUD
# ============================

def save_leads(project_id: str, leads: list[dict]) -> list[dict]:
    """Save a batch of leads to the database."""
    rows = []
    for lead in leads:
        row = {
            "project_id": project_id,
            "company_name": lead.get("company_name", ""),
            "website": lead.get("website", ""),
            "email": lead.get("email", "") or (lead.get("emails", [""])[0] if lead.get("emails") else ""),
            "phone": ("; ".join(lead.get("phones", [])) if isinstance(lead.get("phones"), list) else lead.get("phone", "")),
            "linkedin": (lead.get("linkedin", [""])[0] if isinstance(lead.get("linkedin"), list) and lead.get("linkedin") else lead.get("linkedin_url", "")),
            "services": ", ".join(lead.get("services_detected", [])) if isinstance(lead.get("services_detected"), list) else "",
            "has_hiring_page": lead.get("has_hiring_page", False),
            "has_pricing_page": lead.get("has_pricing_page", False),
            "has_blog": lead.get("has_blog", False),
            "blog_updated_recently": lead.get("blog_updated_recently", False),
            "tech_stack": lead.get("tech_stack", []),
            "score": lead.get("score", 0),
            "grade": lead.get("grade", "Cold"),
            "insights": lead.get("insights", ""),
            "raw_data": {
                "search_title": lead.get("title", ""),
                "meta_description": lead.get("meta_description", ""),
            },
        }
        rows.append(row)

    if rows:
        result = supabase.table("leads").insert(rows).execute()
        logger.info(f"Saved {len(result.data)} leads to project {project_id}")
        return result.data or []
    return []


def get_project_leads(project_id: str, grade: str = None, min_score: int = None) -> list[dict]:
    """Get leads for a project, with optional filters."""
    query = supabase.table("leads").select("*").eq("project_id", project_id)
    if grade:
        query = query.eq("grade", grade)
    if min_score is not None:
        query = query.gte("score", min_score)
    result = query.order("score", desc=True).execute()
    return result.data or []


def get_lead(lead_id: str) -> dict:
    """Get a single lead by ID."""
    result = supabase.table("leads").select("*").eq("id", lead_id).single().execute()
    return result.data if result.data else {}


def delete_project_leads(project_id: str):
    """Delete all leads for a project."""
    supabase.table("leads").delete().eq("project_id", project_id).execute()


# ============================
# Stats
# ============================

def get_user_stats(user_id: str) -> dict:
    """Get aggregate stats for a user."""
    projects = get_user_projects(user_id)
    project_ids = [p["id"] for p in projects]

    if not project_ids:
        return {"total_projects": 0, "total_leads": 0, "hot_leads": 0, "warm_leads": 0, "cold_leads": 0, "avg_score": 0}

    all_leads = []
    for pid in project_ids:
        leads = get_project_leads(pid)
        all_leads.extend(leads)

    total = len(all_leads)
    hot = sum(1 for l in all_leads if l.get("grade") == "Hot")
    warm = sum(1 for l in all_leads if l.get("grade") == "Warm")
    cold = sum(1 for l in all_leads if l.get("grade") == "Cold")
    avg_score = sum(l.get("score", 0) for l in all_leads) / total if total > 0 else 0

    return {
        "total_projects": len(projects),
        "total_leads": total,
        "hot_leads": hot,
        "warm_leads": warm,
        "cold_leads": cold,
        "avg_score": round(avg_score, 1),
    }
