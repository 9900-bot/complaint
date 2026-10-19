from datetime import timedelta
import logging
from threading import Thread, Event
from sqlalchemy import select, update, or_
from app.models import Complaint, now
from app.config import settings

log = logging.getLogger(__name__)


class LocalWorker:
    def __init__(self, sessions, clustering, config=settings):
        self.sessions, self.clustering, self.config = sessions, clustering, config
        self.stop_event = Event()
        self.thread = None

    def recover(self):
        with self.sessions.begin() as db:
            db.execute(update(Complaint).where(Complaint.internal_processing_state == 'processing').values(
                internal_processing_state='pending', attempts=Complaint.attempts-1, next_attempt_at=None))

    def once(self):
        with self.sessions.begin() as db:
            complaint = db.scalar(select(Complaint).where(
                Complaint.internal_processing_state == 'pending',
                or_(Complaint.next_attempt_at.is_(None), Complaint.next_attempt_at <= now()),
                Complaint.attempts < self.config.worker_max_attempts,
            ).order_by(Complaint.created_at, Complaint.id).limit(1))
            if not complaint:
                return False
            complaint.internal_processing_state = 'processing'
            complaint.attempts += 1
            complaint_id, text = complaint.id, complaint.original_text
        try:
            embedding = self.clustering.runtime.embed(text)  # No write lock during model loading/inference.
            with self.sessions.begin() as db:
                complaint = db.get(Complaint, complaint_id)
                self.clustering.process(db, complaint, embedding)
        except Exception as error:
            # IDs and exception type only; no emails, coordinates or complaint text in logs.
            log.error('Semantic processing failed for reference %s (%s)', complaint_id, type(error).__name__)
            with self.sessions.begin() as db:
                complaint = db.get(Complaint, complaint_id)
                complaint.internal_processing_state = 'failed' if complaint.attempts >= self.config.worker_max_attempts else 'pending'
                complaint.next_attempt_at = now() + timedelta(seconds=10 * complaint.attempts)
        return True

    def run(self):
        while not self.stop_event.is_set():
            try:
                worked = self.once()
            except Exception as error:
                log.error('Worker poll failed (%s)', type(error).__name__)
                worked = False
            if not worked:
                self.stop_event.wait(self.config.worker_poll_seconds)

    def start(self):
        self.recover()
        self.thread = Thread(target=self.run, name='atlas-semantics', daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5)
