"""Verify a live local submission, worker result, public privacy and synchronized APIs."""
import argparse
import json
import sys
import time
from pathlib import Path
import httpx
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.database import SessionLocal
from app.models import Complaint

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--reference',required=True)
args=parser.parse_args()
reference=args.reference
deadline=time.monotonic()+55
while time.monotonic()<deadline:
    with SessionLocal() as db:
        complaint=db.get(Complaint,reference)
        assert complaint is not None,'Reference missing from SQLite'
        if complaint.internal_processing_state=='completed':break
        if complaint.internal_processing_state=='failed':raise AssertionError('Semantic processing failed')
    time.sleep(1)
else:raise AssertionError('Semantic worker did not finish within 55 seconds')
with SessionLocal.begin() as db:
    c=db.get(Complaint,reference)
    assert c.embedding_dimension==384 and c.cluster_id
    assert c.embedding_model_version.startswith('sentence-transformers/all-MiniLM-L6-v2@')
    assert c.constituency_id,'Browser sample did not resolve an Assembly constituency'
    filters={'state_id':c.state_id,'district_id':c.district_id,'constituency_id':c.constituency_id,'cluster_id':c.cluster_id}
    # This exact synthetic browser fixture is removable alongside the other demo data.
    if c.email=='browser-verification@example.com' and c.original_text.startswith('Fictional browser verification:'):
        c.is_demo=True

results={}
private={'email','latitude','longitude','embedding','internal_processing_state','attempts','geographic_ambiguity'}
def check_fields(value):
    if isinstance(value,dict):
        assert not private.intersection(value),'Private response key exposed'
        for child in value.values():check_fields(child)
    elif isinstance(value,list):
        for child in value:check_fields(child)

with httpx.Client(base_url='http://127.0.0.1:8011/api/',timeout=30) as client:
    for endpoint in ['complaints','clusters','map/complaints','map/heatmap','map/regions',
                     'analytics/overview','analytics/categories','analytics/geography','analytics/timeline','analytics/trends']:
        response=client.get(endpoint,params=filters)
        response.raise_for_status()
        body=response.json()
        check_fields(body)
        assert 'browser-verification@example.com' not in response.text
        results[endpoint]=response.status_code
    overview=client.get('analytics/overview',params=filters).json()
    records=client.get('complaints',params=filters).json()
    assert overview['total']==records['total']
    assert any(c['id']==reference for c in records['items'])
    points=client.get('map/complaints',params=filters).json()['features']
    point=next(p for p in points if p['properties']['id']==reference)
    assert point['geometry']['coordinates']!=[77.5946,12.9716]
report={'reference':reference,'worker_completed':True,'embedding_dimension':384,'constituency_resolved':True,
        'combined_filters_consistent':True,'public_privacy_passed':True,'endpoints':results}
(ROOT/'outputs').mkdir(exist_ok=True)
(ROOT/'outputs/smoke-test.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
