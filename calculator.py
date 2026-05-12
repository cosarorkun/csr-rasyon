"""Pure calculation functions for TMR rations and INRA performance estimation.

calc_mode options
-----------------
"actual"  (default) — use the *real* kg/day entered by the user.
          Gain is estimated from total_ufv and min(total_pdie, total_pdin).
          This is the correct field-use mode.

"scaled"  (legacy)  — multiply nutrient density (UFV or PDIE per kg DM) by the
          breed-table expected DMI, then estimate gain from that scaled supply.
          Useful for evaluating whether a ration *formulation* is adequate at
          target intake, regardless of what the user typed.
"""

from typing import Optional

from data import (
    DMI_ANCHORS,
    DMI_FALLBACK_PCT,
    FEEDS_BY_NAME,
    GAIN_COLS,
    PDI_MATRIX,
    UFV_MATRIX,
    WEIGHT_ROWS,
)


class CalculationError(Exception):
    pass


# ── DMI lookup (linear interpolation) ─────────────────────────────────────────

def lookup_dmi_pct(live_weight: float) -> float:
    """Return expected DMI as % of BW, interpolated from DMI_ANCHORS."""
    anchors = DMI_ANCHORS
    if live_weight <= anchors[0][0]:
        return anchors[0][1]
    if live_weight >= anchors[-1][0]:
        return DMI_FALLBACK_PCT
    for i in range(len(anchors) - 1):
        w0, p0 = anchors[i]
        w1, p1 = anchors[i + 1]
        if w0 <= live_weight <= w1:
            return p0 + (live_weight - w0) * (p1 - p0) / (w1 - w0)
    return DMI_FALLBACK_PCT


# ── Matrix helpers ─────────────────────────────────────────────────────────────

def _interp(x: float, x0: float, x1: float, y0: float, y1: float) -> float:
    if x1 == x0:
        return y0
    return y0 + (x - x0) * (y1 - y0) / (x1 - x0)


def _bracket(value: float, sorted_keys: list[int]) -> tuple[int, int]:
    if value <= sorted_keys[0]:
        return sorted_keys[0], sorted_keys[0]
    if value >= sorted_keys[-1]:
        return sorted_keys[-1], sorted_keys[-1]
    for i in range(len(sorted_keys) - 1):
        if sorted_keys[i] <= value <= sorted_keys[i + 1]:
            return sorted_keys[i], sorted_keys[i + 1]
    return sorted_keys[-1], sorted_keys[-1]


def _row_at_weight(matrix: dict, live_weight: float) -> dict[int, float]:
    w0, w1 = _bracket(live_weight, WEIGHT_ROWS)
    if w0 == w1:
        return dict(matrix[w0])
    return {
        g: _interp(live_weight, w0, w1, matrix[w0][g], matrix[w1][g])
        for g in GAIN_COLS
    }


def estimate_gain_from_provided(
    matrix: dict, live_weight: float, provided: float
) -> float:
    """Inverse-lookup: given actual nutrient supply, return estimated gain (g/day).

    Below the table minimum (gains[0] = 800 g/day), the gain is linearly
    extrapolated downward and clamped at 0 — NOT floored at 800 as the old code
    did. This prevents 1 kg of barley from reporting 800 g/day gain for a 400 kg
    animal.
    """
    row = _row_at_weight(matrix, live_weight)
    gains = GAIN_COLS
    values = [row[g] for g in gains]

    # Below minimum — extrapolate toward 0
    if provided <= values[0]:
        v_min = values[0]
        v_next = values[1] if len(values) > 1 else v_min
        g_min = gains[0]
        g_next = gains[1] if len(gains) > 1 else g_min
        if v_next == v_min:
            return max(0.0, float(g_min) * provided / v_min) if v_min > 0 else 0.0
        # Linear extrapolation from (v_min, g_min) toward 0
        slope = (g_next - g_min) / (v_next - v_min)
        extrapolated = g_min + slope * (provided - v_min)
        return max(0.0, extrapolated)

    # Above maximum — cap at top gain
    if provided >= values[-1]:
        return float(gains[-1])

    # Normal interpolation
    for i in range(len(gains) - 1):
        v0, v1 = values[i], values[i + 1]
        if v0 <= provided <= v1:
            return _interp(provided, v0, v1, gains[i], gains[i + 1])
    return float(gains[-1])


