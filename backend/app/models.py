"""SQLAlchemy ORM models for the Job Hunt dashboard."""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Text, DateTime, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Job(Base):
    """A job posting and all derived AI analysis."""
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Listing fields
    company: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(300))
    location: Mapped[Optional[str]] = mapped_column(String(200))
    work_type: Mapped[Optional[str]] = mapped_column(String(50))
    platform: Mapped[Optional[str]] = mapped_column(String(100))
    source_url: Mapped[Optional[str]] = mapped_column(String(1000))
    description: Mapped[Optional[str]] = mapped_column(Text)
    salary_min: Mapped[Optional[int]] = mapped_column(Integer)
    salary_max: Mapped[Optional[int]] = mapped_column(Integer)
    currency: Mapped[Optional[str]] = mapped_column(String(3), default="GBP")

    # Tracking
    status: Mapped[str] = mapped_column(String(30), default="New")
    notes: Mapped[Optional[str]] = mapped_column(Text)
    starred: Mapped[bool] = mapped_column(default=False)
    applied_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # AI-derived (JSON blobs)
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
    """The user's profile - one row, used as context for every AI call.

    Singleton table: we only ever store one row (id=1).
    """
    __tablename__ = "profile"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)

    # Identity
    full_name: Mapped[Optional[str]] = mapped_column(String(200))
    headline: Mapped[Optional[str]] = mapped_column(String(300))  # e.g. "Senior Backend Engineer"
    location: Mapped[Optional[str]] = mapped_column(String(200))
    email: Mapped[Optional[str]] = mapped_column(String(200))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    website: Mapped[Optional[str]] = mapped_column(String(500))
    linkedin: Mapped[Optional[str]] = mapped_column(String(500))
    github: Mapped[Optional[str]] = mapped_column(String(500))

    # The big content blocks - markdown
    summary: Mapped[Optional[str]] = mapped_column(Text)         # 2-3 paragraph elevator pitch
    experience: Mapped[Optional[str]] = mapped_column(Text)      # full work history in markdown
    skills: Mapped[Optional[str]] = mapped_column(Text)          # languages, frameworks, infra
    education: Mapped[Optional[str]] = mapped_column(Text)
    achievements: Mapped[Optional[str]] = mapped_column(Text)    # awards, talks, OSS

    # Targeting preferences (the AI uses these but recruiters don't see them)
    target_roles: Mapped[Optional[str]] = mapped_column(Text)
    target_salary: Mapped[Optional[str]] = mapped_column(String(200))
    deal_breakers: Mapped[Optional[str]] = mapped_column(Text)
    private_notes: Mapped[Optional[str]] = mapped_column(Text)

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
