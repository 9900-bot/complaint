from collections import Counter, defaultdict
from datetime import datetime, timedelta, date, time
from math import floor
from sqlalchemy import select
from app.models import Complaint, Cluster, Region
from app.schemas import Filters

GRID = 0.05
INDIA_OFFSET = timedelta(hours=5, minutes=30)


def local_date(value):
    return (value + INDIA_OFFSET).date()


def approximate(latitude, longitude):
    # Stable cell centers, shared by heatmap and individual view. Never random offsets.
    return (round((floor(longitude / GRID) + .5) * GRID, 3), round((floor(latitude / GRID) + .5) * GRID, 3))


class PublicQueries:
    def __init__(self, db):
        self.db = db
        self.clusters = {c.id: c for c in db.scalars(select(Cluster))}
        self.regions = {r.id: r for r in db.scalars(select(Region))}

    def rows(self, filters: Filters):
        stmt = select(Complaint)
        for field in ('state_id', 'district_id', 'constituency_id', 'cluster_id'):
            value = getattr(filters, field)
            if value:
                stmt = stmt.where(getattr(Complaint, field) == value)
        if filters.date_from:
            stmt = stmt.where(Complaint.created_at >= datetime.combine(filters.date_from, time.min) - INDIA_OFFSET)
        if filters.date_to:
            stmt = stmt.where(Complaint.created_at < datetime.combine(filters.date_to + timedelta(days=1), time.min) - INDIA_OFFSET)
        rows = list(self.db.scalars(stmt.order_by(Complaint.created_at.desc(), Complaint.id)))
        if filters.bbox:
            west, south, east, north = map(float, filters.bbox.split(','))
            # Filter on PUBLIC grid positions, not private coordinates (prevents bbox binary-search attacks).
            rows = [c for c in rows if west <= approximate(c.latitude, c.longitude)[0] <= east and south <= approximate(c.latitude, c.longitude)[1] <= north]
        return rows

    def region_name(self, region_id):
        return self.regions[region_id].name if region_id in self.regions else None

    def category_name(self, cluster_id):
        return self.clusters[cluster_id].label if cluster_id in self.clusters else None

    def public(self, c):
        return {'id': c.id, 'text': c.original_text, 'created_at': c.created_at, 'category_id': c.cluster_id,
                'category': self.category_name(c.cluster_id), 'state': self.region_name(c.state_id),
                'district': self.region_name(c.district_id), 'constituency': self.region_name(c.constituency_id), 'is_demo': c.is_demo}

    def page(self, filters, page=1, page_size=20, sort='newest'):
        rows = self.rows(filters)
        if sort == 'oldest':
            rows.reverse()
        return {'items': [self.public(c) for c in rows[(page-1)*page_size:page*page_size]], 'total': len(rows), 'page': page, 'page_size': page_size}

    def window(self, filters, rows):
        end = filters.date_to or local_date(datetime.utcnow())
        start = filters.date_from or end - timedelta(days=29)
        midpoint = start + timedelta(days=(end-start).days // 2)
        return start, end, midpoint

    def categories(self, filters):
        rows = self.rows(filters)
        counts = Counter(c.cluster_id for c in rows)
        start, end, midpoint = self.window(filters, rows)
        early = Counter(c.cluster_id for c in rows if start <= local_date(c.created_at) <= midpoint)
        late = Counter(c.cluster_id for c in rows if midpoint < local_date(c.created_at) <= end)
        return [{'id': key, 'label': self.category_name(key) or 'Uncategorised', 'count': count,
                 'share': round(count / len(rows) * 100, 2), 'growth': late[key] - early[key],
                 'new': bool(key and start <= local_date(self.clusters[key].created_at) <= end),
                 'representative_text': self.clusters[key].representative_text if key else None}
                for key, count in sorted(counts.items(), key=lambda item: (-item[1], str(item[0])))]

    def overview(self, filters):
        rows = self.rows(filters)
        categories = self.categories(filters)
        all_dates = self.rows(filters.model_copy(update={'date_from': None, 'date_to': None}))
        return {'total': len(rows), 'total_all_dates': len(all_dates), 'active_clusters': len({c.cluster_id for c in rows if c.cluster_id}),
                'states': len({c.state_id for c in rows}), 'top_category': categories[0]['label'] if categories else None,
                'latest_submission': max((c.created_at for c in rows), default=None), 'demo_count': sum(c.is_demo for c in rows)}

    def geography(self, filters, level='state'):
        rows = self.rows(filters)
        grouped = defaultdict(list)
        for c in rows:
            key = getattr(c, level + '_id')
            if key:
                grouped[key].append(c)
        return [{'id': key, 'name': self.region_name(key), 'count': len(items),
                 'top_category': self.category_name(Counter(c.cluster_id for c in items).most_common(1)[0][0])}
                for key, items in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0]))]

    def timeline(self, filters, interval='day'):
        rows = self.rows(filters)
        end = filters.date_to or local_date(datetime.utcnow())
        start = filters.date_from or (min((local_date(c.created_at) for c in rows), default=end - timedelta(days=29)))
        # Protect localhost from unbounded ranges; API validates maximum range independently.
        start = max(start, end - timedelta(days=3660))
        step = 7 if interval == 'week' else 1
        if interval == 'week':
            start -= timedelta(days=start.weekday())
        buckets = {}
        day = start
        while day <= end:
            buckets[day.isoformat()] = {'date': day.isoformat(), 'count': 0, 'categories': {}}
            day += timedelta(days=step)
        for c in rows:
            day = local_date(c.created_at)
            if interval == 'week':
                day -= timedelta(days=day.weekday())
            bucket = buckets.get(day.isoformat())
            if bucket is not None:
                bucket['count'] += 1
                label = c.cluster_id or 'uncategorised'
                bucket['categories'][label] = bucket['categories'].get(label, 0) + 1
        return list(buckets.values())

    def trends(self, filters):
        rows = self.rows(filters)
        start, end, _ = self.window(filters, rows)
        previous_start = start - timedelta(days=(end-start).days + 1)
        previous = self.rows(filters.model_copy(update={'date_from': previous_start, 'date_to': start-timedelta(days=1)}))
        current = sum(start <= local_date(c.created_at) <= end for c in rows)
        return {'current': current, 'previous': len(previous), 'change': current-len(previous),
                'emerging': [c for c in self.categories(filters) if c['new'] and c['id']]}

    def points(self, filters, aggregate=False):
        rows = self.rows(filters)
        if aggregate:
            cells = Counter(approximate(c.latitude, c.longitude) for c in rows)
            return {'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': list(cell)}, 'properties': {'count': count}} for cell, count in cells.items()]}
        return {'type': 'FeatureCollection', 'features': [
            {'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': list(approximate(c.latitude, c.longitude))},
             'properties': self.public(c)} for c in rows]}
