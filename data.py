"""Hardcoded reference data for the CSR Rasyon Hesaplayıcı.

NOTE: ``FEEDS`` is used only as the **initial** seed for the database when the
``feeds`` table is empty. After that, admin edits live in SQLite and are NOT
overwritten by these values. Targeted one-time data fixes are handled via the
versioned migration system in ``database.py``.
"""

FEEDS = [
    {"name": "Mısır silajı 35 KM iyi",  "dm_pct": 35,    "ufv": 0.87,    "protein": 6.5,    "pdie": 68,    "pdin": 47,    "cf": 16.5,  "fat": 3.0,   "ash": 4.7,   "starch": 29,   "ndf_pct": 41.6,  "nfc_pct": 45.0,   "endf_pct": 33.28,  "ca_pct": 0.08,  "p_pct": 0.13},
    {"name": "Mısır silajı 35 KM orta", "dm_pct": 35,    "ufv": 0.85,    "protein": 6.5,    "pdie": 60.7,  "pdin": 40.3,  "cf": 21.7,  "fat": 3.0,   "ash": 8.8,   "starch": 23.9, "ndf_pct": 47.7,  "nfc_pct": 35.0,   "endf_pct": 38.16,  "ca_pct": 0.08,  "p_pct": 0.13},
    {"name": "Mısır silajı 35 KM kötü", "dm_pct": 35,    "ufv": 0.78,    "protein": 6.2,    "pdie": 57.9,  "pdin": 38.6,  "cf": 26.0,  "fat": 3.0,   "ash": 8.9,   "starch": 21.4, "ndf_pct": 54.8,  "nfc_pct": 28.0,   "endf_pct": 43.84,  "ca_pct": 0.08,  "p_pct": 0.13},
    {"name": "Mısır silajı 30 KM iyi",  "dm_pct": 30,    "ufv": 0.80,    "protein": 7.0,    "pdie": 65,    "pdin": 42,    "cf": 20.5,  "fat": 2.5,   "ash": 4.6,   "starch": 25,   "ndf_pct": 44.4,  "nfc_pct": 42.6,   "endf_pct": 35.52,  "ca_pct": 0.08,  "p_pct": 0.13},
    {"name": "Mısır silajı 30 KM orta", "dm_pct": 28,    "ufv": 0.76,    "protein": 7.0,    "pdie": 46.5,  "pdin": 43,    "cf": 24.1,  "fat": 2.7,   "ash": 7.3,   "starch": 21.5, "ndf_pct": 53.6,  "nfc_pct": 30.5,   "endf_pct": 42.88,  "ca_pct": 0.08,  "p_pct": 0.13},
    {"name": "Mısır silajı 30 KM kötü", "dm_pct": 30,    "ufv": 0.74,    "protein": 7.0,    "pdie": 59.7,  "pdin": 42.8,  "cf": 28.3,  "fat": 2.66,  "ash": 7.7,   "starch": 14.8, "ndf_pct": 62.0,  "nfc_pct": 21.8,   "endf_pct": 49.6,   "ca_pct": 0.08,  "p_pct": 0.13},
    {"name": "Mısır silajı 25 KM iyi",  "dm_pct": 25,    "ufv": 0.81,    "protein": 7.0,    "pdie": 62,    "pdin": 43,    "cf": 25.2,  "fat": 2.4,   "ash": 6.0,   "starch": 23,   "ndf_pct": 54.0,  "nfc_pct": 31.7,   "endf_pct": 43.2,   "ca_pct": 0.08,  "p_pct": 0.13},
    {"name": "Mısır silajı 25 KM orta", "dm_pct": 25,    "ufv": 0.79,    "protein": 7.0,    "pdie": 63.6,  "pdin": 51.6,  "cf": 27.9,  "fat": 2.4,   "ash": 7.8,   "starch": 18.4, "ndf_pct": 58.0,  "nfc_pct": 25.9,   "endf_pct": 46.4,   "ca_pct": 0.08,  "p_pct": 0.13},
    {"name": "Mısır silajı 25 KM kötü", "dm_pct": 25,    "ufv": 0.70,    "protein": 7.0,    "pdie": 59,    "pdin": 49,    "cf": 33.4,  "fat": 2.4,   "ash": 9.4,   "starch": 16.6, "ndf_pct": 61.0,  "nfc_pct": 21.32,  "endf_pct": 48.8,   "ca_pct": 0.08,  "p_pct": 0.13},
    {"name": "Yonca 15 prt",            "dm_pct": 90,    "ufv": 0.56,    "protein": 15.0,   "pdie": 89,    "pdin": 96,    "cf": 32.0,  "fat": 2.4,   "ash": 10.8,  "starch": 0,    "ndf_pct": 50.4,  "nfc_pct": None,   "endf_pct": 44.352, "ca_pct": 2.04,  "p_pct": 0.26},
    {"name": "Yonca 17.5 prt",          "dm_pct": 90,    "ufv": 0.60,    "protein": 17.5,   "pdie": 101,   "pdin": 114,   "cf": 29.6,  "fat": 2.7,   "ash": 11.5,  "starch": 0,    "ndf_pct": 47.7,  "nfc_pct": None,   "endf_pct": 41.976, "ca_pct": 2.18,  "p_pct": 0.26},
    {"name": "Yonca 18.5 prt",          "dm_pct": 90,    "ufv": 0.62,    "protein": 18.5,   "pdie": 104.5, "pdin": 121,   "cf": 28.5,  "fat": 2.88,  "ash": 11.7,  "starch": 0,    "ndf_pct": 46.4,  "nfc_pct": None,   "endf_pct": 40.832, "ca_pct": 2.22,  "p_pct": 0.26},
    {"name": "Yonca 23 prt",            "dm_pct": 90,    "ufv": 0.71,    "protein": 23.2,   "pdie": 126.6, "pdin": 156.6, "cf": 21.0,  "fat": 3.4,   "ash": 12.8,  "starch": 0,    "ndf_pct": 37.7,  "nfc_pct": None,   "endf_pct": 33.176, "ca_pct": 2.5,   "p_pct": 0.26},
    {"name": "Pancar Posası",           "dm_pct": 20,    "ufv": 0.87,    "protein": 8.7,    "pdie": 101,   "pdin": 61,    "cf": 20.8,  "fat": 0,     "ash": 6.7,   "starch": 0,    "ndf_pct": 48.0,  "nfc_pct": 39.7,   "endf_pct": None,   "ca_pct": 0.28,  "p_pct": 0.08},
    {"name": "Yulaf Otu",               "dm_pct": 88,    "ufv": 0.58,    "protein": 10.3,   "pdie": 68.4,  "pdin": 65.5,  "cf": 30.4,  "fat": 2.3,   "ash": 9.8,   "starch": 0,    "ndf_pct": 61.9,  "nfc_pct": 15.5,   "endf_pct": 55.7,   "ca_pct": None,  "p_pct": None},
    {"name": "Fiğ Yulaf Otu",           "dm_pct": 88,    "ufv": 0.59,    "protein": 14.0,   "pdie": 77.4,  "pdin": 90.6,  "cf": 31.0,  "fat": 3.0,   "ash": 9.0,   "starch": 0,    "ndf_pct": 55.9,  "nfc_pct": 18.0,   "endf_pct": 50.3,   "ca_pct": None,  "p_pct": None},
    {"name": "Fiğ Otu",                 "dm_pct": 88,    "ufv": 0.75,    "protein": 16.4,   "pdie": 90.4,  "pdin": 107,   "cf": 24.7,  "fat": 2.4,   "ash": 7.4,   "starch": 0,    "ndf_pct": 38.8,  "nfc_pct": 19.0,   "endf_pct": 34.9,   "ca_pct": None,  "p_pct": None},
    {"name": "Arpa Otu",                "dm_pct": 88,    "ufv": 0.33,    "protein": 5.0,    "pdie": 56,    "pdin": 46,    "cf": 39.0,  "fat": 0,     "ash": 6.6,   "starch": 0,    "ndf_pct": 68.0,  "nfc_pct": None,   "endf_pct": 61.22,  "ca_pct": 0.14,  "p_pct": 0.05},
    {"name": "Saman",                   "dm_pct": 88,    "ufv": 0.29,    "protein": 3.1,    "pdie": 44,    "pdin": 22,    "cf": 42.0,  "fat": 0,     "ash": 8.0,   "starch": 0,    "ndf_pct": 79.8,  "nfc_pct": None,   "endf_pct": 75.81,  "ca_pct": 0.08,  "p_pct": 0.05},
    {"name": "Arpa Posası",             "dm_pct": 25.8,  "ufv": 1.05,    "protein": 26.3,   "pdie": 16.2,  "pdin": 16.9,  "cf": 11.0,  "fat": 7.9,   "ash": 3.9,   "starch": 5.13, "ndf_pct": 53.2,  "nfc_pct": 11.0,   "endf_pct": 53.2,   "ca_pct": 0.28,  "p_pct": 0.5},
    {"name": "Arpa",                    "dm_pct": 89.5,  "ufv": 1.00,    "protein": 12.3,   "pdie": 100,   "pdin": 84,    "cf": 6.7,   "fat": 2.0,   "ash": 3.0,   "starch": 56.4, "ndf_pct": 21.2,  "nfc_pct": 61.45,  "endf_pct": None,   "ca_pct": 0.05,  "p_pct": 0.29},
    {"name": "Mısır",                   "dm_pct": 86,    "ufv": 1.22,    "protein": 7.9,    "pdie": 89.9,  "pdin": 61.7,  "cf": 2.2,   "fat": 2.8,   "ash": 1.4,   "starch": 60,   "ndf_pct": 10.5,  "nfc_pct": 77.4,   "endf_pct": None,   "ca_pct": 0.03,  "p_pct": 0.23},
    {"name": "Arpa flake",              "dm_pct": 89.5,  "ufv": 1.06,    "protein": 12.3,   "pdie": 100,   "pdin": 84,    "cf": 6.7,   "fat": 2.0,   "ash": 3.0,   "starch": 56.4, "ndf_pct": 21.2,  "nfc_pct": 61.45,  "endf_pct": None,   "ca_pct": 0.05,  "p_pct": 0.29},
    {"name": "Mısır flake",             "dm_pct": 86,    "ufv": 1.254,   "protein": 7.9,    "pdie": 89.9,  "pdin": 61.7,  "cf": 2.2,   "fat": 2.8,   "ash": 1.4,   "starch": 75.5, "ndf_pct": 10.5,  "nfc_pct": 77.4,   "endf_pct": None,   "ca_pct": 0.03,  "p_pct": 0.23},
    {"name": "Buğday",                  "dm_pct": 90,    "ufv": 1.146,   "protein": 13.11,  "pdie": 103,   "pdin": 87.5,  "cf": 3.3,   "fat": 1.78,  "ash": 1.56,  "starch": 70,   "ndf_pct": 13.7,  "nfc_pct": 70.0,   "endf_pct": None,   "ca_pct": 0.04,  "p_pct": 0.26},
    {"name": "Razmol",                  "dm_pct": 88,    "ufv": 0.98,    "protein": 17.6,   "pdie": 99,    "pdin": 115,   "cf": 8.0,   "fat": 4.0,   "ash": 4.9,   "starch": 31.4, "ndf_pct": 35.5,  "nfc_pct": 42.5,   "endf_pct": None,   "ca_pct": 0.14,  "p_pct": 0.98},
    {"name": "Bonkalit",                "dm_pct": 88,    "ufv": 1.26,    "protein": 14.4,   "pdie": 107.9, "pdin": 95.5,  "cf": 1.7,   "fat": 2.7,   "ash": 1.6,   "starch": 67.8, "ndf_pct": 11.0,  "nfc_pct": 72.4,   "endf_pct": None,   "ca_pct": 0.1,   "p_pct": 0.4},
    {"name": "Pamuk Tohumu (çiğit)",    "dm_pct": 90.6,  "ufv": 0.944,   "protein": 23.6,   "pdie": 85.6,  "pdin": 145.6, "cf": 26.0,  "fat": 21.2,  "ash": 4.3,   "starch": 0,    "ndf_pct": 42.56, "nfc_pct": None,   "endf_pct": None,   "ca_pct": 0.16,  "p_pct": 0.63},
    {"name": "Arpamiks",                "dm_pct": 89,    "ufv": 0.757,   "protein": 22.4,   "pdie": 87,    "pdin": 120,   "cf": 12.3,  "fat": 3.4,   "ash": 15.6,  "starch": 12.3, "ndf_pct": 32.4,  "nfc_pct": 26.4,   "endf_pct": None,   "ca_pct": 3.68,  "p_pct": 0.79},
    {"name": "Ayçiçek Küspesi 26 prot", "dm_pct": 87,    "ufv": 0.38,    "protein": 27.5,   "pdie": 94,    "pdin": 179,   "cf": 31.0,  "fat": 1.3,   "ash": 7.0,   "starch": 0,    "ndf_pct": 45.9,  "nfc_pct": 15.8,   "endf_pct": None,   "ca_pct": 0.25,  "p_pct": 0.76},
    {"name": "Ayçiçek Küspesi 35 prot", "dm_pct": 88,    "ufv": 0.726,   "protein": 38.6,   "pdie": 135,   "pdin": 251,   "cf": 20.0,  "fat": 1.0,   "ash": 7.0,   "starch": 0,    "ndf_pct": 39.7,  "nfc_pct": 13.5,   "endf_pct": None,   "ca_pct": 0.25,  "p_pct": 0.8},
    {"name": "Pamuk Küspesi Exp 25 prot","dm_pct": 86,   "ufv": 0.63,    "protein": 28.5,   "pdie": 135,   "pdin": 199,   "cf": 27.9,  "fat": 10.4,  "ash": 5.8,   "starch": 0,    "ndf_pct": 46.5,  "nfc_pct": 8.7,    "endf_pct": None,   "ca_pct": 0.11,  "p_pct": 0.7},
    {"name": "Pamuk Küspesi 30 prot",   "dm_pct": 89,    "ufv": 0.80,    "protein": 35.4,   "pdie": 177,   "pdin": 247,   "cf": 17.9,  "fat": 2.47,  "ash": 7.4,   "starch": 0,    "ndf_pct": 39.33, "nfc_pct": 15.3,   "endf_pct": None,   "ca_pct": 0.15,  "p_pct": 0.81},
    {"name": "CSR CD BESİ",             "dm_pct": 91.07, "ufv": 1.043,   "protein": 35.97,  "pdie": 108,   "pdin": 108,   "cf": 14.01, "fat": 6.94,  "ash": 13.94, "starch": 1.72, "ndf_pct": 19.91, "nfc_pct": 19.9,   "endf_pct": 7.8,    "ca_pct": 3.07,  "p_pct": 0.8},
    {"name": "SDF H",                   "dm_pct": 91.16, "ufv": 1.176,   "protein": 43.36,  "pdie": 114.73,"pdin": 114.73,"cf": 12.41, "fat": 3.44,  "ash": 6.63,  "starch": 3.13, "ndf_pct": 21.8,  "nfc_pct": 24.77,  "endf_pct": 7.4,    "ca_pct": 0.43,  "p_pct": 0.8},
    {"name": "Soya küspesi",            "dm_pct": 89,    "ufv": 1.209,   "protein": 50.8,   "pdie": 261,   "pdin": 373,   "cf": 4.34,  "fat": 2.3,   "ash": 6.8,   "starch": 0,    "ndf_pct": 9.8,   "nfc_pct": 30.0,   "endf_pct": None,   "ca_pct": 0.354, "p_pct": None},
    {"name": "Üre",                     "dm_pct": 99,    "ufv": 0,       "protein": 287,    "pdie": 0,     "pdin": 0,     "cf": 0,     "fat": 0,     "ash": 0.7,   "starch": 0,    "ndf_pct": None,  "nfc_pct": None,   "endf_pct": None,   "ca_pct": None,  "p_pct": None},
]

