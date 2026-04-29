"""SQLite + SQLAlchemy models, engine, and seeding."""

import os
from datetime import datetime
from typing import Generator

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

DB_PATH = os.environ.get("DOYA_DB_PATH", "./rasyon.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    rations = relationship(
        "SavedRation", back_populates="user", cascade="all, delete-orphan"
    )


class SavedRation(Base):
    __tablename__ = "saved_rations"
    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    herd_name = Column(String, nullable=True)
    live_weight = Column(Float, nullable=False)
    target_gain = Column(Float, nullable=True)
    breed = Column(String, nullable=True)
    ration_json = Column(Text, nullable=False)
    results_json = Column(Text, nullable=False)

    user = relationship("User", back_populates="rations")


class Feed(Base):
    __tablename__ = "feeds"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)
    dm_pct = Column(Float, nullable=False)
    ufv = Column(Float, nullable=False)
    protein = Column(Float, nullable=False)
    pdie = Column(Float, nullable=False)
    pdin = Column(Float, nullable=False)
    cf = Column(Float, nullable=False, default=0)
    fat = Column(Float, nullable=False, default=0)
    ash = Column(Float, nullable=False, default=0)
    starch = Column(Float, nullable=False, default=0)
    is_custom = Column(Boolean, default=True, nullable=False)
    created_by = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def feed_to_dict(feed: Feed) -> dict:
    return {
        "id": feed.id,
        "name": feed.name,
        "dm_pct": feed.dm_pct,
        "ufv": feed.ufv,
        "protein": feed.protein,
        "pdie": feed.pdie,
        "pdin": feed.pdin,
        "cf": feed.cf,
        "fat": feed.fat,
        "ash": feed.ash,
        "starch": feed.starch,
        "is_custom": feed.is_custom,
    }


def init_db() -> None:
    """Create tables and seed initial users + feeds on first run."""
    # Local imports avoid circular dependency at module load.
    from auth import hash_password
    from data import FEEDS as SEED_FEEDS

    Base.metadata.create_all(bind=engine)

    seed_users = [
        ("sezer.karabulut", "SezerCsrRasyon2026.", False),
        ("emre.basar", "EmreCsrRasyon2026.", False),
        ("ayhan.cosar", "26051108Ac.", True),
    ]

    with SessionLocal() as db:
        if db.query(User).count() == 0:
            db.add_all(
                User(
                    username=u,
                    hashed_password=hash_password(p),
                    is_admin=admin,
                )
                for (u, p, admin) in seed_users
            )
            db.commit()

        if db.query(Feed).count() == 0:
            db.add_all(
                Feed(
                    name=f["name"],
                    dm_pct=f["dm_pct"],
                    ufv=f["ufv"],
                    protein=f["protein"],
                    pdie=f["pdie"],
                    pdin=f["pdin"],
                    cf=f["cf"],
                    fat=f["fat"],
                    ash=f["ash"],
                    starch=f["starch"],
                    is_custom=False,
                )
                for f in SEED_FEEDS
            )
            db.commit()
