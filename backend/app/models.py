"""SQLAlchemy ORM models for the Job Hunting Dashboard."""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Text, DateTime, JSON, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Job(Base):
    """A job posting and all derived AI analysis."""
    __tablename__ = "jobs"
    __table_args__ = (Index("ix_jobs_source_external_id", "source", "external_id", unique=True),)

    id: Mapped[int] = mapped_column(primary_key=True)

    # Listing fields
    company: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(300))
    location: Mapped[Optional[str]] = mapped_column(String(200))
    work_type: Mapped[Optional[str]] = mapped_column(String(50))
    platform: Mapped[Optional[str]] = mapped_column(String(100))
    source_url: Mapped[Optional[str]] = mapped_column(String(1000))
    source: Mapped[Optional[str]] = mapped_column(String(50))
    external_id: Mapped[Optional[str]] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)
    salary_min: Mapped[Optional[int]] = mapped_column(Integer)
    salary_max: Mapped[Optional[int]] = mapped_column(Integer)
    currency: Mapped[Optional[str]] = mapped_column(String(3), default="GBP")

    # Tracking
    status: Mapped[str] = mapped_column(String(30), default="New")
    notes: Mapped[Optional[str]] = mapped_column(Text)
    starred: Mapped[bool] = mapped_column(default=False)
    applied_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # AI-derived (JSON blobs - can iterate on shape without migrations)
    suitability: Mapped[Optional[int]] = mapped_column(Integer)
    analysis: Mapped[Optional[dict]] = mapped_column(JSON)
    interview_prep: Mapped[Optional[dict]] = mapped_column(JSON)
    company_research: Mapped[Optional[dict]] = mapped_column(JSON)
    tailored_docs: Mapped[Optional[dict]] = mapped_column(JSON)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    analyzed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


class Profile(Base):
    """The user's profile - one row, used as context for every AI call."""
    __tablename__ = "profile"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)

    # Identity
    full_name: Mapped[Optional[str]] = mapped_column(String(200))
    headline: Mapped[Optional[str]] = mapped_column(String(300))
    location: Mapped[Optional[str]] = mapped_column(String(200))
    email: Mapped[Optional[str]] = mapped_column(String(200))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    website: Mapped[Optional[str]] = mapped_column(String(500))
    linkedin: Mapped[Optional[str]] = mapped_column(String(500))
    github: Mapped[Optional[str]] = mapped_column(String(500))

    # Public sections - markdown
    summary: Mapped[Optional[str]] = mapped_column(Text)
    experience: Mapped[Optional[str]] = mapped_column(Text)
    skills: Mapped[Optional[str]] = mapped_column(Text)
    education: Mapped[Optional[str]] = mapped_column(Text)
    achievements: Mapped[Optional[str]] = mapped_column(Text)

    # Private targeting (AI uses but never includes in tailored docs)
    target_roles: Mapped[Optional[str]] = mapped_column(Text)
    target_salary: Mapped[Optional[str]] = mapped_column(String(200))
    deal_breakers: Mapped[Optional[str]] = mapped_column(Text)
    private_notes: Mapped[Optional[str]] = mapped_column(Text)

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
