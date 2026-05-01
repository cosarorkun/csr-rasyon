"""SQLite + SQLAlchemy models, engine, versioned migrations, and one-time seeding.

Design rules (so live data on Railway stays safe):

1. ``Base.metadata.create_all`` is the only "auto-create" step. It creates tables
   that don't yet exist; it never alters existing tables.
2. ``init_db`` seeds users + feeds **only** when those tables are empty.
   Existing users and saved rations are never touched.
3. Each one-time data fix is a numbered migration tracked in
   ``schema_migrations``. A migration runs at most once, ever, on a given DB.
   Future admin edits in the feeds table are NOT overwritten on restart.
"""

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

# Env var name preserved as DOYA_DB_PATH so existing Railway deploys keep working.
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
    customer_name = Column(String, nullable=True)
    herd_name = Column(String, nullable=True)
    live_weight = Column(Float, nullable=False)
    target_gain = Column(Float, nullable=True)
    breed = Column(String, nullable=True)
    ration_json = Column(Text, nullable=False)
    results_json = Column(Text, nullable=False)
    # Added by migration 001
    # Added by migration 003
    ration_type = Column(String(10), nullable=False, default="besi", server_default="besi")

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
    # Added by migration 004
    category = Column(String(20), nullable=False, default="besi", server_default="besi")
    rdp_pct_of_cp = Column(Float, nullable=True)
    rup_pct_of_cp = Column(Float, nullable=True)
    pdi_g_per_kg_dm = Column(Float, nullable=True)
    ufl_per_kg_dm = Column(Float, nullable=True)
    ndf_pct = Column(Float, nullable=True)
    ca_pct = Column(Float, nullable=True)
    p_pct = Column(Float, nullable=True)
    note = Column(Text, nullable=True)


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
        "category": feed.category or "besi",
        "rdp_pct_of_cp": feed.rdp_pct_of_cp,
        "rup_pct_of_cp": feed.rup_pct_of_cp,
        "pdi_g_per_kg_dm": feed.pdi_g_per_kg_dm,
        "ufl_per_kg_dm": feed.ufl_per_kg_dm,
        "ndf_pct": feed.ndf_pct,
        "ca_pct": feed.ca_pct,
        "p_pct": feed.p_pct,
        "note": feed.note,
    }


# ---------------------------------------------------------------------------
# Versioned migration system
# ---------------------------------------------------------------------------

def _m001_add_customer_name_to_saved_rations(conn) -> None:
    cols = {row[1] for row in conn.exec_driver_sql(
        "PRAGMA table_info(saved_rations)"
    ).fetchall()}
    if "customer_name" not in cols:
        conn.exec_driver_sql(
            "ALTER TABLE saved_rations ADD COLUMN customer_name VARCHAR"
        )


def _m002_remove_obsolete_feeds_and_fix_csr_sdf(conn) -> None:
    obsolete_names = [
        "Buzağı Büyütme", "Efe Toz", "Efect Besi Başlangıç",
        "Grand", "Pehlivan", "Pehlivan Toz", "Yiğit", "Çevik",
    ]
    for name in obsolete_names:
        conn.exec_driver_sql("DELETE FROM feeds WHERE name = ?", (name,))

    conn.exec_driver_sql(
        "UPDATE feeds SET pdie = ?, pdin = ? WHERE name = ?",
        (108.0, 108.0, "CSR CD BESİ"),
    )
    conn.exec_driver_sql(
        "UPDATE feeds SET pdie = ?, pdin = ? WHERE name = ?",
        (114.73, 114.73, "SDF H"),
    )


def _m003_add_ration_type_to_saved_rations(conn) -> None:
    cols = {row[1] for row in conn.exec_driver_sql(
        "PRAGMA table_info(saved_rations)"
    ).fetchall()}
    if "ration_type" not in cols:
        conn.exec_driver_sql(
            "ALTER TABLE saved_rations ADD COLUMN ration_type VARCHAR(10) NOT NULL DEFAULT 'besi'"
        )


