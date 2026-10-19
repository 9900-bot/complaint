import json
from pathlib import Path
from shapely.geometry import shape, Point, mapping
from shapely.strtree import STRtree
from sqlalchemy import select
from app.models import Region


class Geography:
    def __init__(self, path: Path):
        self.features = json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
        self.by_id = {f['id']: f for f in self.features}
        self.layers = {}
        for kind in ('state', 'district', 'constituency'):
            items = [f for f in self.features if f['region_type'] == kind]
            geometries = [shape(f['geometry']) for f in items]
            self.layers[kind] = (items, geometries, STRtree(geometries))

    def import_metadata(self, sessions):
        with sessions.begin() as db:
            existing = set(db.scalars(select(Region.id)).all())
            for f in self.features:
                if f['id'] not in existing:
                    db.add(Region(**{k: f[k] for k in ('id', 'stable_code', 'name', 'region_type', 'parent_region_id', 'dataset_version')}, geometry_reference=f['id']))
                    # Commit state inserts first to satisfy immediate FK checks.
                    if f['region_type'] == 'state':
                        db.flush()

    def resolve(self, latitude: float, longitude: float):
        point = Point(longitude, latitude)
        result = {'state': None, 'district': None, 'constituency': None, 'ambiguities': {}}
        for kind, (items, geometries, index) in self.layers.items():
            matches = [int(i) for i in index.query(point, predicate='intersects')]
            if kind != 'state' and result['state']:
                matches = [i for i in matches if items[i]['parent_region_id'] == result['state']['id']]
            # Shared boundaries/overlaps resolve to smallest polygon, then stable ID.
            matches.sort(key=lambda i: (geometries[i].area, items[i]['id']))
            if matches:
                result[kind] = self.public(items[matches[0]])
            if len(matches) > 1:
                result['ambiguities'][kind] = [items[i]['id'] for i in matches]
        return result

    @staticmethod
    def public(f):
        return {k: f[k] for k in ('id', 'name', 'region_type', 'parent_region_id', 'dataset_version')}

    def regions(self, kind, state_id=None):
        return sorted([self.public(f) for f in self.features if f['region_type'] == kind and (not state_id or f['parent_region_id'] == state_id)], key=lambda f: f['name'])

    def boundaries(self, kind, state_id=None):
        return {'type': 'FeatureCollection', 'features': [
            {'type': 'Feature', 'id': n, 'properties': self.public(f), 'geometry': f['display_geometry']}
            for n, f in enumerate(self.features) if f['region_type'] == kind and (not state_id or (f['id'] == state_id if kind == 'state' else f['parent_region_id'] == state_id))
        ]}