FEEDS_BY_NAME = {f["name"]: f for f in FEEDS}

# Names removed from the seed list (also enforced in the live DB by migration 002).
OBSOLETE_FEED_NAMES = [
    "Buzağı Büyütme",
    "Efe Toz",
    "Efect Besi Başlangıç",
    "Grand",
    "Pehlivan",
    "Pehlivan Toz",
    "Yiğit",
    "Çevik",
]

UFV_MATRIX = {
    250: {800: 4.1, 1000: 4.5, 1200: 4.9, 1400: 5.3, 1600: 5.7, 1800: 6.1, 2000: 6.5},
    300: {800: 4.6, 1000: 5.0, 1200: 5.4, 1400: 5.8, 1600: 6.3, 1800: 6.8, 2000: 7.3},
    350: {800: 5.1, 1000: 5.5, 1200: 5.9, 1400: 6.4, 1600: 6.9, 1800: 7.4, 2000: 7.9},
    400: {800: 5.6, 1000: 6.0, 1200: 6.4, 1400: 6.9, 1600: 7.4, 1800: 8.0, 2000: 8.6},
    450: {800: 5.9, 1000: 6.4, 1200: 6.9, 1400: 7.5, 1600: 8.0, 1800: 8.6, 2000: 9.2},
    500: {800: 6.4, 1000: 6.9, 1200: 7.4, 1400: 8.0, 1600: 8.6, 1800: 9.3, 2000: 10.0},
    550: {800: 6.8, 1000: 7.4, 1200: 8.0, 1400: 8.6, 1600: 9.3, 1800: 10.0, 2000: 10.7},
    600: {800: 7.3, 1000: 7.9, 1200: 8.5, 1400: 9.2, 1600: 10.0, 1800: 10.8, 2000: 11.6},
    650: {800: 7.6, 1000: 8.4, 1200: 9.2, 1400: 9.9, 1600: 10.8, 1800: 11.7, 2000: 12.6},
    700: {800: 8.3, 1000: 9.0, 1200: 9.9, 1400: 10.8, 1600: 11.7, 1800: 12.6, 2000: 13.5},
    750: {800: 8.9, 1000: 9.8, 1200: 10.8, 1400: 11.8, 1600: 12.8, 1800: 13.8, 2000: 14.8},
}