def _m004_add_dairy_columns_and_seed_dairy_feeds(conn) -> None:
    """Add dairy columns to feeds table; insert 12 dairy feeds if absent."""
    from data import DAIRY_FEEDS as _DAIRY_FEEDS

    # 1. Add new columns (idempotent via PRAGMA check)
    cols = {row[1] for row in conn.exec_driver_sql(
        "PRAGMA table_info(feeds)"
    ).fetchall()}
    for col_name, col_def in [
        ("category",        "VARCHAR(20) NOT NULL DEFAULT 'besi'"),
        ("rdp_pct_of_cp",   "FLOAT"),
        ("rup_pct_of_cp",   "FLOAT"),
        ("pdi_g_per_kg_dm", "FLOAT"),
        ("ufl_per_kg_dm",   "FLOAT"),
        ("ndf_pct",         "FLOAT"),
        ("ca_pct",          "FLOAT"),
        ("p_pct",           "FLOAT"),
        ("note",            "TEXT"),
    ]:
        if col_name not in cols:
            conn.exec_driver_sql(
                f"ALTER TABLE feeds ADD COLUMN {col_name} {col_def}"
            )

    # 2. Insert dairy feeds (skip any that already exist by name)
    for f in _DAIRY_FEEDS:
        exists = conn.exec_driver_sql(
            "SELECT 1 FROM feeds WHERE name = ?", (f["name"],)
        ).fetchone()
        if exists:
            continue
        conn.exec_driver_sql(
            """INSERT INTO feeds
               (name, dm_pct, ufv, protein, pdie, pdin, cf, fat, ash, starch,
                is_custom, category,
                rdp_pct_of_cp, rup_pct_of_cp, pdi_g_per_kg_dm,
                ufl_per_kg_dm, ndf_pct, ca_pct, p_pct, note)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                f["name"], f["dm_pct"], f.get("ufv", 0), f["protein"],
                f.get("pdie", 0), f.get("pdin", 0),
                f.get("cf", 0), f.get("fat", 0), f.get("ash", 0), f.get("starch", 0),
                0,  # is_custom = False
                f.get("category", "sut"),
                f.get("rdp_pct_of_cp"), f.get("rup_pct_of_cp"),
                f.get("pdi_g_per_kg_dm"), f.get("ufl_per_kg_dm"),
                f.get("ndf_pct"), f.get("ca_pct"), f.get("p_pct"),
                f.get("note"),
            ),
        )


_MIGRATIONS: list[tuple[str, callable]] = [
    ("001_add_customer_name_to_saved_rations",          _m001_add_customer_name_to_saved_rations),
    ("002_remove_obsolete_feeds_and_fix_csr_sdf",       _m002_remove_obsolete_feeds_and_fix_csr_sdf),
    ("003_add_ration_type_to_saved_rations",            _m003_add_ration_type_to_saved_rations),
    ("004_add_dairy_columns_and_seed_dairy_feeds",      _m004_add_dairy_columns_and_seed_dairy_feeds),
]


def _run_migrations() -> None:
    with engine.begin() as conn:
        conn.exec_driver_sql(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                name VARCHAR PRIMARY KEY,
                applied_at DATETIME NOT NULL
            )
            """
        )
        applied = {
            row[0]
            for row in conn.exec_driver_sql(
                "SELECT name FROM schema_migrations"
            ).fetchall()
        }
        for name, fn in _MIGRATIONS:
            if name in applied:
                continue
            fn(conn)
            conn.exec_driver_sql(
                "INSERT INTO schema_migrations (name, applied_at) VALUES (?, ?)",
                (name, datetime.utcnow().isoformat()),
            )


def init_db() -> None:
    """Create tables, run idempotent migrations, and seed initial data once."""
    from auth import hash_password
    from data import FEEDS as SEED_FEEDS, DAIRY_FEEDS as SEED_DAIRY_FEEDS

    Base.metadata.create_all(bind=engine)
    _run_migrations()

    seed_users = [
        ("sezer.karabulut", "SezerCsrRasyon2026.", False),
        ("emre.basar",      "EmreCsrRasyon2026.", False),
        ("ayhan.cosar",     "26051108Ac.",         True),
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
            all_seeds = []
            for f in SEED_FEEDS:
                all_seeds.append(Feed(
                    name=f["name"], dm_pct=f["dm_pct"], ufv=f["ufv"],
                    protein=f["protein"], pdie=f["pdie"], pdin=f["pdin"],
                    cf=f.get("cf", 0), fat=f.get("fat", 0),
                    ash=f.get("ash", 0), starch=f.get("starch", 0),
                    is_custom=False, category="besi",
                ))
            for f in SEED_DAIRY_FEEDS:
                all_seeds.append(Feed(
                    name=f["name"], dm_pct=f["dm_pct"], ufv=f.get("ufv", 0),
                    protein=f["protein"], pdie=f.get("pdie", 0), pdin=f.get("pdin", 0),
                    cf=f.get("cf", 0), fat=f.get("fat", 0),
                    ash=f.get("ash", 0), starch=f.get("starch", 0),
                    is_custom=False,
                    category=f.get("category", "sut"),
                    rdp_pct_of_cp=f.get("rdp_pct_of_cp"),
                    rup_pct_of_cp=f.get("rup_pct_of_cp"),
                    pdi_g_per_kg_dm=f.get("pdi_g_per_kg_dm"),
                    ufl_per_kg_dm=f.get("ufl_per_kg_dm"),
                    ndf_pct=f.get("ndf_pct"),
                    ca_pct=f.get("ca_pct"),
                    p_pct=f.get("p_pct"),
                    note=f.get("note"),
                ))
            db.add_all(all_seeds)
            db.commit()
