from contextlib import asynccontextmanager
from collections import defaultdict, deque
import json
import time
from typing import Annotated, Literal
from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import select
from app.config import settings
from app.database import SessionLocal
from app.models import Complaint, Cluster
from app.geography import Geography
from app.ml import ModelRuntime
from app.clustering import ClusterService
from app.worker import LocalWorker
from app.queries import PublicQueries
from app.schemas import (Submission, SubmissionResult, Filters, ComplaintPage, Category, Overview,
                         GeographicCount, TimelinePoint, Trends, RegionPublic, Resolution, GeoJSON, PublicConfig)


def create_app(sessions=SessionLocal, geography=None, runtime=None, config=settings):
    geo = geography or Geography(config.geography_path)
    worker = LocalWorker(sessions, ClusterService(runtime or ModelRuntime(config), config), config)

    @asynccontextmanager
    async def lifespan(app):
        if config.worker_enabled:
            worker.start()
        yield
        worker.stop()

    app = FastAPI(title='Civic Atlas', version='0.1.0', lifespan=lifespan)
    app.state.worker = worker
    app.state.geography = geo
    requests = defaultdict(deque)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, error):
        # Do not echo private request input back through validation errors.
        return JSONResponse(status_code=422, content={'detail': [
            {'loc': list(e['loc']), 'msg': e['msg'], 'type': e['type']} for e in error.errors()]})

    def filters(state_id: str | None = None, district_id: str | None = None, constituency_id: str | None = None,
                cluster_id: str | None = None, date_from: str | None = None, date_to: str | None = None, bbox: str | None = None):
        try:
            result = Filters(state_id=state_id, district_id=district_id, constituency_id=constituency_id,
                             cluster_id=cluster_id, date_from=date_from, date_to=date_to, bbox=bbox)
            if result.date_from and result.date_to and (result.date_to-result.date_from).days > 3660:
                raise ValueError('Choose a date range of ten years or less.')
            return result
        except ValueError:
            raise HTTPException(422, 'Invalid filters. Check dates and map bounds.')

    F = Annotated[Filters, Depends(filters)]

    def queries():
        with sessions() as db:
            yield PublicQueries(db)

    Q = Annotated[PublicQueries, Depends(queries)]

    @app.get('/api/health')
    def health():
        return {'ok': True, 'geography_available': bool(geo.features)}

    @app.get('/api/config', response_model=PublicConfig)
    def public_config():
        return {'complaint_max_length': config.complaint_max_length, 'geography_available': bool(geo.features),
                'boundary_vintage': 'Historical DataMeet boundaries · Census 2011 districts', 'public_grid_degrees': .05}

    @app.post('/api/complaints', response_model=SubmissionResult, status_code=201)
    def submit(body: Submission, request: Request):
        key = request.client.host if request.client else 'local'
        events = requests[key]
        current = time.monotonic()
        while events and events[0] < current-60:
            events.popleft()
        if len(events) >= config.rate_limit_per_minute:
            raise HTTPException(429, 'Please wait one minute before submitting another complaint.', headers={'Retry-After': '60'})
        if not geo.features:
            raise HTTPException(503, 'Geographic data is not installed. Run the local setup script.')
        location = geo.resolve(body.latitude, body.longitude)
        if not location['state']:
            raise HTTPException(422, 'This location is outside the supported Indian boundary coverage. Adjust the pin and try again.')
        with sessions.begin() as db:
            complaint = Complaint(email=str(body.email), original_text=body.text, latitude=body.latitude, longitude=body.longitude,
                                  state_id=location['state']['id'], district_id=location['district']['id'] if location['district'] else None,
                                  constituency_id=location['constituency']['id'] if location['constituency'] else None,
                                  geographic_ambiguity=json.dumps(location['ambiguities']) if location['ambiguities'] else None)
            db.add(complaint)
            db.flush()
            reference = complaint.id
        events.append(current)
        return {'reference_id': reference, 'message': 'Your complaint has been recorded.'}

    @app.get('/api/complaints', response_model=ComplaintPage)
    def complaints(f: F, q: Q, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), sort: Literal['newest', 'oldest'] = 'newest'):
        return q.page(f, page, page_size, sort)

    @app.get('/api/clusters', response_model=list[Category])
    def clusters(f: F, q: Q, search: str = Query('', max_length=100)):
        return [c for c in q.categories(f) if c['id'] and search.casefold() in c['label'].casefold()]

    @app.get('/api/clusters/{cluster_id}', response_model=Category)
    def cluster(cluster_id: str, f: F, q: Q):
        item = q.clusters.get(cluster_id)
        if not item or not item.active:
            raise HTTPException(404, 'Category not found or merged. Refresh the category list.')
        categories = q.categories(f.model_copy(update={'cluster_id': cluster_id}))
        return categories[0] if categories else {'id': item.id, 'label': item.label, 'count': 0, 'share': 0, 'growth': 0, 'new': False, 'representative_text': item.representative_text}

    @app.get('/api/clusters/{cluster_id}/complaints', response_model=ComplaintPage)
    def cluster_complaints(cluster_id: str, f: F, q: Q, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
        return q.page(f.model_copy(update={'cluster_id': cluster_id}), page, page_size)

    @app.get('/api/geography/states', response_model=list[RegionPublic])
    def states():
        return geo.regions('state')

    @app.get('/api/geography/districts', response_model=list[RegionPublic])
    def districts(state_id: str | None = None):
        return geo.regions('district', state_id)

    @app.get('/api/geography/constituencies', response_model=list[RegionPublic])
    def constituencies(state_id: str | None = None):
        return geo.regions('constituency', state_id)

    @app.get('/api/geography/resolve', response_model=Resolution)
    def resolve(latitude: float = Query(ge=-90, le=90), longitude: float = Query(ge=-180, le=180)):
        location = geo.resolve(latitude, longitude)
        return {k: location[k] for k in ('state', 'district', 'constituency')} | {'coverage_note': 'Historical boundaries; constituency may be unknown. Public map positions are approximate.'}

    @app.get('/api/geography/boundaries', response_model=GeoJSON)
    def boundaries(level: Literal['state', 'district', 'constituency'] = 'state', state_id: str | None = None):
        return geo.boundaries(level, state_id)

    @app.get('/api/map/heatmap', response_model=GeoJSON)
    def heatmap(f: F, q: Q):
        return q.points(f, aggregate=True)

    @app.get('/api/map/complaints', response_model=GeoJSON)
    def map_complaints(f: F, q: Q):
        return q.points(f)

    @app.get('/api/map/regions', response_model=list[GeographicCount])
    def map_regions(f: F, q: Q, level: Literal['state', 'district', 'constituency'] = 'state'):
        return q.geography(f, level)

    @app.get('/api/analytics/overview', response_model=Overview)
    def overview(f: F, q: Q):
        return q.overview(f)

    @app.get('/api/analytics/categories', response_model=list[Category])
    def categories(f: F, q: Q):
        return q.categories(f)

    @app.get('/api/analytics/geography', response_model=list[GeographicCount])
    def geographic(f: F, q: Q, level: Literal['state', 'district', 'constituency'] = 'state'):
        return q.geography(f, level)

    @app.get('/api/analytics/timeline', response_model=list[TimelinePoint])
    def timeline(f: F, q: Q, interval: Literal['day', 'week'] = 'day'):
        return q.timeline(f, interval)

    @app.get('/api/analytics/trends', response_model=Trends)
    def trends(f: F, q: Q):
        return q.trends(f)

    return app


app = create_app()
