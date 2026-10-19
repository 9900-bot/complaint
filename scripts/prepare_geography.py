"""Download pinned DataMeet shapefiles, validate and build local atlas assets."""
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMIT = 'b3fbbde595310b397a55d718e0958ce249a4fa1f'
DATA = ROOT / 'data/geography'
SOURCES = {
    'state': 'States/Admin2',
    'district': 'Districts/Census_2011/2011_Dist',
    'constituency': 'assembly-constituencies/India_AC',
}


def download():
    hashes = {}
    baseline = DATA / 'source-manifest.json'
    expected = json.loads(baseline.read_text())['sha256'] if baseline.exists() else {}
    for prefix in SOURCES.values():
        for ext in ('shp', 'shx', 'dbf', 'prj'):
            relative = f'{prefix}.{ext}'
            target = DATA / 'raw' / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists() or (relative in expected and hashlib.sha256(target.read_bytes()).hexdigest() != expected[relative]):
                print(f'Downloading {relative}', flush=True)
                temporary = target.with_suffix(target.suffix + '.partial')
                urllib.request.urlretrieve(f'https://raw.githubusercontent.com/datameet/maps/{COMMIT}/{relative}', temporary)
                temporary.replace(target)
            hashes[relative] = hashlib.sha256(target.read_bytes()).hexdigest()
            if relative in expected and hashes[relative] != expected[relative]:
                raise ValueError(f'Source checksum mismatch: {relative}')
    return hashes


def prepare():
    import shapefile
    from shapely import make_valid
    from shapely.geometry import shape, mapping
    hashes = download()
    features = []
    skipped_assemblies = 0
    repaired = 0
    diagnostics = {}
    for kind, prefix in SOURCES.items():
        reader = shapefile.Reader(str(DATA / 'raw' / prefix), encoding='utf-8', encodingErrors='replace')
        crs = (DATA / 'raw' / (prefix + '.prj')).read_text()
        if 'WGS_1984' not in crs and 'WGS 84' not in crs:
            raise ValueError(f'Unexpected source CRS for {kind}; explicit transformation is required')
        print(kind, [f[0] for f in reader.fields[1:]], flush=True)
        diagnostics[kind] = {'source_records': len(reader)}
        for number, row in enumerate(reader.iterShapeRecords()):
            props = row.record.as_dict()
            if kind == 'constituency' and (not props.get('AC_NO') or not str(props.get('AC_NAME') or '').strip()):
                skipped_assemblies += 1
                continue  # Unidentified source fragments are not invented constituencies.
            if number == 0:
                print('example', props, flush=True)
            geometry = shape(row.shape.__geo_interface__)
            if not geometry.is_valid:
                geometry = make_valid(geometry)
                repaired += 1
            if geometry.geom_type == 'GeometryCollection':
                from shapely.ops import unary_union
                geometry = unary_union([g for g in geometry.geoms if g.geom_type in ('Polygon', 'MultiPolygon')])
            if geometry.is_empty or geometry.geom_type not in ('Polygon', 'MultiPolygon'):
                raise ValueError(f'Unsupported geometry: {kind}/{number}')
            if kind == 'state':
                name = str(props.get('ST_NM') or props.get('NAME_1') or props.get('NAME') or '').strip()
                code = str(props.get('ST_CODE') or number + 1)
            elif kind == 'district':
                name = str(props.get('DISTRICT') or props.get('DIST_NAME') or props.get('NAME_2') or '').strip()
                code = f"census-{props['censuscode']}" if props.get('censuscode') else f'record-{number + 1}'
            else:
                name = str(props.get('AC_NAME') or f"Assembly {props.get('AC_NO', number + 1)}").strip()
                code = f"{props.get('ST_CODE', '')}-{props.get('AC_NO', number + 1)}"
            if not name:
                raise ValueError(f'Missing name for {kind}: {props}')
            region_id = f'{kind}:{code}'
            features.append({'id': region_id, 'stable_code': region_id, 'name': name.title(), 'region_type': kind,
                             'parent_region_id': None, 'dataset_version': COMMIT, 'geometry': mapping(geometry),
                             'display_geometry': mapping(geometry.simplify(0.012 if kind == 'state' else 0.004, preserve_topology=True))})
    # Multipart constituencies are sometimes separate source records with the same identity.
    from shapely.ops import unary_union
    grouped = {}
    for feature in features:
        if feature['id'] in grouped:
            current = grouped[feature['id']]
            if current['name'] != feature['name']:
                raise ValueError(f"Conflicting names for {feature['id']}")
            geometry = unary_union([shape(current['geometry']), shape(feature['geometry'])])
            current['geometry'] = mapping(geometry)
            current['display_geometry'] = mapping(geometry.simplify(0.004, preserve_topology=True))
        else:
            grouped[feature['id']] = feature
    dissolved_records = len(features) - len(grouped)
    features = list(grouped.values())
    # Link districts/assemblies independently to the state containing most of their area.
    # Source state names/codes have incompatible vintages; never use text matching for point resolution.
    from shapely.strtree import STRtree
    states = [f for f in features if f['region_type'] == 'state']
    state_shapes = [shape(f['geometry']) for f in states]
    index = STRtree(state_shapes)
    orphaned = []
    for number, feature in enumerate(features):
        if feature['region_type'] == 'state':
            continue
        geometry = shape(feature['geometry'])
        candidates = index.query(geometry, predicate='intersects')
        if len(candidates):
            best = candidates[0] if len(candidates) == 1 else max(candidates, key=lambda i: (geometry.intersection(state_shapes[i]).area, states[i]['id']))
            feature['parent_region_id'] = states[best]['id']
        else:
            orphaned.append(feature['id'])
        if number % 500 == 0:
            print(f'Validated geographic parents: {number}/{len(features)}', flush=True)
    ids = [f['id'] for f in features]
    if len(set(ids)) != len(ids):
        raise ValueError('Source identifiers are not unique')
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / 'regions.json').write_text(json.dumps(features, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    manifest = {'source': 'DataMeet Community Maps', 'commit': COMMIT, 'crs': 'EPSG:4326',
                'sha256': hashes, 'coverage': diagnostics, 'imported_counts': {kind: sum(f['region_type']==kind for f in features) for kind in SOURCES},
                'repaired_geometries': repaired, 'orphaned_regions': orphaned,
                'dissolved_multipart_records': dissolved_records, 'skipped_unidentified_assembly_fragments': skipped_assemblies,
                'license': 'CC BY 2.5 India (layer-specific); repository default CC BY 4.0',
                'vintage': 'Historical state boundaries, Census 2011 districts, historical ECI-scraped Assembly constituencies'}
    (DATA / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps(manifest, indent=2))
    if '--download-only' not in sys.argv:
        sys.path.insert(0, str(ROOT / 'backend'))
        from app.database import SessionLocal
        from app.geography import Geography
        Geography(DATA / 'regions.json').import_metadata(SessionLocal)
        print('Region metadata imported into SQLite.')


if __name__ == '__main__':
    prepare()
