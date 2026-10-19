from datetime import datetime
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.main import create_app
from app.models import Complaint
from app.clustering import ClusterService
from conftest import add_complaint


@pytest.fixture
def client(sessions,geo,runtime,config):
    with TestClient(create_app(sessions,geo,runtime,config)) as client:
        yield client


def submission():
    return {'email':'private@example.com','text':'Street lighting has not worked for several days.','latitude':15.123456,'longitude':74.123456}


def test_submission_persistence_and_private_fields(client,sessions):
    response=client.post('/api/complaints',json=submission())
    assert response.status_code==201
    reference=response.json()['reference_id']
    with sessions() as db:
        row=db.get(Complaint,reference)
        assert row.email=='private@example.com'
        assert row.latitude==15.123456
        assert row.internal_processing_state=='pending'
        assert row.constituency_id=='a1'
    result=client.get('/api/complaints').json()
    assert result['total']==1
    assert result['items'][0]['category'] is None
    for path in ['complaints','map/complaints','map/heatmap','analytics/overview','analytics/categories','analytics/geography','analytics/timeline','analytics/trends','map/regions']:
        response=client.get('/api/'+path)
        assert response.status_code==200
        raw=response.text
        assert 'private@example.com' not in raw
        assert '15.123456' not in raw and '74.123456' not in raw
        assert 'latitude' not in raw and 'longitude' not in raw
        assert 'internal_processing_state' not in raw


@pytest.mark.parametrize('changes',[{'email':'bad'},{'latitude':91},{'longitude':181},{'text':'short'},{'text':' '*12},{'latitude':0,'longitude':0},{'text':'x'*3001},{'cluster_id':'injected'}])
def test_validation(client,changes):
    response=client.post('/api/complaints',json=submission()|changes)
    assert response.status_code==422
    assert 'private@example.com' not in response.text


def test_missing_constituency_allowed(client):
    response=client.post('/api/complaints',json=submission()|{'longitude':71.123456})
    assert response.status_code==201
    assert client.get('/api/complaints').json()['items'][0]['constituency'] is None


def test_geographic_independence_and_overlap(geo):
    west=geo.resolve(15,74)
    east=geo.resolve(15,76)
    assert west['constituency']['id']==east['constituency']['id']=='a1'
    assert west['district']['id']!=east['district']['id']
    assert geo.resolve(0,0)['state'] is None
    overlap=geo.resolve(15,80)
    assert len(overlap['ambiguities']['state'])==2
    assert geo.resolve(15,80)==overlap  # Deterministic shared-boundary rule.


def test_filters_pagination_and_analytics(client,sessions,geo,runtime,config):
    service=ClusterService(runtime,config)
    with sessions.begin() as db:
        a=add_complaint(db,created_at=datetime(2026,10,1),district_id='d1',constituency_id='a1')
        service.process(db,a,[1,0,0]); cluster_id=a.cluster_id
        b=add_complaint(db,created_at=datetime(2026,10,2),state='s2',longitude=84)
        service.process(db,b,[1,0,0])
        add_complaint(db,text='Drinking water has stopped coming to our homes.',created_at=datetime(2026,10,3),district_id='d2')
    params={'state_id':'s1','district_id':'d1','constituency_id':'a1','cluster_id':cluster_id,'date_from':'2026-10-01','date_to':'2026-10-01'}
    assert client.get('/api/complaints',params=params).json()['total']==1
    overview=client.get('/api/analytics/overview').json()
    assert overview['total']==3 and overview['active_clusters']==1 and overview['states']==2
    assert sum(c['count'] for c in client.get('/api/analytics/categories').json())==3
    assert sum(c['count'] for c in client.get('/api/analytics/timeline').json())==3
    assert sum(c['count'] for c in client.get('/api/analytics/timeline?interval=week').json())==3
    assert client.get('/api/complaints?page=2&page_size=1').json()['items'][0]['created_at'].startswith('2026-10-02')
    assert len(client.get('/api/clusters').json())==1
    assert client.get(f'/api/clusters/{cluster_id}/complaints').json()['total']==2
    assert client.get(f'/api/clusters/{cluster_id}').json()['count']==2
    assert client.get('/api/complaints?date_from=2026-10-04&date_to=2026-10-01').status_code==422
    assert client.get('/api/complaints?bbox=bad').status_code==422
    assert client.get('/api/complaints?page_size=10001').status_code==422


def test_grid_privacy_bbox_and_empty_states(client):
    assert client.get('/api/analytics/overview').json()['total']==0
    assert client.get('/api/map/complaints').json()['features']==[]
    client.post('/api/complaints',json=submission())
    point=client.get('/api/map/complaints').json()['features'][0]['geometry']['coordinates']
    assert point==[74.125,15.125]
    assert client.get('/api/map/complaints').json()['features'][0]['geometry']['coordinates']==point
    # A bounding box enclosing the precise GPS but excluding its public center must return no hit.
    assert client.get('/api/map/complaints?bbox=74.123,15.123,74.124,15.124').json()['features']==[]
    assert client.get('/api/map/heatmap').json()['features'][0]['properties']['count']==1


def test_rate_limit(sessions,geo,runtime,config):
    with TestClient(create_app(sessions,geo,runtime,config.model_copy(update={'rate_limit_per_minute':1}))) as client:
        assert client.post('/api/complaints',json=submission()).status_code==201
        assert client.post('/api/complaints',json=submission()).status_code==429
