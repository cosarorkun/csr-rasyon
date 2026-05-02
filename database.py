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
    nfc_pct = Column(Float, nullable=True)
    endf_pct = Column(Float, nullable=True)
    ca_pct = Column(Float, nullable=True)
    p_pct = Column(Float, nullable=True)
    ton_maliyeti = Column(Float, nullable=True)
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
        "nfc_pct": feed.nfc_pct,
        "endf_pct": feed.endf_pct,
        "ca_pct": feed.ca_pct,
        "p_pct": feed.p_pct,
        "ton_maliyeti": feed.ton_maliyeti,
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
        # nfc_pct/endf_pct/ton_maliyeti added by migration 005; update if present
        if f.get("nfc_pct") is not None or f.get("endf_pct") is not None:
            conn.exec_driver_sql(
                "UPDATE feeds SET nfc_pct=?, endf_pct=? WHERE name=?",
                (f.get("nfc_pct"), f.get("endf_pct"), f["name"]),
            )


def _m005_add_nfc_endf_cost_and_backfill(conn) -> None:
    """Add nfc_pct, endf_pct, ton_maliyeti columns and backfill nutrient data."""
    cols = {row[1] for row in conn.exec_driver_sql(
        "PRAGMA table_info(feeds)"
    ).fetchall()}
    for col_name, col_def in [
        ("nfc_pct",      "FLOAT"),
        ("endf_pct",     "FLOAT"),
        ("ton_maliyeti", "FLOAT"),
    ]:
        if col_name not in cols:
            conn.exec_driver_sql(f"ALTER TABLE feeds ADD COLUMN {col_name} {col_def}")

    # Backfill NDF, NFC, eNDF, Ca, P for the 37 besi feeds (from Excel BESİ sheet).
    # Only updates rows where the value is currently NULL to preserve any admin edits.
    _BACKFILL = [
        ("Mısır silajı 35 KM iyi",   41.6,  45.0,   33.28,  0.08, 0.13),
        ("Mısır silajı 35 KM orta",  47.7,  35.0,   38.16,  0.08, 0.13),
        ("Mısır silajı 35 KM kötü",  54.8,  28.0,   43.84,  0.08, 0.13),
        ("Mısır silajı 30 KM iyi",   44.4,  42.6,   35.52,  0.08, 0.13),
        ("Mısır silajı 30 KM orta",  53.6,  30.5,   42.88,  0.08, 0.13),
        ("Mısır silajı 30 KM kötü",  62.0,  21.8,   49.6,   0.08, 0.13),
        ("Mısır silajı 25 KM iyi",   54.0,  31.7,   43.2,   0.08, 0.13),
        ("Mısır silajı 25 KM orta",  58.0,  25.9,   46.4,   0.08, 0.13),
        ("Mısır silajı 25 KM kötü",  61.0,  21.32,  48.8,   0.08, 0.13),
        ("Yonca 15 prt",             50.4,  None,   44.352, 2.04, 0.26),
        ("Yonca 17.5 prt",           47.7,  None,   41.976, 2.18, 0.26),
        ("Yonca 18.5 prt",           46.4,  None,   40.832, 2.22, 0.26),
        ("Yonca 23 prt",             37.7,  None,   33.176, 2.5,  0.26),
        ("Pancar Posası",            48.0,  39.7,   None,   0.28, 0.08),
        ("Yulaf Otu",                61.9,  15.5,   55.7,   None, None),
        ("Fiğ Yulaf Otu",            55.9,  18.0,   50.3,   None, None),
        ("Fiğ Otu",                  38.8,  19.0,   34.9,   None, None),
        ("Arpa Otu",                 68.0,  None,   61.22,  0.14, 0.05),
        ("Saman",                    79.8,  None,   75.81,  0.08, 0.05),
        ("Arpa Posası",              53.2,  11.0,   53.2,   0.28, 0.5),
        ("Arpa",                     21.2,  61.45,  None,   0.05, 0.29),
        ("Mısır",                    10.5,  77.4,   None,   0.03, 0.23),
        ("Arpa flake",               21.2,  61.45,  None,   0.05, 0.29),
        ("Mısır flake",              10.5,  77.4,   None,   0.03, 0.23),
        ("Buğday",                   13.7,  70.0,   None,   0.04, 0.26),
        ("Razmol",                   35.5,  42.5,   None,   0.14, 0.98),
        ("Bonkalit",                 11.0,  72.4,   None,   0.1,  0.4),
        ("Pamuk Tohumu (çiğit)",     42.56, None,   None,   0.16, 0.63),
        ("Arpamiks",                 32.4,  26.4,   None,   3.68, 0.79),
        ("Ayçiçek Küspesi 26 prot",  45.9,  15.8,   None,   0.25, 0.76),
        ("Ayçiçek Küspesi 35 prot",  39.7,  13.5,   None,   0.25, 0.8),
        ("Pamuk Küspesi Exp 25 prot",46.5,  8.7,    None,   0.11, 0.7),
        ("Pamuk Küspesi 30 prot",    39.33, 15.3,   None,   0.15, 0.81),
        ("CSR CD BESİ",              19.91, 19.9,   7.8,    3.07, 0.8),
        ("SDF H",                    21.8,  24.77,  7.4,    0.43, 0.8),
        ("Soya küspesi",             9.8,   30.0,   None,   0.354,None),
    ]
    for name, ndf, nfc, endf, ca, p in _BACKFILL:
        if ndf is not None:
            conn.exec_driver_sql("UPDATE feeds SET ndf_pct=? WHERE name=? AND ndf_pct IS NULL",
                                 (ndf, name))
        if nfc is not None:
            conn.exec_driver_sql("UPDATE feeds SET nfc_pct=? WHERE name=? AND nfc_pct IS NULL",
                                 (nfc, name))
        if endf is not None:
            conn.exec_driver_sql("UPDATE feeds SET endf_pct=? WHERE name=? AND endf_pct IS NULL",
                                 (endf, name))
        if ca is not None:
            conn.exec_driver_sql("UPDATE feeds SET ca_pct=? WHERE name=? AND ca_pct IS NULL",
                                 (ca, name))
        if p is not None:
            conn.exec_driver_sql("UPDATE feeds SET p_pct=? WHERE name=? AND p_pct IS NULL",
                                 (p, name))


