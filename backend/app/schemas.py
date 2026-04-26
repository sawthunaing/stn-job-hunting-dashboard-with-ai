"""Pydantic schemas for request/response bodies."""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict


# ============ JOBS ============

class JobBase(BaseModel):
    company: str
    role: str
    location: Optional[str] = None
    work_type: Optional[str] = None
    platform: Optional[str] = None
    source_url: Optional[str] = None
    description: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    currency: Optional[str] = "GBP"
    status: Optional[str] = "New"
    notes: Optional[str] = None
    starred: Optional[bool] = False


class JobCreate(JobBase):
    pass


class JobFromUrl(BaseModel):
    url: str


class JobUpdate(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    location: Optional[str] = None
    work_type: Optional[str] = None
    platform: Optional[str] = None
    source_url: Optional[str] = None
    description: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    currency: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    starred: Optional[bool] = None
    applied_date: Optional[datetime] = None


class JobListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company: str
    role: str
    location: Optional[str]
    platform: Optional[str]
    status: str
    suitability: Optional[int]
    starred: bool
    created_at: datetime


class JobDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company: str
    role: str
    location: Optional[str]
    work_type: Optional[str]
    platform: Optional[str]
    source_url: Optional[str]
    description: Optional[str]
    salary_min: Optional[int]
    salary_max: Optional[int]
    currency: Optional[str]
    status: str
    notes: Optional[str]
    starred: bool
    applied_date: Optional[datetime]

    suitability: Optional[int]
    analysis: Optional[dict[str, Any]]
    interview_prep: Optional[dict[str, Any]]
    company_research: Optional[dict[str, Any]]
    tailored_docs: Optional[dict[str, Any]]

    created_at: datetime
    updated_at: datetime
    analyzed_at: Optional[datetime]


class TailorRequest(BaseModel):
    doc_type: str


# ============ PROFILE ============

class ProfileSchema(BaseModel):
    """The user's profile. All fields optional - whatever they fill in, the AI uses."""
    model_config = ConfigDict(from_attributes=True)

    full_name: Optional[str] = None
    headline: Optional[str] = None
    location: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None

    summary: Optional[str] = None
    experience: Optional[str] = None
    skills: Optional[str] = None
    education: Optional[str] = None
    achievements: Optional[str] = None

    target_roles: Optional[str] = None
    target_salary: Optional[str] = None
    deal_breakers: Optional[str] = None
    private_notes: Optional[str] = None

    updated_at: Optional[datetime] = None
