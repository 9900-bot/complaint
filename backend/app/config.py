from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / '.env', extra='ignore')
    database_url: str = f"sqlite:///{(ROOT / 'data' / 'atlas.db').as_posix()}"
    geography_path: Path = ROOT / 'data/geography/regions.json'
    bi_encoder: str = 'sentence-transformers/all-MiniLM-L6-v2'
    cross_encoder: str = 'cross-encoder/stsb-TinyBERT-L4'
    bi_revision: str = '1110a243fdf4706b3f48f1d95db1a4f5529b4d41'
    cross_revision: str = '1f478482145797a0cac02d6b9ab3c65c9d25fb1e'
    membership_threshold: float = 0.62
    merge_threshold: float = 0.92
    merge_candidate_similarity: float = 0.55
    merge_top_k: int = 5
    merge_iterations: int = 3
    complaint_max_length: int = 3000
    worker_enabled: bool = True
    worker_poll_seconds: float = 2
    worker_max_attempts: int = 3
    rate_limit_per_minute: int = 12


settings = Settings()
