from __future__ import annotations
import json
from datetime import datetime
from typing import List, Optional

from sqlalchemy import JSON, Boolean, Column, DateTime, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    path = Column(String, nullable=False)
    case_id = Column(String, nullable=True, index=True)

    status = Column(String, default="queued", index=True)
    error_messages = Column(JSON, default=list)

    classification = Column(JSON, nullable=True)
    extracted_dates = Column(JSON, default=list)
    obligations = Column(JSON, default=list)
    human_review_required = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(String, primary_key=True)
    case_id = Column(String, index=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    start = Column(DateTime, nullable=False)
    end = Column(DateTime, nullable=False)
    all_day = Column(Boolean, default=False)
    source_document = Column(String, nullable=True)


# Tables are created during FastAPI startup event to avoid race with DB readiness
