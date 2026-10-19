"""Optional fictional reports. Stop the API before running this maintenance command."""
from datetime import timedelta
import argparse
import json
from pathlib import Path
import socket
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from sqlalchemy import select, delete
from app.database import SessionLocal
from app.models import Complaint, Cluster, now
from app.geography import Geography
from app.config import settings
from app.ml import ModelRuntime
from app.clustering import ClusterService

PLACES=[('Bengaluru',12.9716,77.5946),('Mumbai',19.0760,72.8777),('Delhi',28.6139,77.2090),
        ('Chennai',13.0827,80.2707),('Kolkata',22.5726,88.3639),('Jaipur',26.9124,75.7873),
        ('Hyderabad',17.3850,78.4867),('Lucknow',26.8467,80.9462)]
ISSUES=[
    ['The streetlights on our residential road have stopped working. The road is completely dark after sunset.',
     'Several road lamps have been broken for a week, making the street unsafe to walk at night.',
     'The streetlights on our residential road have stopped working. The road is completely dark after sunset.'],
    ['There has been no drinking water supply to our homes for three days. Residents have to purchase water.',
     'Our taps have been dry for days. The neighbourhood urgently needs its drinking water supply restored.',
     'Water supply is interrupted almost every morning and households cannot store enough drinking water.'],
    ['Garbage has not been collected from our lane for a week. Waste is piling up beside the homes.',
     'The waste collection vehicle has missed our street repeatedly and rubbish is attracting insects.',
     'Household garbage is accumulating because the municipal waste pickup has not come for several days.'],
    ['Deep potholes on the main road make daily travel dangerous for cyclists and motorbike riders.',
     'The road surface is broken with large potholes. Vehicles swerve suddenly to avoid the damaged patches.',
     'Rain has made the potholes deeper and the damaged road needs urgent repair.'],
    ['The local bus is repeatedly delayed by more than half an hour, affecting the daily commute.',
     'Public buses do not arrive according to the schedule and passengers wait for a long time.',
     'Bus service on our route is unreliable, with frequent late arrivals during morning rush hour.'],
    ['An open drain is overflowing into the street after rainfall and dirty water is entering nearby homes.',
     'The drainage channel is blocked and sewage overflows onto the road whenever it rains.',
     'Blocked drains are causing stagnant sewage outside homes and need cleaning.'],
    ['The pedestrian footbridge has loose planks and a broken railing, making it unsafe for children.',
     'The neighbourhood footbridge railing is damaged and several boards need repair.',
     'A broken footbridge handrail and loose walking surface create a fall hazard.'],
]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--remove',action='store_true')
    parser.add_argument('--count',type=int,default=56)
    args=parser.parse_args()
    with socket.socket() as s:
        if s.connect_ex(('127.0.0.1',8011))==0:
            raise SystemExit('Stop the backend on port 8011 before maintenance, then run this command again.')
    runtime=ModelRuntime()
    service=ClusterService(runtime)
    if args.remove:
        with SessionLocal.begin() as db:
            db.execute(delete(Complaint).where(Complaint.is_demo))
            db.flush()
            for cluster in db.scalars(select(Cluster).where(Cluster.active)):
                if service.members(db,cluster.id):
                    service.refresh(db,cluster)
                else:
                    cluster.active=False
                    cluster.complaint_count=0
        print('Fictional demo complaints removed. Remaining cluster representations refreshed.')
        return
    with SessionLocal() as db:
        if db.scalar(select(Complaint.id).where(Complaint.is_demo).limit(1)):
            raise SystemExit('Demo data already exists. Remove it first to avoid duplicates.')
    geography=Geography(settings.geography_path)
    if not geography.features:
        raise SystemExit('Run geographic preparation first.')
    runtime.load()
    for index in range(max(1,min(args.count,500))):
        place,lat,lng=PLACES[index%len(PLACES)]
        # Repeated points are intentional approximations for a fictional dataset.
        loc=geography.resolve(lat,lng)
        if not loc['state']:
            print(f'Skipping unsupported source point: {place}')
            continue
        issue=ISSUES[index%len(ISSUES)][(index//len(ISSUES))%3]
        if index%17==0:
            issue+=' A nearby drain also needs attention.'  # Explicitly ambiguous, multi-issue example.
        embedding=runtime.embed(issue)
        with SessionLocal.begin() as db:
            c=Complaint(email='fictional-demo@example.com',original_text=issue,latitude=lat,longitude=lng,
                        state_id=loc['state']['id'],district_id=loc['district']['id'] if loc['district'] else None,
                        constituency_id=loc['constituency']['id'] if loc['constituency'] else None,
                        geographic_ambiguity=json.dumps(loc['ambiguities']) or None,
                        is_demo=True,created_at=now()-timedelta(days=(index*7)%30,hours=index%20))
            db.add(c);db.flush()
            service.process(db,c,embedding)
        print(f'{index+1}/{args.count}: fictional complaint in {place}',flush=True)
    with SessionLocal() as db:
        clusters=list(db.scalars(select(Cluster).where(Cluster.active)))
        print('Actual-pipeline categories:',[(c.label,c.complaint_count) for c in clusters])


if __name__=='__main__':main()
