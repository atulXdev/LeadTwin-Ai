"""
Pydantic Models for LeadTwin AI API
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# --- Request Models ---

class GenerateLeadsRequest(BaseModel):
    keyword: str = Field(..., min_length=2, max_length=200, description="Industry keyword to search for")
    country: str = Field(default="India", max_length=50)
    max_results: int = Field(default=20, ge=1, le=100)
    company_size: Optional[str] = Field(default=None, max_length=50)
    project_name: Optional[str] = Field(default=None, max_length=100)


class CreateProjectRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    keyword: str = Field(..., min_length=2, max_length=200)
    country: str = Field(default="India", max_length=50)
    company_size: Optional[str] = Field(default=None)


class ExportRequest(BaseModel):
    project_id: str
    format: str = Field(default="csv", pattern="^(csv|json)$")


# --- Response Models ---

class LeadResponse(BaseModel):
    id: Optional[str] = None
    company_name: str = ""
    website: str = ""
    email: str = ""
    phone: str = ""
    linkedin: str = ""
    score: int = 0
    grade: str = "Cold"
    insights: str = ""
    has_hiring_page: bool = False
    has_pricing_page: bool = False
    tech_stack: list[str] = []
    services: list[str] = []
    created_at: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    keyword: str
    country: str
    status: str = "pending"
    total_leads: int = 0
    created_at: Optional[str] = None


class PipelineStatusResponse(BaseModel):
    project_id: str
    status: str
    total_found: int = 0
    total_enriched: int = 0
    total_scored: int = 0
    errors: list = []
    leads: list[LeadResponse] = []
    export_path: Optional[str] = None


class StatsResponse(BaseModel):
    total_projects: int = 0
    total_leads: int = 0
    hot_leads: int = 0
    warm_leads: int = 0
    cold_leads: int = 0
    avg_score: float = 0.0
