from sqlalchemy import select
from app.worker import LocalWorker
from app.clustering import ClusterService
from app.models import Complaint, Cluster
from conftest import add_complaint


def test_restart_recovery_and_committed_results(sessions,geo,runtime,config):
    with sessions.begin() as db:
        row=add_complaint(db,internal_processing_state='processing',attempts=1)
        reference=row.id
    worker=LocalWorker(sessions,ClusterService(runtime,config),config)
    worker.recover()
    assert worker.once()
    with sessions() as db:
        c=db.get(Complaint,reference)
        assert c.internal_processing_state=='completed'
        assert db.get(Cluster,c.cluster_id).complaint_count==1
    assert worker.once() is False


def test_failed_work_retries_bounded(sessions,geo,runtime,config):
    def fail(text): raise RuntimeError('model unavailable')
    runtime.embed=fail
    with sessions.begin() as db:
        reference=add_complaint(db).id
    worker=LocalWorker(sessions,ClusterService(runtime,config),config)
    for attempt in range(3):
        assert worker.once()
        with sessions.begin() as db:
            c=db.get(Complaint,reference)
            assert c.attempts==attempt+1
            c.next_attempt_at=None
    with sessions() as db:
        assert db.get(Complaint,reference).internal_processing_state=='failed'
        assert not list(db.scalars(select(Cluster)))
    assert worker.once() is False
