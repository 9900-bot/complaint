import os
import numpy as np
import pytest
from app.ml import ModelRuntime


@pytest.fixture(scope='module')
def actual_runtime():
    if os.environ.get('RUN_MODEL_TESTS')!='1':
        pytest.skip('Opt in with RUN_MODEL_TESTS=1; downloads actual model weights')
    runtime=ModelRuntime()
    runtime.load(download=True)
    return runtime


@pytest.mark.integration
def test_actual_model_dimensions_and_similarity(actual_runtime):
    runtime=actual_runtime
    first=runtime.embed('The streetlights on our road have stopped working.')
    similar=runtime.embed('The road lamps are broken and the street is dark at night.')
    unrelated=runtime.embed('The local bus service is frequently late.')
    assert first.shape==(384,)
    assert np.linalg.norm(first)==pytest.approx(1,abs=1e-5)
    assert first@similar > first@unrelated
    scores=runtime.score([('The streetlights are broken.','The streetlights are broken.'),('The streetlights are broken.','The water supply is contaminated.')])
    assert scores[0]>scores[1]
    assert all(0<=s<=1 for s in scores)


@pytest.mark.integration
def test_actual_pipeline_cross_encoder_merge(actual_runtime,sessions,geo,config):
    from app.clustering import ClusterService
    from conftest import add_complaint
    from app.models import ClusterMerge
    from sqlalchemy import select
    # Force a fragmented pair to test real cross-encoder merging independently of assignment.
    service=ClusterService(actual_runtime,config.model_copy(update={'membership_threshold':1.01}))
    text='The street lights are broken.'
    embedding=actual_runtime.embed(text)
    with sessions.begin() as db:
        a=add_complaint(db,text=text);b=add_complaint(db,text=text,state='s2',longitude=84)
        canonical=service.assign(db,a,embedding)
        other=service.assign(db,b,embedding)
        assert canonical.id!=other.id
        service.merge_candidates(db)
        assert a.cluster_id==b.cluster_id==canonical.id
        assert canonical.complaint_count==2
        history=db.scalar(select(ClusterMerge))
        assert history.merge_score>.92
