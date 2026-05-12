"""FastAPI app for the CSR Rasyon Hesaplayıcı."""

import io
import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
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

# ── PDF font setup (runs once at import time) ────────────────────────────────
_PDF_FONT       = "Helvetica"
_PDF_FONT_BOLD  = "Helvetica-Bold"
_PDF_UNICODE    = False
_PDF_LOADED     = False
_TR_TAB = str.maketrans("ğüşıöçĞÜŞİÖÇ", "gusiocGUSIOC")

try:
    from reportlab.pdfbase import pdfmetrics as _pm
    from reportlab.pdfbase.ttfonts import TTFont as _TTFont
    _PDF_LOADED = True
    for _r, _b in [
        ("/Library/Fonts/Arial.ttf",                                          "/Library/Fonts/Arial Bold.ttf"),
        ("/System/Library/Fonts/Supplemental/Arial.ttf",                      "/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",                   "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ("/usr/share/fonts/dejavu/DejaVuSans.ttf",                            "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"),
    ]:
        if _r and Path(_r).exists():
            try:
                _pm.registerFont(_TTFont("_PDFFont", _r))
                _PDF_FONT = "_PDFFont"
                if _b and Path(_b).exists():
                    _pm.registerFont(_TTFont("_PDFFontBold", _b))
                    _PDF_FONT_BOLD = "_PDFFontBold"
                else:
                    _PDF_FONT_BOLD = "_PDFFont"
                _PDF_UNICODE = True
                break
            except Exception:
                pass
except ImportError:
    pass


def _ptxt(s) -> str:
    """Return PDF-safe string — Unicode if a TTF font is registered, else ASCII-transliterated."""
    if s is None:
        return ""
    s = str(s)
    return s if _PDF_UNICODE else s.translate(_TR_TAB)


def _pfmt(n, decimals: int = 2) -> str:
    if n is None:
        return "–"
    try:
        return f"{float(n):.{decimals}f}"
    except Exception:
        return str(n)


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
    calc_mode: str = "actual"  # "actual" | "scaled"


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


class ReportRequest(BaseModel):
    ration_type: str = "besi"
    customer_name: Optional[str] = None
    herd_name: Optional[str] = None
    live_weight: float
    target_gain: Optional[float] = None
    breed: Optional[str] = None
    ration: List[dict]
    results: dict


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
            calc_mode=req.calc_mode,
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


# --- PDF Report ---

@app.post("/api/report/pdf")
def generate_pdf_report(
    req: ReportRequest,
    user: User = Depends(get_current_user),
):
    if not _PDF_LOADED:
        raise HTTPException(
            status_code=501,
            detail="PDF özelliği için 'reportlab' paketi gereklidir. pip install reportlab",
        )

    from datetime import datetime

    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        Image,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    buf = io.BytesIO()
    logo_path = STATIC_DIR / "csr-logo.png"

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    F  = _PDF_FONT
    FB = _PDF_FONT_BOLD
    navy      = colors.HexColor("#1e3a73")
    green     = colors.HexColor("#14803c")
    light_bg  = colors.HexColor("#f8fafd")
    row_alt   = colors.HexColor("#eef2f9")
    border_c  = colors.HexColor("#d8dee8")

    _align_map = {"LEFT": TA_LEFT, "CENTER": TA_CENTER, "RIGHT": TA_RIGHT}

    def P(text, size=10, bold=False, color=colors.black, align="LEFT"):
        style = ParagraphStyle(
            "s",
            fontName=FB if bold else F,
            fontSize=size,
            textColor=color,
            alignment=_align_map.get(align, TA_LEFT),
            spaceAfter=2,
            leading=size * 1.3,
        )
        return Paragraph(_ptxt(str(text)) if text is not None else "", style)

    story = []

    # ── Header ────────────────────────────────────────────────────────────────
    logo_cell: object = ""
    if logo_path.exists():
        try:
            logo_cell = Image(str(logo_path), width=1.2 * cm, height=1.2 * cm)
        except Exception:
            pass

    hdr_table = Table(
        [[logo_cell, P("CSR Rasyon Hesaplayici", 16, bold=True, color=navy)]],
        colWidths=[1.5 * cm, None],
    )
    hdr_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(hdr_table)

    mode_str = "Sut Rasyonu Raporu" if req.ration_type == "sut" else "Besi Rasyonu Raporu"
    story.append(P(mode_str, 13, bold=True, color=navy))
    story.append(P(
        f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}  |  Hazirlayan: {user.username}",
        9, color=colors.grey,
    ))
    story.append(Spacer(1, 0.3 * cm))

    # ── Customer info ─────────────────────────────────────────────────────────
    info_rows: list = []
    if req.customer_name:
        info_rows.append([P("Musteri / Isletme:", 9, bold=True), P(req.customer_name, 10)])
    if req.herd_name:
        info_rows.append([P("Suru / Not:", 9, bold=True), P(req.herd_name, 10)])
    info_rows.append([P("Canli Agirlik:", 9, bold=True), P(f"{req.live_weight:.0f} kg", 10)])
    if req.breed:
        info_rows.append([P("Irk:", 9, bold=True), P(req.breed, 10)])
    if req.target_gain:
        info_rows.append([P("Hedef CA Artisi:", 9, bold=True), P(f"{req.target_gain:.0f} g/gun", 10)])

    info_t = Table(info_rows, colWidths=[4 * cm, None])
    info_t.setStyle(TableStyle([
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(info_t)
    story.append(Spacer(1, 0.35 * cm))

    # ── Ration table ──────────────────────────────────────────────────────────
    story.append(P("Rasyon Bilesimi", 11, bold=True, color=navy))
    story.append(Spacer(1, 0.12 * cm))

    rows_data = req.results.get("rows", [])
    page_w = A4[0] - 3 * cm
    name_w = 4.5 * cm

    if req.ration_type == "sut":
        ration_cols = ["Yem", "Yas (kg)", "KM (kg)", "UFL", "PDI (g)", "HP (g)", "NDF (g)", "Maliyet (TL)"]
        n_other = len(ration_cols) - 1
        col_widths = [name_w] + [(page_w - name_w) / n_other] * n_other
        def _row_sut(r):
            ndf = _pfmt(r.get("ndf_g"), 0) if r.get("ndf_g") is not None else "–"
            cost = _pfmt(r.get("cost_tl"), 2) if r.get("cost_tl") is not None else "–"
            return [
                P(r.get("name", ""), 9),
                P(_pfmt(r.get("as_fed_kg"), 2), 9, align="RIGHT"),
                P(_pfmt(r.get("dm_kg"), 2), 9, align="RIGHT"),
                P(_pfmt(r.get("ufl"), 2), 9, align="RIGHT"),
                P(_pfmt(r.get("pdi_g"), 0), 9, align="RIGHT"),
                P(_pfmt(r.get("hp_g"), 0), 9, align="RIGHT"),
                P(ndf, 9, align="RIGHT"),
                P(cost, 9, align="RIGHT"),
            ]
        ration_body = [_row_sut(r) for r in rows_data]
    else:
        ration_cols = ["Yem", "Yas (kg)", "KM (kg)", "UFV", "PDIE", "Protein (kg)", "Maliyet (TL)"]
        n_other = len(ration_cols) - 1
        col_widths = [name_w] + [(page_w - name_w) / n_other] * n_other
        def _row_besi(r):
            cost = _pfmt(r.get("cost_tl"), 2) if r.get("cost_tl") is not None else "–"
            return [
                P(r.get("name", ""), 9),
                P(_pfmt(r.get("as_fed_kg"), 2), 9, align="RIGHT"),
                P(_pfmt(r.get("dm_kg"), 2), 9, align="RIGHT"),
                P(_pfmt(r.get("ufv"), 2), 9, align="RIGHT"),
                P(_pfmt(r.get("pdie"), 0), 9, align="RIGHT"),
                P(_pfmt(r.get("protein_kg"), 2), 9, align="RIGHT"),
                P(cost, 9, align="RIGHT"),
            ]
        ration_body = [_row_besi(r) for r in rows_data]

    thead_row = [P(h, 8, bold=True) for h in ration_cols]
    rat_table = Table([thead_row] + ration_body, colWidths=col_widths, repeatRows=1)
    rat_table.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0),  navy),
        ("TEXTCOLOR",      (0, 0), (-1, 0),  colors.white),
        ("TOPPADDING",     (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [light_bg, colors.white]),
        ("GRID",           (0, 0), (-1, -1), 0.4, border_c),
        ("ALIGN",          (1, 0), (-1, -1), "RIGHT"),
    ]))
    story.append(rat_table)
    story.append(Spacer(1, 0.4 * cm))

    # ── TMR Summary ───────────────────────────────────────────────────────────
    story.append(P("TMR Ozeti", 11, bold=True, color=navy))
    story.append(Spacer(1, 0.12 * cm))
    t = req.results.get("tmr_summary", {})

    if req.ration_type == "sut":
        summary_items = [
            ("Toplam Yas Madde",  f"{_pfmt(t.get('total_as_fed_kg'), 2)} kg/gun"),
            ("Toplam Kuru Madde", f"{_pfmt(t.get('total_dm_kg'), 2)} kg/gun"),
            ("Rasyon KM%",        f"{_pfmt(t.get('ration_dm_pct'), 1)} %"),
            ("UFL / kg KM",       _pfmt(t.get("ufl_per_kg_dm"), 3)),
            ("PDI / kg KM",       f"{_pfmt(t.get('pdi_per_kg_dm'), 1)} g/kg KM"),
            ("HP (KM)",           f"{_pfmt(t.get('hp_pct_dm'), 1)} %"),
        ]
        if t.get("ndf_pct_dm") is not None:
            summary_items.append(("NDF (KM)", f"{_pfmt(t.get('ndf_pct_dm'), 1)} %"))
        if t.get("nfc_pct_dm") is not None:
            summary_items.append(("NFC (KM)", f"{_pfmt(t.get('nfc_pct_dm'), 1)} %"))
        if (t.get("total_cost_tl") or 0) > 0:
            summary_items += [
                ("Rasyon Maliyeti",   f"{_pfmt(t.get('total_cost_tl'), 2)} TL/gun"),
                ("Maliyet / kg KM",   f"{_pfmt(t.get('cost_per_kg_dm'), 2)} TL/kg"),
            ]
            if t.get("cost_per_liter_milk") is not None:
                summary_items.append(("Maliyet / Lt Sut", f"{_pfmt(t.get('cost_per_liter_milk'), 2)} TL/lt"))
    else:
        summary_items = [
            ("Toplam Yas Madde",  f"{_pfmt(t.get('total_as_fed_kg'), 2)} kg/gun"),
            ("Toplam Kuru Madde", f"{_pfmt(t.get('total_dm_kg'), 2)} kg/gun"),
            ("Rasyon KM%",        f"{_pfmt(t.get('ration_dm_pct'), 1)} %"),
            ("UFV / kg KM",       _pfmt(t.get("ufv_per_kg_dm"), 2)),
            ("Protein (KM)",      f"{_pfmt(t.get('protein_pct_dm'), 1)} %"),
            ("Nisasta (KM)",      f"{_pfmt(t.get('starch_pct_dm'), 1)} %"),
        ]
        if t.get("ndf_pct_dm") is not None:
            summary_items.append(("NDF (KM)", f"{_pfmt(t.get('ndf_pct_dm'), 1)} %"))
        if t.get("nfc_pct_dm") is not None:
            summary_items.append(("NFC (KM)", f"{_pfmt(t.get('nfc_pct_dm'), 1)} %"))
        if (t.get("total_cost_tl") or 0) > 0:
            summary_items += [
                ("Rasyon Maliyeti", f"{_pfmt(t.get('total_cost_tl'), 2)} TL/gun"),
                ("Maliyet / kg KM", f"{_pfmt(t.get('cost_per_kg_dm'), 2)} TL/kg"),
            ]

    # Render summary as 2-column layout
    half_w = (page_w) / 2
    sum_rows = []
    for i in range(0, len(summary_items), 2):
        row: list = []
        for j in range(2):
            if i + j < len(summary_items):
                k, v = summary_items[i + j]
                row += [P(k + ":", 9, bold=True), P(v, 9)]
            else:
                row += [P(""), P("")]
        sum_rows.append(row)
    sum_table = Table(sum_rows, colWidths=[3.5 * cm, half_w - 3.5 * cm, 3.5 * cm, half_w - 3.5 * cm])
    sum_table.setStyle(TableStyle([
        ("TOPPADDING",     (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [light_bg, colors.white]),
    ]))
    story.append(sum_table)
    story.append(Spacer(1, 0.4 * cm))

    # ── Performance / Milk ────────────────────────────────────────────────────
    if req.ration_type == "sut":
        m = req.results.get("milk_estimate", {})
        story.append(P("Sut Miktari Tahmini", 11, bold=True, color=navy))
        story.append(Spacer(1, 0.12 * cm))
        perf_rows = [
            [P("Enerji Bazli Tahmini Sut:",   9, bold=True), P(f"{_pfmt(m.get('milk_by_energy_L'), 1)} L/gun", 10)],
            [P("Protein Bazli Tahmini Sut:",  9, bold=True), P(f"{_pfmt(m.get('milk_by_pdi_L'), 1)} L/gun", 10)],
            [P("Tahmini Gunluk Sut Uretimi:", 9, bold=True), P(f"{_pfmt(m.get('predicted_milk_L'), 1)} L/gun", 13, bold=True, color=green)],
            [P("Sinirlatici Faktor:",         9, bold=True), P(_ptxt(m.get("limit_factor", "")), 10)],
        ]
    else:
        p = req.results.get("expected_performance", {})
        story.append(P("Beklenen Performans", 11, bold=True, color=navy))
        story.append(Spacer(1, 0.12 * cm))
        perf_rows = [
            [P("Tahmini CA Artisi:",        9, bold=True), P(f"{_pfmt(p.get('estimated_gain_g'), 0)} g/gun", 13, bold=True, color=green)],
            [P("Sinirlatici besin ogesi:",  9, bold=True), P(_ptxt(p.get("bottleneck", "")), 10)],
            [P("UFV-bazli tahmin:",         9, bold=True), P(f"{_pfmt(p.get('gain_ufv_limited_g'), 0)} g/gun", 10)],
            [P("PDI-bazli tahmin:",         9, bold=True), P(f"{_pfmt(p.get('gain_pdi_limited_g'), 0)} g/gun", 10)],
        ]

    perf_table = Table(perf_rows, colWidths=[4.5 * cm, None])
    perf_table.setStyle(TableStyle([
        ("TOPPADDING",     (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [light_bg, colors.white]),
    ]))
    story.append(perf_table)

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.6 * cm))
    story.append(P(
        "Bu rapor CSR Rasyon Hesaplayici tarafindan otomatik olarak olusturulmustur.",
        8, color=colors.grey, align="CENTER",
    ))

    doc.build(story)
    buf.seek(0)

    safe_name = (req.customer_name or "rasyon").replace(" ", "_")[:20]
    filename = f"rasyon_{req.ration_type}_{safe_name}.pdf"

    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
