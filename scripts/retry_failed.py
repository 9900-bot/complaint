"""Explicit local maintenance: requeue jobs after fixing a model/setup failure."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from sqlalchemy import update
from app.database import SessionLocal
from app.models import Complaint
with SessionLocal.begin() as db:
    result=db.execute(update(Complaint).where(Complaint.internal_processing_state=='failed').values(
        internal_processing_state='pending',attempts=0,next_attempt_at=None))
    print(f'Requeued {result.rowcount} failed local jobs.')
