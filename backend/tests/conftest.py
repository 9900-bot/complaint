import json
import numpy as np
import pytest
from sqlalchemy.orm import sessionmaker
from shapely.geometry import box, mapping
from app.database import Base, make_engine
from app.models import Complaint
from app.geography import Geography
from app.config import Settings


class FakeRuntime:
    version = 'test-model@1'
    cross_version = 'test-cross@1'
    merge_score = .5

    def embed(self, text):
        return np.array([1, 0, 0], dtype=np.float32)

    def score(self, pairs):
        return np.full(len(pairs), self.merge_score)


@pytest.fixture
def config():
    return Settings(worker_enabled=False, membership_threshold=.8, merge_candidate_similarity=.1, rate_limit_per_minute=100)


@pytest.fixture
def sessions(tmp_path):
    engine = make_engine(f'sqlite:///{tmp_path / "test.db"}')
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    yield factory
    engine.dispose()


@pytest.fixture
def geo(tmp_path, sessions):
    features=[]
    # Synthetic rectangles are TEST FIXTURES only. Runtime uses real DataMeet polygons.
    for kind, code, name, parent, rectangle in [
        ('state','s1','Test State',None,box(70,10,80,20)),
        ('state','s2','Other State',None,box(80,10,90,20)),
        ('district','d1','West District','s1',box(70,10,75,20)),
        ('district','d2','East District','s1',box(75,10,80,20)),
        ('constituency','a1','Cross District Assembly','s1',box(73,11,77,19)),
    ]:
        features.append({'id':code,'stable_code':code,'name':name,'region_type':kind,'parent_region_id':parent,
                         'dataset_version':'fixture','geometry':mapping(rectangle),'display_geometry':mapping(rectangle)})
    path=tmp_path/'regions.json'
    path.write_text(json.dumps(features))
    geo=Geography(path)
    geo.import_metadata(sessions)
    return geo


@pytest.fixture
def runtime():
    return FakeRuntime()


def add_complaint(db, text='Streetlights have stopped working on our road.', state='s1', latitude=15.123456, longitude=74.123456, **kwargs):
    c=Complaint(email='private@example.com',original_text=text,latitude=latitude,longitude=longitude,state_id=state,**kwargs)
    db.add(c)
    db.flush()
    return c
