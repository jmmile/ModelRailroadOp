from sqlalchemy.orm import sessionmaker

from modelrailroadops.database.engine import engine

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)