PDI_MATRIX = {
    250: {800: 425, 1000: 473, 1200: 521, 1400: 568, 1600: 615, 1800: 662, 2000: 709},
    300: {800: 462, 1000: 512, 1200: 562, 1400: 609, 1600: 654, 1800: 699, 2000: 744},
    350: {800: 501, 1000: 551, 1200: 601, 1400: 649, 1600: 694, 1800: 738, 2000: 782},
    400: {800: 539, 1000: 590, 1200: 641, 1400: 689, 1600: 734, 1800: 777, 2000: 818},
    450: {800: 580, 1000: 631, 1200: 682, 1400: 731, 1600: 776, 1800: 818, 2000: 857},
    500: {800: 621, 1000: 674, 1200: 727, 1400: 775, 1600: 820, 1800: 860, 2000: 897},
    550: {800: 669, 1000: 722, 1200: 775, 1400: 823, 1600: 866, 1800: 905, 2000: 944},
    600: {800: 720, 1000: 774, 1200: 828, 1400: 875, 1600: 915, 1800: 955, 2000: 995},
    650: {800: 782, 1000: 833, 1200: 884, 1400: 927, 1600: 960, 1800: 993, 2000: 1026},
    700: {800: 834, 1000: 892, 1200: 936, 1400: 967, 1600: 998, 1800: 1029, 2000: 1060},
    750: {800: 889, 1000: 932, 1200: 952, 1400: 972, 1600: 992, 1800: 1012, 2000: 1032},
}

