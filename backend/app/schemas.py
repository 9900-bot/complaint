from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator, model_validator
from app.config import settings


class Submission(BaseModel):
    model_config = ConfigDict(extra='forbid')
    email: EmailStr = Field(max_length=254)
    text: str = Field(min_length=10, max_length=settings.complaint_max_length)
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)

    @field_validator('text')
    @classmethod
    def meaningful(cls, value):
        value = value.strip()
        if len(value) < 10:
            raise ValueError('Describe the concern in at least 10 characters.')
        return value


class SubmissionResult(BaseModel):
    reference_id: str
    message: str


class Filters(BaseModel):
    state_id: str | None = None
    district_id: str | None = None
    constituency_id: str | None = None
    cluster_id: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    bbox: str | None = None

    @model_validator(mode='after')
    def dates(self):
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError('Start date must be before end date.')
        return self

    @field_validator('bbox')
    @classmethod
    def bounds(cls, value):
        if value:
            try:
                west, south, east, north = map(float, value.split(','))
                if not (-180 <= west <= east <= 180 and -90 <= south <= north <= 90):
                    raise ValueError()
            except (ValueError, TypeError):
                raise ValueError('bbox must be west,south,east,north within valid bounds.')
        return value


class PublicComplaint(BaseModel):
    id: str
    text: str
    created_at: datetime
    category_id: str | None
    category: str | None
    state: str | None
    district: str | None
    constituency: str | None
    is_demo: bool


class ComplaintPage(BaseModel):
    items: list[PublicComplaint]
    total: int
    page: int
    page_size: int


class Category(BaseModel):
    id: str | None
    label: str
    count: int
    share: float
    growth: int
    new: bool
    representative_text: str | None = None


class Overview(BaseModel):
    total: int
    total_all_dates: int
    active_clusters: int
    states: int
    top_category: str | None
    latest_submission: datetime | None
    demo_count: int


class GeographicCount(BaseModel):
    id: str
    name: str
    count: int
    top_category: str | None = None


class TimelinePoint(BaseModel):
    date: str
    count: int
    categories: dict[str, int]


class Trends(BaseModel):
    current: int
    previous: int
    change: int
    emerging: list[Category]


class RegionPublic(BaseModel):
    id: str
    name: str
    region_type: str
    parent_region_id: str | None
    dataset_version: str


class Resolution(BaseModel):
    state: RegionPublic | None
    district: RegionPublic | None
    constituency: RegionPublic | None
    coverage_note: str


class GeoJSON(BaseModel):
    type: Literal['FeatureCollection'] = 'FeatureCollection'
    features: list[dict]


class PublicConfig(BaseModel):
    complaint_max_length: int
    geography_available: bool
    boundary_vintage: str
    public_grid_degrees: float
