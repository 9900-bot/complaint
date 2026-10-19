from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.config import settings


class Base(DeclarativeBase):
    pass


def make_engine(url: str):
    engine = create_engine(url, connect_args={'check_same_thread': False, 'timeout': 15})

    @event.listens_for(engine, 'connect')
    def pragmas(connection, _):
        cursor = connection.cursor()
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.execute('PRAGMA journal_mode=WAL')
        cursor.execute('PRAGMA busy_timeout=15000')
        cursor.close()

    return engine


engine = make_engine(settings.database_url)
SessionLocal = sessionmaker(engine, expire_on_commit=False)
