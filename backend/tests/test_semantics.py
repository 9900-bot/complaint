import numpy as np
import pytest
from sqlalchemy import select, func
from app.clustering import ClusterService
from app.ml import SQLiteVectors, normalize, exact_nearest
from app.models import Cluster, ClusterMerge, Complaint
from conftest import add_complaint


def test_vector_format_and_dimension():
    store=SQLiteVectors()
    raw=store.serialize(np.array([3,4,0]))
    assert len(raw)==12
    np.testing.assert_allclose(store.deserialize(raw,3),[.6,.8,0])
    with pytest.raises(ValueError): store.deserialize(raw,4)
    with pytest.raises(ValueError): store.serialize([0,0])
    with pytest.raises(ValueError): store.serialize([np.nan,1])


def test_exact_global_nearest(sessions,geo,runtime,config):
    service=ClusterService(runtime,config)
    with sessions.begin() as db:
        for i in range(30):
            c=add_complaint(db,text=f'Concern number {i} needs attention.')
            # Force separate clusters, then compare globally (last one must win).
            service.config=service.config.model_copy(update={'membership_threshold':1.01})
            service.assign(db,c,[np.cos(i*.04),np.sin(i*.04),0])
        clusters=list(db.scalars(select(Cluster).order_by(Cluster.created_at,Cluster.id)))
        nearest,score=exact_nearest([np.cos(29*.04),np.sin(29*.04),0],clusters,service.vectors)
        assert nearest.id==c.cluster_id
        assert score==pytest.approx(1,abs=1e-6)


def test_threshold_inclusive_new_cluster_and_full_centroid(sessions,geo,runtime,config):
    service=ClusterService(runtime,config.model_copy(update={'membership_threshold':1.0}))
    with sessions.begin() as db:
        a=add_complaint(db)
        first=service.assign(db,a,[1,0,0])
        b=add_complaint(db,state='s2',latitude=15,longitude=84)
        assert service.assign(db,b,[1,0,0]).id==first.id  # Equal threshold, different geography.
        c=add_complaint(db,text='There is no drinking water supply.')
        assert service.assign(db,c,[0,1,0]).id!=first.id
        service.config=service.config.model_copy(update={'membership_threshold':.7})
        d=add_complaint(db)
        assert service.assign(db,d,[.8,.6,0]).id==first.id
        expected=normalize(np.array([2.8,.6,0])/3)
        np.testing.assert_allclose(service.vectors.deserialize(first.centroid_embedding,3),expected,atol=1e-6)
        assert first.complaint_count==3
        assert db.scalar(select(func.count()).select_from(Cluster))==2
        assert service.assign(db,d,[0,0,1]).id==first.id  # Retry does not duplicate membership.
        assert first.complaint_count==3


@pytest.mark.parametrize('score,merged',[(.92,False),(.919,False),(.921,True),(.2,False)])
def test_cross_encoder_merge_threshold(sessions,geo,runtime,config,score,merged):
    service=ClusterService(runtime,config.model_copy(update={'membership_threshold':.99}))
    with sessions.begin() as db:
        a,b=add_complaint(db),add_complaint(db,text='The road lamps are broken at night.')
        first=service.assign(db,a,[1,0,0]); second=service.assign(db,b,[.9,.3,0])
        runtime.merge_score=score
        service.merge_candidates(db)
        assert second.active is not merged
        assert (a.cluster_id==b.cluster_id)==merged
        assert db.scalar(select(func.count()).select_from(ClusterMerge))==int(merged)


def test_merge_canonical_idempotency_and_rollback(sessions,geo,runtime,config):
    service=ClusterService(runtime,config.model_copy(update={'membership_threshold':1.01}))
    with sessions.begin() as db:
        a,b=add_complaint(db),add_complaint(db)
        first=service.assign(db,a,[1,0,0]);second=service.assign(db,b,[.9,.3,0])
        first_id,second_id=first.id,second.id
    with pytest.raises(RuntimeError):
        with sessions.begin() as db:
            service.merge(db,second_id,first_id,.99)
            raise RuntimeError('simulated transaction interruption')
    with sessions.begin() as db:
        assert db.get(Cluster,second_id).active
        assert db.scalar(select(func.count()).select_from(ClusterMerge))==0
        target=service.merge(db,second_id,first_id,.99)
        assert target.id==first_id
        assert target.complaint_count==2
        assert not db.get(Cluster,second_id).active
        assert service.merge(db,first_id,second_id,.99) is None
        assert db.scalar(select(func.count()).select_from(ClusterMerge))==1
        assert len(set(db.scalars(select(Complaint.cluster_id))))==1


def test_model_version_mismatch_fails(sessions,geo,runtime,config):
    service=ClusterService(runtime,config)
    with sessions.begin() as db:
        service.assign(db,add_complaint(db),[1,0,0])
        runtime.version='other-model'
        with pytest.raises(ValueError,match='model changed'):
            service.assign(db,add_complaint(db),[1,0,0])


def test_labels_are_derived_not_fixed():
    from app.labels import LabelService
    label=LabelService().label(['The footbridge planks are broken.', 'Broken footbridge planks need repair.'])
    assert any(word in label.lower() for word in ['footbridge','planks','broken'])