def required_at(matrix: dict, live_weight: float, target_gain: float) -> float:
    w0, w1 = _bracket(live_weight, WEIGHT_ROWS)
    g0, g1 = _bracket(target_gain, GAIN_COLS)

    v00 = matrix[w0][g0]
    v01 = matrix[w0][g1]
    v10 = matrix[w1][g0]
    v11 = matrix[w1][g1]

    a = _interp(target_gain, g0, g1, v00, v01) if g0 != g1 else v00
    b = _interp(target_gain, g0, g1, v10, v11) if g0 != g1 else v10
    return _interp(live_weight, w0, w1, a, b) if w0 != w1 else a


# ── Main calculate function ────────────────────────────────────────────────────

def calculate(
    live_weight: float,
    ration: list[dict],
    target_gain: Optional[float] = None,
    breed: Optional[str] = None,
    feeds_by_name: Optional[dict] = None,
    calc_mode: str = "actual",
) -> dict:
    """Calculate TMR summary and INRA performance estimate.

    Parameters
    ----------
    calc_mode : "actual" (default) | "scaled"
        "actual"  — gain estimated from nutrients the user *actually entered*.
        "scaled"  — gain estimated after scaling nutrient density by expected DMI
                    (legacy behaviour; useful for formulation checks).
    """
    if live_weight <= 0:
        raise CalculationError("Canlı ağırlık 0'dan büyük olmalı.")

    feed_lookup = feeds_by_name if feeds_by_name is not None else FEEDS_BY_NAME

    rows = []
    total_as_fed     = 0.0
    total_dm         = 0.0
    total_ufv        = 0.0
    total_pdie       = 0.0
    total_pdin       = 0.0
    total_protein_kg = 0.0
    total_starch_kg  = 0.0
    total_ndf_kg     = 0.0
    total_nfc_kg     = 0.0
    total_endf_kg    = 0.0
    total_ca_kg      = 0.0
    total_p_kg       = 0.0
    total_cost_tl    = 0.0
    has_ndf = has_nfc = has_endf = has_ca = has_p = False

    # Track whether any feed is missing PDIN (= 0 AND protein > 0 — likely a
    # data gap rather than a genuinely nitrogen-free ingredient like pure fat).
    feeds_missing_pdin: list[str] = []

    for item in ration:
        name   = item.get("feed_name")
        as_fed = float(item.get("as_fed_kg") or 0)
        if not name or as_fed <= 0:
            continue
        feed = feed_lookup.get(name)
        if not feed:
            raise CalculationError(f"Bilinmeyen yem: {name}")

        dm_kg      = as_fed * (feed["dm_pct"] / 100.0)
        ufv        = dm_kg * (feed["ufv"] or 0)
        pdie       = dm_kg * (feed["pdie"] or 0)
        pdin_val   = feed.get("pdin")
        pdin       = dm_kg * (pdin_val or 0)
        protein_kg = dm_kg * (feed["protein"] / 100.0)
        starch_kg  = dm_kg * ((feed.get("starch") or 0) / 100.0)

        # Flag feeds where PDIN is 0 but protein is non-negligible
        if (pdin_val is None or pdin_val == 0) and feed["protein"] > 5:
            feeds_missing_pdin.append(name)

        ndf  = feed.get("ndf_pct")
        nfc  = feed.get("nfc_pct")
        endf = feed.get("endf_pct")
        ca   = feed.get("ca_pct")
        p    = feed.get("p_pct")
        ton_mal  = (
            item.get("ton_maliyeti")
            if item.get("ton_maliyeti") is not None
            else feed.get("ton_maliyeti")
        )

        ndf_kg  = dm_kg * (ndf  / 100.0) if ndf  is not None else None
        nfc_kg  = dm_kg * (nfc  / 100.0) if nfc  is not None else None
        endf_kg = dm_kg * (endf / 100.0) if endf is not None else None
        ca_kg   = dm_kg * (ca   / 100.0) if ca   is not None else None
        p_kg    = dm_kg * (p    / 100.0) if p    is not None else None
        row_cost = (as_fed / 1000.0) * ton_mal if ton_mal is not None else None

        if ndf_kg  is not None: total_ndf_kg  += ndf_kg;  has_ndf  = True
        if nfc_kg  is not None: total_nfc_kg  += nfc_kg;  has_nfc  = True
        if endf_kg is not None: total_endf_kg += endf_kg; has_endf = True
        if ca_kg   is not None: total_ca_kg   += ca_kg;   has_ca   = True
        if p_kg    is not None: total_p_kg    += p_kg;    has_p    = True
        if row_cost is not None: total_cost_tl += row_cost

        rows.append({
            "name":       name,
            "as_fed_kg":  round(as_fed, 3),
            "dm_kg":      round(dm_kg, 3),
            "ufv":        round(ufv, 3),
            "pdie":       round(pdie, 1),
            "pdin":       round(pdin, 1),
            "protein_kg": round(protein_kg, 3),
            "cost_tl":    round(row_cost, 2) if row_cost is not None else None,
        })

        total_as_fed     += as_fed
        total_dm         += dm_kg
        total_ufv        += ufv
        total_pdie       += pdie
        total_pdin       += pdin
        total_protein_kg += protein_kg
        total_starch_kg  += starch_kg

    if total_dm <= 0:
        raise CalculationError(
            "Rasyona en az bir yem (kg > 0) ekleyin. Toplam kuru madde 0."
        )

    # ── Derived ratios ────────────────────────────────────────────────────────
    ufv_per_kg_dm   = total_ufv  / total_dm
    pdie_per_kg_dm  = total_pdie / total_dm
    tmr_protein_pct = (total_protein_kg / total_dm) * 100.0
    tmr_starch_pct  = (total_starch_kg  / total_dm) * 100.0
    ration_dm_pct   = (total_dm / total_as_fed) * 100.0 if total_as_fed > 0 else 0.0
    ndf_pct_dm      = (total_ndf_kg  / total_dm) * 100.0 if has_ndf  else None
    nfc_pct_dm      = (total_nfc_kg  / total_dm) * 100.0 if has_nfc  else None
    endf_pct_dm     = (total_endf_kg / total_dm) * 100.0 if has_endf else None
    ca_pct_dm       = (total_ca_kg   / total_dm) * 100.0 if has_ca   else None
    p_pct_dm        = (total_p_kg    / total_dm) * 100.0 if has_p    else None
    cost_per_kg_dm  = total_cost_tl / total_dm if total_cost_tl > 0 else 0.0

    # PDI supply = min(PDIE, PDIN)  — the actual bottleneck nutrient
    pdi_supply_g = min(total_pdie, total_pdin)

    # ── Expected DMI (reference only) ─────────────────────────────────────────
    dmi_pct          = lookup_dmi_pct(live_weight)
    expected_dmi_kg  = live_weight * (dmi_pct / 100.0)
    actual_dm_pct_bw = (total_dm / live_weight) * 100.0

    # ── Choose nutrient supply for gain estimation ────────────────────────────
    if calc_mode == "scaled":
        ufv_for_gain = ufv_per_kg_dm  * expected_dmi_kg
        pdi_for_gain = pdie_per_kg_dm * expected_dmi_kg
    else:  # "actual" (default)
        ufv_for_gain = total_ufv
        pdi_for_gain = pdi_supply_g

    gain_ufv = estimate_gain_from_provided(UFV_MATRIX, live_weight, ufv_for_gain)
    gain_pdi = estimate_gain_from_provided(PDI_MATRIX, live_weight, pdi_for_gain)

    final_gain = min(gain_ufv, gain_pdi)

    _BALANCE_THRESHOLD = 15  # g/day — gains within this are "Dengeli"
    if abs(gain_ufv - gain_pdi) <= _BALANCE_THRESHOLD:
        bottleneck = "Dengeli"
    elif gain_ufv <= gain_pdi:
        bottleneck = "ENERJİ (UFV)"
    else:
        bottleneck = "PROTEİN (PDI)"

    # ── Warnings ──────────────────────────────────────────────────────────────
    warnings: list[str] = []

    dmi_ratio = total_dm / expected_dmi_kg if expected_dmi_kg > 0 else 1.0
    if dmi_ratio < 0.80:
        warnings.append(
            f"Gerçek KM ({total_dm:.1f} kg) beklenen DMİ'nin "
            f"%{dmi_ratio*100:.0f}'i — rasyon eksik olabilir."
        )
    elif dmi_ratio > 1.20:
        warnings.append(
            f"Gerçek KM ({total_dm:.1f} kg) beklenen DMİ'nin "
            f"%{dmi_ratio*100:.0f}'i — rasyon aşırı olabilir."
        )

    if total_pdin < total_pdie * 0.85:
        warnings.append(
            "PDİN (azot sınırlı PDİ) enerji sınırlı PDİE'den belirgin şekilde "
            "düşük — protein dengesi gözden geçirin."
        )

    if feeds_missing_pdin:
        names_str = ", ".join(feeds_missing_pdin[:3])
        warnings.append(
            f"PDIN değeri eksik yem(ler): {names_str}. "
            "PDI arzı olduğundan düşük hesaplanmış olabilir."
        )

    breed_note = (
        "Irk seçimi bu INRA matrisinde besi performansını değiştirmez; "
        "kayıt/rapor amacıyla saklanır."
    ) if breed else None

    # ── Build result ──────────────────────────────────────────────────────────
    result = {
        "breed":       breed,
        "live_weight": live_weight,
        "target_gain": target_gain,
        "calc_mode":   calc_mode,
        "tmr_summary": {
            "total_as_fed_kg":  round(total_as_fed, 2),
            "total_dm_kg":      round(total_dm, 2),
            "ration_dm_pct":    round(ration_dm_pct, 1),
            "ufv_per_kg_dm":    round(ufv_per_kg_dm, 2),
            "pdie_per_kg_dm":   round(pdie_per_kg_dm, 1),
            "protein_pct_dm":   round(tmr_protein_pct, 1),
            "starch_pct_dm":    round(tmr_starch_pct, 1),
            "ndf_pct_dm":       round(ndf_pct_dm,  1) if ndf_pct_dm  is not None else None,
            "nfc_pct_dm":       round(nfc_pct_dm,  1) if nfc_pct_dm  is not None else None,
            "endf_pct_dm":      round(endf_pct_dm, 1) if endf_pct_dm is not None else None,
            "ca_pct_dm":        round(ca_pct_dm,   2) if ca_pct_dm   is not None else None,
            "p_pct_dm":         round(p_pct_dm,    2) if p_pct_dm    is not None else None,
            "total_ufv":        round(total_ufv, 2),
            "total_pdie_g":     round(total_pdie, 0),
            "total_pdin_g":     round(total_pdin, 0),
            "pdi_supply_g":     round(pdi_supply_g, 0),
            "total_cost_tl":    round(total_cost_tl, 2),
            "cost_per_kg_dm":   round(cost_per_kg_dm, 2),
        },
        "expected_performance": {
            "calc_mode":                  calc_mode,
            "dmi_pct_bw":                 round(dmi_pct, 1),
            "expected_dmi_kg":            round(expected_dmi_kg, 2),
            "actual_dm_pct_bw":           round(actual_dm_pct_bw, 2),
            # Actual nutrient totals (always shown regardless of mode)
            "ration_ufv_actual":          round(total_ufv, 2),
            "ration_pdie_actual_g":       round(total_pdie, 0),
            "ration_pdin_actual_g":       round(total_pdin, 0),
            "ration_pdi_supply_g":        round(pdi_supply_g, 0),
            # Nutrient values used for gain estimation
            "ufv_for_gain":               round(ufv_for_gain, 2),
            "pdi_for_gain_g":             round(pdi_for_gain, 0),
            # Gain estimates
            "gain_ufv_limited_g":         int(round(gain_ufv / 10.0) * 10),
            "gain_pdi_limited_g":         int(round(gain_pdi / 10.0) * 10),
            "estimated_gain_g":           int(round(final_gain / 10.0) * 10),
            "bottleneck":                 bottleneck,
            # Scaled values (always computed for reference, even in "actual" mode)
            "ration_ufv_total_at_dmi":    round(ufv_per_kg_dm  * expected_dmi_kg, 2),
            "ration_pdie_total_at_dmi_g": round(pdie_per_kg_dm * expected_dmi_kg, 0),
            "warnings":                   warnings,
            "breed_note":                 breed_note,
        },
        "rows": rows,
    }

    if target_gain:
        ufv_required = required_at(UFV_MATRIX, live_weight, target_gain)
        pdi_required = required_at(PDI_MATRIX, live_weight, target_gain)
        result["inra_comparison"] = {
            "target_gain_g":  target_gain,
            "ufv_required":   round(ufv_required, 2),
            "ufv_provided":   round(ufv_for_gain, 2),
            "ufv_met":        ufv_for_gain >= ufv_required,
            "pdi_required_g": round(pdi_required, 0),
            "pdi_provided_g": round(pdi_for_gain, 0),
            "pdi_met":        pdi_for_gain >= pdi_required,
        }

    return result