WEIGHT_ROWS = sorted(UFV_MATRIX.keys())
GAIN_COLS = sorted(UFV_MATRIX[WEIGHT_ROWS[0]].keys())

DMI_TABLE = [
    (181.2, 3.0),
    (249.15, 2.8),
    (317.1, 2.6),
    (385.05, 2.4),
    (453.0, 2.2),
    (543.6, 2.0),
    (543.6, 1.8),
]
DMI_FALLBACK_PCT = 1.6

BREEDS = ["Holstein", "Simmental", "Charolais/Limousin"]

# ─── Dairy feed seeds (category sut/common) ──────────────────────────────────
# Used on fresh DB (seeded via init_db) AND on existing DBs (inserted by
# migration 004 if the feed name is not already present).

DAIRY_FEEDS = [
    # ── Common (3 feeds) – appear in BOTH besi and sut dropdowns ──
    {
        "name": "Mısır silajı sütçü 35 KM",
        "dm_pct": 35, "ufv": 0.87, "protein": 7.5,
        "pdie": 70, "pdin": 52, "cf": 20, "fat": 3.2, "ash": 5.0, "starch": 28,
        "category": "common",
        "rdp_pct_of_cp": 72.0, "rup_pct_of_cp": 28.0,
        "pdi_g_per_kg_dm": 70.0, "ufl_per_kg_dm": 0.87,
        "ndf_pct": 48.0, "nfc_pct": None, "endf_pct": None, "ca_pct": 0.22, "p_pct": 0.21,
    },
    {
        "name": "Arpa (ortak)",
        "dm_pct": 89.5, "ufv": 1.00, "protein": 12.3,
        "pdie": 100, "pdin": 84, "cf": 6.7, "fat": 2.0, "ash": 3.0, "starch": 56.4,
        "category": "common",
        "rdp_pct_of_cp": 75.0, "rup_pct_of_cp": 25.0,
        "pdi_g_per_kg_dm": 100.0, "ufl_per_kg_dm": 1.00,
        "ndf_pct": 20.0, "nfc_pct": 61.45, "endf_pct": None, "ca_pct": 0.06, "p_pct": 0.36,
    },
    {
        "name": "Melas",
        "dm_pct": 76, "ufv": 0.90, "protein": 10.0,
        "pdie": 55, "pdin": 60, "cf": 0, "fat": 0.3, "ash": 10.0, "starch": 0,
        "category": "common",
        "rdp_pct_of_cp": 95.0, "rup_pct_of_cp": 5.0,
        "pdi_g_per_kg_dm": 55.0, "ufl_per_kg_dm": 0.90,
        "ndf_pct": 0.0, "nfc_pct": None, "endf_pct": None, "ca_pct": 0.80, "p_pct": 0.10,
        "note": "Şeker pancarı melası",
    },
    # ── Süt (9 feeds) ─────────────────────────────────────────────
    {
        "name": "Yonca silajı 1. biçim",
        "dm_pct": 35, "ufv": 0.72, "protein": 19.0,
        "pdie": 110, "pdin": 130, "cf": 28, "fat": 3.0, "ash": 11.0, "starch": 0,
        "category": "sut",
        "rdp_pct_of_cp": 70.0, "rup_pct_of_cp": 30.0,
        "pdi_g_per_kg_dm": 110.0, "ufl_per_kg_dm": 0.72,
        "ndf_pct": 40.0, "nfc_pct": None, "endf_pct": None, "ca_pct": 1.50, "p_pct": 0.28,
    },
    {
        "name": "Buğday silajı",
        "dm_pct": 30, "ufv": 0.80, "protein": 10.5,
        "pdie": 72, "pdin": 71, "cf": 31, "fat": 2.5, "ash": 8.0, "starch": 12,
        "category": "sut",
        "rdp_pct_of_cp": 68.0, "rup_pct_of_cp": 32.0,
        "pdi_g_per_kg_dm": 72.0, "ufl_per_kg_dm": 0.80,
        "ndf_pct": 55.0, "nfc_pct": None, "endf_pct": None, "ca_pct": 0.50, "p_pct": 0.22,
    },
    {
        "name": "Korunan soya küspesi",
        "dm_pct": 88, "ufv": 1.05, "protein": 49.0,
        "pdie": 295, "pdin": 370, "cf": 4.0, "fat": 2.5, "ash": 6.5, "starch": 0,
        "category": "sut",
        "rdp_pct_of_cp": 30.0, "rup_pct_of_cp": 70.0,
        "pdi_g_per_kg_dm": 295.0, "ufl_per_kg_dm": 1.05,
        "ndf_pct": 9.0, "nfc_pct": None, "endf_pct": None, "ca_pct": 0.32, "p_pct": 0.65,
        "note": "Isı işlemli bypass soya",
    },
    {
        "name": "Rumen bypass yağ",
        "dm_pct": 99, "ufv": 3.00, "protein": 0.0,
        "pdie": 0, "pdin": 0, "cf": 0, "fat": 85.0, "ash": 1.0, "starch": 0,
        "category": "sut",
        "rdp_pct_of_cp": 0.0, "rup_pct_of_cp": 0.0,
        "pdi_g_per_kg_dm": 0.0, "ufl_per_kg_dm": 3.00,
        "ndf_pct": 0.0, "nfc_pct": None, "endf_pct": None, "ca_pct": 9.0, "p_pct": 0.0,
        "note": "Rumen korumalı yağ asidi",
    },
    {
        "name": "CSR SÜT konsantresi",
        "dm_pct": 90, "ufv": 1.00, "protein": 22.0,
        "pdie": 130, "pdin": 145, "cf": 8.0, "fat": 5.0, "ash": 12.0, "starch": 20,
        "category": "sut",
        "rdp_pct_of_cp": 60.0, "rup_pct_of_cp": 40.0,
        "pdi_g_per_kg_dm": 130.0, "ufl_per_kg_dm": 1.00,
        "ndf_pct": 22.0, "nfc_pct": None, "endf_pct": None, "ca_pct": 2.50, "p_pct": 0.80,
        "note": "CSR süt sığırı konsantresi",
    },
    {
        "name": "Sodyum bikarbonat",
        "dm_pct": 99, "ufv": 0.0, "protein": 0.0,
        "pdie": 0, "pdin": 0, "cf": 0, "fat": 0.0, "ash": 99.0, "starch": 0,
        "category": "sut",
        "rdp_pct_of_cp": 0.0, "rup_pct_of_cp": 0.0,
        "pdi_g_per_kg_dm": 0.0, "ufl_per_kg_dm": 0.0,
        "ndf_pct": 0.0, "nfc_pct": None, "endf_pct": None, "ca_pct": 0.0, "p_pct": 0.0,
        "note": "Tampon ajan; rumen pH koruma",
    },
    {
        "name": "Kalsiyum karbonat",
        "dm_pct": 99, "ufv": 0.0, "protein": 0.0,
        "pdie": 0, "pdin": 0, "cf": 0, "fat": 0.0, "ash": 56.0, "starch": 0,
        "category": "sut",
        "rdp_pct_of_cp": 0.0, "rup_pct_of_cp": 0.0,
        "pdi_g_per_kg_dm": 0.0, "ufl_per_kg_dm": 0.0,
        "ndf_pct": 0.0, "nfc_pct": None, "endf_pct": None, "ca_pct": 38.0, "p_pct": 0.0,
    },
    {
        "name": "Pancar posası kuru",
        "dm_pct": 88, "ufv": 0.92, "protein": 8.5,
        "pdie": 90, "pdin": 58, "cf": 19.0, "fat": 0.5, "ash": 6.5, "starch": 0,
        "category": "sut",
        "rdp_pct_of_cp": 70.0, "rup_pct_of_cp": 30.0,
        "pdi_g_per_kg_dm": 90.0, "ufl_per_kg_dm": 0.92,
        "ndf_pct": 44.0, "nfc_pct": None, "endf_pct": None, "ca_pct": 0.60, "p_pct": 0.08,
    },
    {
        "name": "Tritikale silajı",
        "dm_pct": 30, "ufv": 0.78, "protein": 11.0,
        "pdie": 75, "pdin": 74, "cf": 30, "fat": 2.0, "ash": 7.5, "starch": 15,
        "category": "sut",
        "rdp_pct_of_cp": 65.0, "rup_pct_of_cp": 35.0,
        "pdi_g_per_kg_dm": 75.0, "ufl_per_kg_dm": 0.78,
        "ndf_pct": 52.0, "nfc_pct": None, "endf_pct": None, "ca_pct": 0.45, "p_pct": 0.20,
    },
]