def _m006_add_new_users(conn) -> None:
    """Seed orkun.cosar (admin) and yagiz.cosar (user) if not already present."""
    from auth import hash_password as _hp
    new_users = [
        ("orkun.cosar",  "26051108Oc.19", True),
        ("yagiz.cosar",  "26051108Yc",    False),
    ]
    for username, password, is_admin in new_users:
        exists = conn.exec_driver_sql(
            "SELECT 1 FROM users WHERE username = ?", (username,)
        ).fetchone()
        if not exists:
            conn.exec_driver_sql(
                "INSERT INTO users (username, hashed_password, is_admin, created_at) "
                "VALUES (?, ?, ?, ?)",
                (username, _hp(password), is_admin, datetime.utcnow().isoformat()),
            )


_MIGRATIONS: list[tuple[str, callable]] = [
    ("001_add_customer_name_to_saved_rations",          _m001_add_customer_name_to_saved_rations),
    ("002_remove_obsolete_feeds_and_fix_csr_sdf",       _m002_remove_obsolete_feeds_and_fix_csr_sdf),
    ("003_add_ration_type_to_saved_rations",            _m003_add_ration_type_to_saved_rations),
    ("004_add_dairy_columns_and_seed_dairy_feeds",      _m004_add_dairy_columns_and_seed_dairy_feeds),
    ("005_add_nfc_endf_cost_and_backfill",              _m005_add_nfc_endf_cost_and_backfill),
    ("006_add_new_users",                               _m006_add_new_users),
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
                    ndf_pct=f.get("ndf_pct"), nfc_pct=f.get("nfc_pct"),
                    endf_pct=f.get("endf_pct"), ca_pct=f.get("ca_pct"),
                    p_pct=f.get("p_pct"),
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
                    ndf_pct=f.get("ndf_pct"), nfc_pct=f.get("nfc_pct"),
                    endf_pct=f.get("endf_pct"), ca_pct=f.get("ca_pct"),
                    p_pct=f.get("p_pct"), note=f.get("note"),
                ))
            db.add_all(all_seeds)
            db.commit()
