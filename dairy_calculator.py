"""Dairy (süt) ration calculator using the INRA UFL/PDI system.

Formulas (INRA 2018):
  maintenance_ufl  = 0.041 × BW^0.75
  maintenance_pdi  = 3.25  × BW^0.75   (g/day)
  milk_by_energy_L = (total_ufl − maint_ufl)  / UFL_PER_LITER
  milk_by_pdi_L    = (total_pdi − maint_pdi_g) / PDI_PER_LITER_G
  predicted_milk_L = min(milk_by_energy_L, milk_by_pdi_L)
"""

from typing import Optional

UFL_PER_LITER = 0.44      # UFL / L  (standard 4 % fat, 3.2 % protein milk)
PDI_PER_LITER_G = 48.0    # PDI g / L
MAINT_UFL_COEFF = 0.041   # UFL × kg BW^0.75
MAINT_PDI_COEFF = 3.25    # g PDI × kg BW^0.75


class DairyCalculationError(Exception):
    pass


def calculate_dairy(
    live_weight: float,
    ration: list[dict],
    feeds_by_name: Optional[dict] = None,
) -> dict:
    if live_weight <= 0:
        raise DairyCalculationError("Canlı ağırlık 0'dan büyük olmalı.")
    if feeds_by_name is None:
        raise DairyCalculationError("Yem veritabanı yüklenemedi.")

    rows = []
    total_as_fed   = 0.0
    total_dm       = 0.0
    total_ufl      = 0.0
    total_pdi_g    = 0.0
    total_hp_g     = 0.0
    total_ndf_g    = 0.0
    total_nfc_g    = 0.0
    total_endf_g   = 0.0
    total_ca_g     = 0.0
    total_p_g      = 0.0
    total_starch_g = 0.0
    total_cost_tl  = 0.0
    has_ndf = has_nfc = has_endf = has_ca = has_p = has_starch = False

    for item in ration:
        name = item.get("feed_name")
        as_fed = float(item.get("as_fed_kg") or 0)
        if not name or as_fed <= 0:
            continue

        feed = feeds_by_name.get(name)
        if not feed:
            raise DairyCalculationError(f"Bilinmeyen yem: {name}")

        dm_kg = as_fed * (feed["dm_pct"] / 100.0)
        ufl   = dm_kg * (feed.get("ufl_per_kg_dm") or feed.get("ufv") or 0.0)
        # Prefer pdi_g_per_kg_dm; fall back to pdie for common/besi feeds
        pdi_g = dm_kg * (feed.get("pdi_g_per_kg_dm") or feed.get("pdie") or 0.0)
        hp_g  = dm_kg * (feed["protein"] / 100.0) * 1000.0

        ndf   = feed.get("ndf_pct")
        nfc   = feed.get("nfc_pct")
        endf  = feed.get("endf_pct")
        ca    = feed.get("ca_pct")
        p     = feed.get("p_pct")
        starch = feed.get("starch") or 0.0

        ndf_g   = dm_kg * (ndf  / 100.0) * 1000.0 if ndf  is not None else None
        nfc_g   = dm_kg * (nfc  / 100.0) * 1000.0 if nfc  is not None else None
        endf_g  = dm_kg * (endf / 100.0) * 1000.0 if endf is not None else None
        ca_g    = dm_kg * (ca   / 100.0) * 1000.0 if ca   is not None else None
        p_g     = dm_kg * (p    / 100.0) * 1000.0 if p    is not None else None
        starch_g = dm_kg * (starch / 100.0)

        # Use item-level ton_maliyeti (from UI) if provided, else fall back to DB value
        ton_mal  = item.get("ton_maliyeti") if item.get("ton_maliyeti") is not None else feed.get("ton_maliyeti")
        row_cost = (as_fed / 1000.0) * ton_mal if ton_mal is not None else None

        if ndf_g   is not None: total_ndf_g   += ndf_g;   has_ndf   = True
        if nfc_g   is not None: total_nfc_g   += nfc_g;   has_nfc   = True
        if endf_g  is not None: total_endf_g  += endf_g;  has_endf  = True
        if ca_g    is not None: total_ca_g    += ca_g;    has_ca    = True
        if p_g     is not None: total_p_g     += p_g;     has_p     = True
        if starch > 0:          total_starch_g += starch_g; has_starch = True
        if row_cost is not None: total_cost_tl += row_cost

        rows.append({
            "name":      name,
            "as_fed_kg": round(as_fed, 3),
            "dm_kg":     round(dm_kg, 3),
            "ufl":       round(ufl, 3),
            "pdi_g":     round(pdi_g, 1),
            "hp_g":      round(hp_g, 1),
            "ndf_g":     round(ndf_g, 1)   if ndf_g   is not None else None,
            "cost_tl":   round(row_cost, 2) if row_cost is not None else None,
        })

        total_as_fed += as_fed
        total_dm     += dm_kg
        total_ufl    += ufl
        total_pdi_g  += pdi_g
        total_hp_g   += hp_g

    if total_dm <= 0:
        raise DairyCalculationError(
            "Rasyona en az bir yem (kg > 0) ekleyin. Toplam kuru madde 0."
        )

    mbw = live_weight ** 0.75
    maintenance_ufl   = MAINT_UFL_COEFF * mbw
    maintenance_pdi_g = MAINT_PDI_COEFF * mbw

    net_ufl   = max(0.0, total_ufl   - maintenance_ufl)
    net_pdi_g = max(0.0, total_pdi_g - maintenance_pdi_g)

    milk_by_energy_L = net_ufl   / UFL_PER_LITER
    milk_by_pdi_L    = net_pdi_g / PDI_PER_LITER_G
    predicted_milk_L = min(milk_by_energy_L, milk_by_pdi_L)
    limit_factor = "ENERJİ" if milk_by_energy_L <= milk_by_pdi_L else "PROTEİN"

    hp_pct_dm     = (total_hp_g    / 1000.0 / total_dm * 100.0) if total_dm > 0 else 0.0
    starch_pct_dm = (total_starch_g / total_dm * 100.0)          if has_starch and total_dm > 0 else None
    ndf_pct_dm    = (total_ndf_g   / 1000.0 / total_dm * 100.0) if has_ndf  else None
    nfc_pct_dm    = (total_nfc_g   / 1000.0 / total_dm * 100.0) if has_nfc  else None
    endf_pct_dm   = (total_endf_g  / 1000.0 / total_dm * 100.0) if has_endf else None
    ca_pct_dm     = (total_ca_g    / 1000.0 / total_dm * 100.0) if has_ca   else None
    p_pct_dm      = (total_p_g     / 1000.0 / total_dm * 100.0) if has_p    else None
    ration_dm_pct = (total_dm / total_as_fed * 100.0)            if total_as_fed > 0 else 0.0
    ufl_per_kg_dm = total_ufl   / total_dm if total_dm > 0 else 0.0
    pdi_per_kg_dm = total_pdi_g / total_dm if total_dm > 0 else 0.0
    cost_per_kg_dm    = total_cost_tl / total_dm         if total_cost_tl > 0 else 0.0
    cost_per_liter_milk = total_cost_tl / predicted_milk_L if (total_cost_tl > 0 and predicted_milk_L > 0) else None

    return {
        "live_weight": live_weight,
        "tmr_summary": {
            "total_as_fed_kg":  round(total_as_fed, 2),
            "total_dm_kg":      round(total_dm, 2),
            "ration_dm_pct":    round(ration_dm_pct, 1),
            "ufl_per_kg_dm":    round(ufl_per_kg_dm, 3),
            "pdi_per_kg_dm":    round(pdi_per_kg_dm, 1),
            "hp_pct_dm":        round(hp_pct_dm, 1),
            "starch_pct_dm":    round(starch_pct_dm, 1) if starch_pct_dm is not None else None,
            "ndf_pct_dm":       round(ndf_pct_dm,  1)  if ndf_pct_dm    is not None else None,
            "nfc_pct_dm":       round(nfc_pct_dm,  1)  if nfc_pct_dm    is not None else None,
            "endf_pct_dm":      round(endf_pct_dm, 1)  if endf_pct_dm   is not None else None,
            "ca_pct_dm":        round(ca_pct_dm,   2)  if ca_pct_dm     is not None else None,
            "p_pct_dm":         round(p_pct_dm,    2)  if p_pct_dm      is not None else None,
            "total_ufl":        round(total_ufl, 2),
            "total_pdi_g":      round(total_pdi_g, 0),
            "total_cost_tl":      round(total_cost_tl, 2),
            "cost_per_kg_dm":     round(cost_per_kg_dm, 2),
            "cost_per_liter_milk": round(cost_per_liter_milk, 2) if cost_per_liter_milk is not None else None,
        },
        "maintenance": {
            "ufl":   round(maintenance_ufl, 2),
            "pdi_g": round(maintenance_pdi_g, 0),
        },
        "milk_estimate": {
            "milk_by_energy_L":  round(milk_by_energy_L, 1),
            "milk_by_pdi_L":     round(milk_by_pdi_L, 1),
            "predicted_milk_L":  round(predicted_milk_L, 1),
            "limit_factor":      limit_factor,
        },
        "rows": rows,
    }
