"""FastAPI app for the CSR Rasyon Hesaplayıcı."""

import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from auth import (
    create_access_token,
    get_current_admin,
    get_current_user,
    verify_password,
)
from calculator import CalculationError, calculate
from dairy_calculator import DairyCalculationError, calculate_dairy
from data import BREEDS
from database import Feed, SavedRation, User, feed_to_dict, get_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="CSR Rasyon Hesaplayıcı", lifespan=lifespan)

STATIC_DIR = Path(__file__).parent / "static"


# --- Schemas ---

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    is_admin: bool
    username: str


class UserOut(BaseModel):
    username: str
    is_admin: bool


class RationItem(BaseModel):
    feed_name: str
    as_fed_kg: float = Field(ge=0)
    ton_maliyeti: Optional[float] = Field(default=None, ge=0)


class CalculateRequest(BaseModel):
    live_weight: float = Field(gt=0)
    target_gain: Optional[float] = Field(default=None, ge=0)
    breed: Optional[str] = None
    ration: List[RationItem]


class DairyCalculateRequest(BaseModel):
    live_weight: float = Field(gt=0)
    breed: Optional[str] = None
    ration: List[RationItem]


class SaveRationRequest(BaseModel):
    customer_name: Optional[str] = None
    herd_name: Optional[str] = None
    live_weight: float = Field(gt=0)
    target_gain: Optional[float] = Field(default=None, ge=0)
    breed: Optional[str] = None
    ration: List[dict]
    results: dict
    ration_type: str = "besi"


class FeedCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    dm_pct: float = Field(ge=0, le=100)
    ufv: float = Field(ge=0)
    protein: float = Field(ge=0)
    pdie: float = Field(ge=0)
    pdin: float = Field(ge=0)
    cf: float = Field(default=0, ge=0)
    fat: float = Field(default=0, ge=0)
    ash: float = Field(default=0, ge=0)
    starch: float = Field(default=0, ge=0)
    category: str = Field(default="besi")
    rdp_pct_of_cp: Optional[float] = Field(default=None, ge=0, le=100)
    rup_pct_of_cp: Optional[float] = Field(default=None, ge=0, le=100)
    pdi_g_per_kg_dm: Optional[float] = Field(default=None, ge=0)
    ufl_per_kg_dm: Optional[float] = Field(default=None, ge=0)
    ndf_pct: Optional[float] = Field(default=None, ge=0, le=100)
    nfc_pct: Optional[float] = Field(default=None, ge=0, le=100)
    endf_pct: Optional[float] = Field(default=None, ge=0, le=100)
    ca_pct: Optional[float] = Field(default=None, ge=0)
    p_pct: Optional[float] = Field(default=None, ge=0)
    ton_maliyeti: Optional[float] = Field(default=None, ge=0)
    note: Optional[str] = None


class UserCreateRequest(BaseModel):
    username: str = Field(min_length=2, max_length=60)
    password: str = Field(min_length=4)
    is_admin: bool = False


class UserUpdateRequest(BaseModel):
    password: Optional[str] = Field(default=None, min_length=4)
    is_admin: Optional[bool] = None


# --- Public routes ---

@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/auth/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if user is None or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=401, detail="Kullanıcı adı veya şifre hatalı."
        )
    token = create_access_token(user.username, user.is_admin)
    return TokenResponse(
        access_token=token, is_admin=user.is_admin, username=user.username
    )


