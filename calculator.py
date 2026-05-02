"""Pure calculation functions for TMR rations and INRA performance estimation."""

from typing import Optional

from data import (
    DMI_FALLBACK_PCT,
    DMI_TABLE,
    FEEDS_BY_NAME,
    GAIN_COLS,
    PDI_MATRIX,
    UFV_MATRIX,
    WEIGHT_ROWS,
)


class CalculationError(Exception):
    pass


def lookup_dmi_pct(live_weight: float) -> float:
    for max_w, pct in DMI_TABLE:
        if live_weight <= max_w:
            return pct
    return DMI_FALLBACK_PCT


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
    row = _row_at_weight(matrix, live_weight)
    gains = GAIN_COLS
    values = [row[g] for g in gains]

    if provided <= values[0]:
        return float(gains[0])
    if provided >= values[-1]:
        return float(gains[-1])

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


def calculate(
    live_weight: float,
    ration: list[dict],
    target_gain: Optional[float] = None,
    breed: Optional[str] = None,
    feeds_by_name: Optional[dict] = None,
) -> dict:
    if live_weight <= 0:
        raise CalculationError("Canlı ağırlık 0'dan büyük olmalı.")

    feed_lookup = feeds_by_name if feeds_by_name is not None else FEEDS_BY_NAME

    rows = []
    total_as_fed = 0.0
    total_dm = 0.0
    total_ufv = 0.0
    total_pdie = 0.0
    total_pdin = 0.0
    total_protein_kg = 0.0
    total_starch_kg = 0.0
    total_ndf_kg = 0.0
    total_nfc_kg = 0.0
    total_endf_kg = 0.0
    total_ca_kg = 0.0
    total_p_kg = 0.0
    total_cost_tl = 0.0
    has_ndf = has_nfc = has_endf = has_ca = has_p = False

    for item in ration:
        name = item.get("feed_name")
        as_fed = float(item.get("as_fed_kg") or 0)
        if not name or as_fed <= 0:
            continue
        feed = feed_lookup.get(name)
        if not feed:
            raise CalculationError(f"Bilinmeyen yem: {name}")

        dm_kg = as_fed * (feed["dm_pct"] / 100.0)
        ufv = dm_kg * (feed["ufv"] or 0)
        pdie = dm_kg * (feed["pdie"] or 0)
        pdin = dm_kg * (feed["pdin"] or 0)
        protein_kg = dm_kg * (feed["protein"] / 100.0)
        starch_kg = dm_kg * ((feed.get("starch") or 0) / 100.0)

        ndf = feed.get("ndf_pct")
        nfc = feed.get("nfc_pct")
        endf = feed.get("endf_pct")
        ca = feed.get("ca_pct")
        p = feed.get("p_pct")
        # Use item-level ton_maliyeti (from UI) if provided, else fall back to DB value
        ton_mal = item.get("ton_maliyeti") if item.get("ton_maliyeti") is not None else feed.get("ton_maliyeti")

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
            "name": name,
            "as_fed_kg":  round(as_fed, 3),
            "dm_kg":      round(dm_kg, 3),
            "ufv":        round(ufv, 3),
            "pdie":       round(pdie, 1),
            "pdin":       round(pdin, 1),
            "protein_kg": round(protein_kg, 3),
            "cost_tl":    round(row_cost, 2) if row_cost is not None else None,
        })

        total_as_fed    += as_fed
        total_dm        += dm_kg
        total_ufv       += ufv
        total_pdie      += pdie
        total_pdin      += pdin
        total_protein_kg += protein_kg
        total_starch_kg += starch_kg

    if total_dm <= 0:
        raise CalculationError(
            "Rasyona en az bir yem (kg > 0) ekleyin. Toplam kuru madde 0."
        )

    ufv_per_kg_dm    = total_ufv / total_dm
    pdie_per_kg_dm   = total_pdie / total_dm
    tmr_protein_pct  = (total_protein_kg / total_dm) * 100.0
    tmr_starch_pct   = (total_starch_kg  / total_dm) * 100.0
    ration_dm_pct    = (total_dm / total_as_fed) * 100.0 if total_as_fed > 0 else 0.0
    ndf_pct_dm       = (total_ndf_kg  / total_dm) * 100.0 if has_ndf  else None
    nfc_pct_dm       = (total_nfc_kg  / total_dm) * 100.0 if has_nfc  else None
    endf_pct_dm      = (total_endf_kg / total_dm) * 100.0 if has_endf else None
    ca_pct_dm        = (total_ca_kg   / total_dm) * 100.0 if has_ca   else None
    p_pct_dm         = (total_p_kg    / total_dm) * 100.0 if has_p    else None
    cost_per_kg_dm   = total_cost_tl / total_dm if total_cost_tl > 0 else 0.0

    dmi_pct = lookup_dmi_pct(live_weight)
    expected_dmi_kg = live_weight * (dmi_pct / 100.0)

    ration_ufv_total  = ufv_per_kg_dm  * expected_dmi_kg
    ration_pdie_total = pdie_per_kg_dm * expected_dmi_kg

    gain_ufv = estimate_gain_from_provided(UFV_MATRIX, live_weight, ration_ufv_total)
    gain_pdi = estimate_gain_from_provided(PDI_MATRIX, live_weight, ration_pdie_total)

    final_gain = min(gain_ufv, gain_pdi)
    bottleneck = "UFV" if gain_ufv <= gain_pdi else "PDI"

    result = {
        "breed": breed,
        "live_weight": live_weight,
        "target_gain": target_gain,
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
            "total_cost_tl":    round(total_cost_tl, 2),
            "cost_per_kg_dm":   round(cost_per_kg_dm, 2),
        },
        "expected_performance": {
            "dmi_pct_bw":               round(dmi_pct, 1),
            "expected_dmi_kg":          round(expected_dmi_kg, 2),
            "ration_ufv_total_at_dmi":  round(ration_ufv_total, 2),
            "ration_pdie_total_at_dmi_g": round(ration_pdie_total, 0),
            "gain_ufv_limited_g":       int(round(gain_ufv / 10.0) * 10),
            "gain_pdi_limited_g":       int(round(gain_pdi / 10.0) * 10),
            "estimated_gain_g":         int(round(final_gain / 10.0) * 10),
            "bottleneck":               bottleneck,
        },
        "rows": rows,
    }

    if target_gain:
        ufv_required = required_at(UFV_MATRIX, live_weight, target_gain)
        pdi_required = required_at(PDI_MATRIX, live_weight, target_gain)
        result["inra_comparison"] = {
            "target_gain_g":   target_gain,
            "ufv_required":    round(ufv_required, 2),
            "ufv_provided":    round(ration_ufv_total, 2),
            "ufv_met":         ration_ufv_total >= ufv_required,
            "pdi_required_g":  round(pdi_required, 0),
            "pdi_provided_g":  round(ration_pdie_total, 0),
            "pdi_met":         ration_pdie_total >= pdi_required,
        }

    return result
