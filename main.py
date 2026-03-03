"""
LeadTwin AI — FastAPI Backend
Main application entry point with API routes.
"""

import os
import logging
import asyncio
from typing import Optional
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv

from models import (
    GenerateLeadsRequest,
    CreateProjectRequest,
    ExportRequest,
    LeadResponse,
    ProjectResponse,
    PipelineStatusResponse,
    StatsResponse,
)
from database import (
    create_project,
    get_project,
    get_user_projects,
    update_project_status,
    save_leads,
    get_project_leads,
    get_lead,
    get_user_stats,
)
from agent.orchestrator import LeadGenerationPipeline
from tools.sheets_export import export_to_csv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("api")

# Thread pool for running pipeline in background
executor = ThreadPoolExecutor(max_workers=3)

# In-memory pipeline status tracking
pipeline_status: dict[str, dict] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("🚀 LeadTwin AI API starting up")
    os.makedirs(".tmp", exist_ok=True)
    yield
    logger.info("👋 LeadTwin AI API shutting down")
    executor.shutdown(wait=False)


# Initialize FastAPI
app = FastAPI(
    title="LeadTwin AI",
    description="AI-powered B2B Lead Intelligence API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://leadtwin-ai.vercel.app",
        "https://leadtwin-ai.onrender.com",
        "*" # Allow all for MVP testing if needed
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================
# Health Check
# ============================

@app.get("/")
def root():
    return {"name": "LeadTwin AI", "status": "running", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}


# ============================
# Project Endpoints
# ============================

# Using a demo user ID for MVP (no auth required for testing)
DEMO_USER_ID = "00000000-0000-0000-0000-000000000000"


@app.post("/api/projects", response_model=ProjectResponse)
def api_create_project(req: CreateProjectRequest):
    """Create a new lead generation project."""
    try:
        project = create_project(
            user_id=DEMO_USER_ID,
            name=req.name,
            keyword=req.keyword,
            country=req.country,
            company_size=req.company_size,
        )
        return ProjectResponse(
            id=project["id"],
            name=project["name"],
            keyword=project["keyword"],
            country=project["country"],
            status=project["status"],
            total_leads=project.get("total_leads", 0),
            created_at=project.get("created_at"),
        )
    except Exception as e:
        logger.error(f"Failed to create project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects")
def api_list_projects():
    """List all projects."""
    try:
        projects = get_user_projects(DEMO_USER_ID)
        return {"projects": projects}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_id}")
def api_get_project(project_id: str):
    """Get a project by ID."""
    try:
        project = get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================
# Lead Generation
# ============================

def _run_pipeline_background(project_id: str, keyword: str, country: str, max_results: int, company_size: str = None):
    """Run the pipeline in a background thread and save results to DB."""
    global pipeline_status
    pipeline_status[project_id] = {"status": "processing", "progress": "Starting..."}

    try:
        update_project_status(project_id, "processing")
        pipeline_status[project_id]["progress"] = "Searching for companies..."

        pipeline = LeadGenerationPipeline()
        result = pipeline.run(
            keyword=keyword,
            country=country,
            max_results=max_results,
            company_size=company_size,
            project_name=keyword.replace(" ", "_"),
        )

        leads = result.get("leads", [])
        stats = result.get("stats", {})

        pipeline_status[project_id]["progress"] = "Saving leads to database..."

        # Save leads to Supabase
        if leads:
            save_leads(project_id, leads)

        update_project_status(project_id, "completed", total_leads=len(leads))

        pipeline_status[project_id] = {
            "status": "completed",
            "progress": "Done!",
            "total_found": stats.get("total_found", 0),
            "total_enriched": stats.get("total_enriched", 0),
            "total_scored": stats.get("total_scored", 0),
            "errors": stats.get("errors", []),
            "export_path": result.get("export_path"),
        }

        logger.info(f"✅ Pipeline completed for project {project_id}: {len(leads)} leads")

    except Exception as e:
        logger.error(f"❌ Pipeline failed for project {project_id}: {e}")
        update_project_status(project_id, "failed")
        pipeline_status[project_id] = {
            "status": "failed",
            "progress": f"Error: {str(e)}",
            "error": str(e),
        }


@app.post("/api/generate")
def api_generate_leads(req: GenerateLeadsRequest, background_tasks: BackgroundTasks):
    """
    Start lead generation pipeline.
    Creates a project and runs the pipeline in background.
    Returns the project ID for status polling.
    """
    try:
        # Create project
        project_name = req.project_name or f"{req.keyword} - {req.country}"
        project = create_project(
            user_id=DEMO_USER_ID,
            name=project_name,
            keyword=req.keyword,
            country=req.country,
            company_size=req.company_size,
        )
        project_id = project["id"]

        # Run pipeline in background
        background_tasks.add_task(
            _run_pipeline_background,
            project_id=project_id,
            keyword=req.keyword,
            country=req.country,
            max_results=req.max_results,
            company_size=req.company_size,
        )

        return {
            "project_id": project_id,
            "status": "processing",
            "message": f"Lead generation started for '{req.keyword}' in {req.country}. Poll /api/generate/{project_id}/status for updates.",
        }

    except Exception as e:
        logger.error(f"Failed to start generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/generate/{project_id}/status")
def api_generation_status(project_id: str):
    """Check the status of a lead generation pipeline."""
    status = pipeline_status.get(project_id)
    if not status:
        # Check database
        project = get_project(project_id)
        if project:
            return {"project_id": project_id, "status": project.get("status", "unknown")}
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return {"project_id": project_id, **status}


# ============================
# Lead Endpoints
# ============================

@app.get("/api/projects/{project_id}/leads")
def api_get_leads(
    project_id: str,
    grade: Optional[str] = Query(None, pattern="^(Hot|Warm|Cold)$"),
    min_score: Optional[int] = Query(None, ge=0, le=100),
):
    """Get leads for a project with optional filters."""
    try:
        leads = get_project_leads(project_id, grade=grade, min_score=min_score)
        return {"leads": leads, "total": len(leads)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/leads/{lead_id}")
def api_get_lead(lead_id: str):
    """Get a single lead by ID."""
    try:
        lead = get_lead(lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        return lead
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================
# Export Endpoints
# ============================

@app.post("/api/export")
def api_export_leads(req: ExportRequest):
    """Export leads for a project as CSV."""
    try:
        leads = get_project_leads(req.project_id)
        if not leads:
            raise HTTPException(status_code=404, detail="No leads found for this project")

        project = get_project(req.project_id)
        project_name = project.get("name", "leads").replace(" ", "_") if project else "leads"

        filepath = export_to_csv(leads, project_name)
        return FileResponse(
            filepath,
            media_type="text/csv",
            filename=os.path.basename(filepath),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================
# Stats Endpoint
# ============================

@app.get("/api/stats", response_model=StatsResponse)
def api_get_stats():
    """Get aggregate stats for the current user."""
    try:
        stats = get_user_stats(DEMO_USER_ID)
        return StatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================
# Quick Test (no DB required)
# ============================

@app.post("/api/test-pipeline")
def api_test_pipeline(req: GenerateLeadsRequest):
    """
    Run the pipeline synchronously and return results directly.
    For testing only — does not save to database.
    """
    try:
        pipeline = LeadGenerationPipeline()
        result = pipeline.run(
            keyword=req.keyword,
            country=req.country,
            max_results=req.max_results,
            company_size=req.company_size,
            project_name=req.keyword.replace(" ", "_"),
        )
        return {
            "leads": result["leads"],
            "stats": result["stats"],
            "export_path": result.get("export_path"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