@app.get("/auth/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return UserOut(username=user.username, is_admin=user.is_admin)


# --- Feeds ---

@app.get("/feeds")
def list_feeds(
    category: Optional[str] = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return feeds filtered by category.

    - category='besi'  → feeds where category='besi' OR 'common'
    - category='sut'   → feeds where category='sut'  OR 'common'
    - no category      → all feeds (used by admin table)
    """
    q = db.query(Feed)
    if category:
        q = q.filter(or_(Feed.category == category, Feed.category == "common"))
    feeds = q.order_by(Feed.name).all()
    return {
        "feeds": [feed_to_dict(f) for f in feeds],
        "breeds": BREEDS,
    }


@app.post("/feeds")
def add_feed(
    req: FeedCreateRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if db.query(Feed).filter(Feed.name == req.name).first():
        raise HTTPException(
            status_code=400, detail=f"'{req.name}' adlı yem zaten mevcut."
        )
    feed = Feed(**req.model_dump(), is_custom=True, created_by=admin.id)
    db.add(feed)
    db.commit()
    db.refresh(feed)
    return feed_to_dict(feed)


@app.put("/feeds/{feed_id}")
def update_feed(
    feed_id: int,
    req: FeedCreateRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    feed = db.query(Feed).filter(Feed.id == feed_id).first()
    if feed is None:
        raise HTTPException(status_code=404, detail="Yem bulunamadı.")
    if req.name != feed.name:
        clash = (
            db.query(Feed)
            .filter(Feed.name == req.name, Feed.id != feed_id)
            .first()
        )
        if clash:
            raise HTTPException(
                status_code=400, detail=f"'{req.name}' adlı yem zaten mevcut."
            )
    for k, v in req.model_dump().items():
        setattr(feed, k, v)
    db.commit()
    db.refresh(feed)
    return feed_to_dict(feed)


@app.delete("/feeds/{feed_id}")
def delete_feed(
    feed_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    feed = db.query(Feed).filter(Feed.id == feed_id).first()
    if feed is None:
        raise HTTPException(status_code=404, detail="Yem bulunamadı.")
    db.delete(feed)
    db.commit()
    return {"ok": True}


# --- Calculate (beef) ---

@app.post("/calculate")
def calculate_endpoint(
    req: CalculateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    feeds_by_name = {f.name: feed_to_dict(f) for f in db.query(Feed).all()}
    try:
        return calculate(
            live_weight=req.live_weight,
            ration=[item.model_dump() for item in req.ration],
            target_gain=req.target_gain,
            breed=req.breed,
            feeds_by_name=feeds_by_name,
        )
    except CalculationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# --- Calculate (dairy) ---

@app.post("/api/dairy/calculate")
def dairy_calculate_endpoint(
    req: DairyCalculateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    feeds_by_name = {f.name: feed_to_dict(f) for f in db.query(Feed).all()}
    try:
        return calculate_dairy(
            live_weight=req.live_weight,
            ration=[item.model_dump() for item in req.ration],
            feeds_by_name=feeds_by_name,
        )
    except DairyCalculationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# --- Saved rations ---

@app.post("/rations")
def save_ration(
    req: SaveRationRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    saved = SavedRation(
        user_id=user.id,
        customer_name=(req.customer_name or "").strip() or None,
        herd_name=(req.herd_name or "").strip() or None,
        live_weight=req.live_weight,
        target_gain=req.target_gain,
        breed=req.breed,
        ration_json=json.dumps(req.ration, ensure_ascii=False),
        results_json=json.dumps(req.results, ensure_ascii=False),
        ration_type=req.ration_type or "besi",
    )
    db.add(saved)
    db.commit()
    db.refresh(saved)
    return {"id": saved.id, "created_at": saved.created_at.isoformat()}


@app.get("/rations")
def list_rations(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(SavedRation, User.username).join(
        User, SavedRation.user_id == User.id
    )
    if not user.is_admin:
        q = q.filter(SavedRation.user_id == user.id)
    rows = q.order_by(SavedRation.created_at.desc()).all()
    out = []
    for r, username in rows:
        out.append({
            "id": r.id,
            "created_at": r.created_at.isoformat(),
            "customer_name": r.customer_name,
            "herd_name": r.herd_name,
            "live_weight": r.live_weight,
            "target_gain": r.target_gain,
            "breed": r.breed,
            "ration": json.loads(r.ration_json),
            "results": json.loads(r.results_json),
            "username": username,
            "owned": r.user_id == user.id,
            "ration_type": r.ration_type or "besi",
        })
    return {"rations": out}


@app.delete("/rations/{ration_id}")
def delete_ration(
    ration_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    r = db.query(SavedRation).filter(SavedRation.id == ration_id).first()
    if r is None:
        raise HTTPException(status_code=404, detail="Rasyon bulunamadı.")
    if not user.is_admin and r.user_id != user.id:
        raise HTTPException(
            status_code=403, detail="Bu rasyonu silme yetkiniz yok."
        )
    db.delete(r)
    db.commit()
    return {"ok": True}


# --- User management (admin only) ---

def _user_out(u: User) -> dict:
    return {
        "id": u.id,
        "username": u.username,
        "is_admin": u.is_admin,
        "created_at": u.created_at.isoformat(),
    }


@app.get("/users")
def list_users(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    users = db.query(User).order_by(User.created_at).all()
    return {"users": [_user_out(u) for u in users]}


@app.post("/users")
def add_user(
    req: UserCreateRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    from auth import hash_password
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(
            status_code=400, detail=f"'{req.username}' kullanıcı adı zaten mevcut."
        )
    user = User(
        username=req.username,
        hashed_password=hash_password(req.password),
        is_admin=req.is_admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _user_out(user)


@app.put("/users/{user_id}")
def update_user(
    user_id: int,
    req: UserUpdateRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    from auth import hash_password
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    if req.password is not None:
        user.hashed_password = hash_password(req.password)
    if req.is_admin is not None:
        user.is_admin = req.is_admin
    db.commit()
    db.refresh(user)
    return _user_out(user)


@app.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Kendi hesabınızı silemezsiniz.")
    # Prevent deleting the last admin
    if user.is_admin:
        admin_count = db.query(User).filter(User.is_admin == True).count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=400, detail="Son yönetici hesabı silinemez."
            )
    db.delete(user)
    db.commit()
    return {"ok": True}


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
