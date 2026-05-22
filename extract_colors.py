#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from pathlib import Path
from collections import Counter
import re

import numpy as np
from PIL import Image, ImageOps

BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / "images"
OUTPUT_FILE = BASE_DIR / "art_periods_data.json"

N_BARV = 6
MAX_PIKSLOV_NA_SLIKO = 120_000

# -----------------------------------------
# OBDOBJA + KLJUČNE BESEDE
# -----------------------------------------

OBDOBJA = [
    {
        "naslov": "Prazgodovina",
        "leto": "40000–3000 pr.n.št.",
        "opis": "Jamske poslikave in zemeljski pigmenti.",
        "keywords": [
            "lascaux", "altamira", "chauvet", "bhimbetka",
            "willendorf", "cueva", "niaux", "capivara"
        ]
    },
    {
        "naslov": "Stari Egipt",
        "leto": "3100–30 pr.n.št.",
        "opis": "Zlati toni in lapis lazuli.",
        "keywords": [
            "nefertiti", "tutank", "egypt", "giza",
            "sphinx", "nebamun", "ramzes", "amenhotep",
            "narmer"
        ]
    },
    {
        "naslov": "Srednji vek",
        "leto": "500–1500",
        "opis": "Religiozna umetnost in bogate simbolne barve.",
        "keywords": [
            "kells", "rubljev", "rublev", "giotto",
            "bayeux", "justinian", "chartres",
            "maesta", "limbourg"
        ]
    },
    {
        "naslov": "Renesansa",
        "leto": "1400–1600",
        "opis": "Bogati zemeljski toni in chiaroscuro.",
        "keywords": [
            "mona", "leonardo", "michelangelo",
            "botticelli", "raphael", "titian",
            "van_eyck", "arnolfini", "primavera"
        ]
    },
    {
        "naslov": "Impresionizem",
        "leto": "1870–1900",
        "opis": "Svetle in vibrantne barve.",
        "keywords": [
            "monet", "renoir", "degas",
            "pissarro", "caillebotte",
            "morisot", "cassatt"
        ]
    },
    {
        "naslov": "Bauhaus",
        "leto": "1919–1933",
        "opis": "Geometrija in primarne barve.",
        "keywords": [
            "kandinsky", "mondrian",
            "bauhaus", "gropius",
            "klee", "bayer"
        ]
    },
    {
        "naslov": "Pop Art",
        "leto": "1955–1975",
        "opis": "Močne nasičene barve pop kulture.",
        "keywords": [
            "warhol", "lichtenstein",
            "hockney", "jasper",
            "marilyn", "campbell"
        ]
    },
    {
        "naslov": "Digitalna doba",
        "leto": "1990–danes",
        "opis": "Digitalne in neonske barve.",
        "keywords": [
            "beeple", "teamlab", "anadol",
            "eliasson", "paik", "arcangel",
            "reas", "digital"
        ]
    }
]

# -----------------------------------------
# BARVNA IMENA
# -----------------------------------------

BARVNA_TABELA = [
    ("Rdeča", (255, 0, 0)),
    ("Modra", (0, 0, 255)),
    ("Zelena", (0, 128, 0)),
    ("Rumena", (255, 255, 0)),
    ("Oranžna", (255, 165, 0)),
    ("Vijolična", (128, 0, 128)),
    ("Rjava", (165, 42, 42)),
    ("Bež", (245, 245, 220)),
    ("Siva", (128, 128, 128)),
    ("Črna", (0, 0, 0)),
    ("Bela", (255, 255, 255)),
]

# -----------------------------------------
# POMOŽNE
# -----------------------------------------

def poimenuj_barvo(hex_barva):
    r, g, b = (int(hex_barva[i:i+2], 16) for i in (1, 3, 5))
    r_, g_, b_ = r / 255.0, g / 255.0, b / 255.0
    cmax = max(r_, g_, b_)
    cmin = min(r_, g_, b_)
    delta = cmax - cmin
    s = (delta / cmax) if cmax > 0 else 0.0
    v = cmax
    luma = 0.2126 * r_ + 0.7152 * g_ + 0.0722 * b_

    if delta == 0:
        h = 0.0
    elif cmax == r_:
        h = (60.0 * ((g_ - b_) / delta)) % 360
    elif cmax == g_:
        h = 60.0 * ((b_ - r_) / delta) + 120
    else:
        h = 60.0 * ((r_ - g_) / delta) + 240

    def podton():
        if s < 0.015:
            return ""
        if h < 12 or h >= 350:
            return "rdečkastim"
        if h < 28:
            return "rdeče-oranžnim"
        if h < 45:
            return "oranžnim"
        if h < 70:
            return "rumenkastim"
        if h < 95:
            return "rumeno-zelenkastim"
        if h < 165:
            return "zelenkastim"
        if h < 195:
            return "turkiznim"
        if h < 250:
            return "modrikastim"
        if h < 290:
            return "vijoličastim"
        if h < 330:
            return "rožnatim"
        return "rdečkasto-rožnatim"

    def nevtralno_ime():
        ton = podton()
        dodatek = f" z {ton} tonom" if ton else ""
        if v >= 0.96:
            return "Skoraj bela" + dodatek
        if v >= 0.88:
            return "Zelo svetlo siva" + dodatek
        if v >= 0.72:
            return "Svetlo siva" + dodatek
        if v >= 0.52:
            return "Srednje siva" + dodatek
        if v >= 0.32:
            return "Temno siva" + dodatek
        if v >= 0.14:
            return "Zelo temno siva" + dodatek
        return "Skoraj črna" + dodatek

    def svetlost():
        if luma >= 0.88:
            return "zelo svetla"
        if luma >= 0.72:
            return "svetla"
        if luma >= 0.55:
            return "srednje svetla"
        if luma >= 0.38:
            return "srednje temna"
        if luma >= 0.20:
            return "temna"
        return "zelo temna"

    def osnovni_odtenek():
        if h < 10 or h >= 350:
            return "rdeča"
        if h < 24:
            return "rdeče-oranžna"
        if h < 42:
            return "oranžna"
        if h < 55:
            return "rumeno-oranžna"
        if h < 72:
            return "rumena"
        if h < 92:
            return "rumeno-zelena"
        if h < 155:
            return "zelena"
        if h < 178:
            return "modro-zelena"
        if h < 198:
            return "turkizna"
        if h < 235:
            return "modra"
        if h < 260:
            return "modro-vijolična"
        if h < 292:
            return "vijolična"
        if h < 330:
            return "rožnata"
        return "rdečkasto rožnata"

    if s < 0.09:
        return nevtralno_ime()

    if v < 0.14:
        ton = podton()
        return f"Skoraj črna z {ton} tonom" if ton else "Skoraj črna"

    if 12 <= h < 48 and v < 0.78:
        if h < 24:
            odtenek = "rdečkasto rjava"
        elif h < 38:
            odtenek = "oranžno rjava"
        else:
            odtenek = "rumenkasto rjava"
        return f"{svetlost().capitalize()} {odtenek}"

    if 48 <= h < 82 and v < 0.68 and s < 0.75:
        return f"{svetlost().capitalize()} oker rjava"

    if 70 <= h < 145 and v < 0.48 and s < 0.65:
        return f"{svetlost().capitalize()} olivno zelena"

    if s < 0.24:
        ton = podton()
        if 42 <= h < 75 and v > 0.70:
            return f"{svetlost().capitalize()} kremno rumena"
        if 18 <= h < 55 and v > 0.55:
            return f"{svetlost().capitalize()} bež"
        return f"{nevtralno_ime()} z izrazitejšim {ton} tonom" if ton else nevtralno_ime()

    if s < 0.45:
        return f"{svetlost().capitalize()} umirjena {osnovni_odtenek()}"

    if s > 0.78 and v > 0.70:
        return f"Živa {osnovni_odtenek()}"

    return f"{svetlost().capitalize()} {osnovni_odtenek()}"


def nalozi_obstojeci_katalog():
    """Prebere trenutni JSON, da generator ohrani naslove, avtorje in letnice."""
    if not OUTPUT_FILE.exists():
        return {}, {}

    try:
        data = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"[OPOZORILO] Obstojecega JSON-a ni bilo mogoce prebrati: {e}")
        return {}, {}

    if not isinstance(data, list):
        return {}, {}

    obdobja = {}
    dela = {}

    for i_obdobje, obdobje in enumerate(data):
        naslov = obdobje.get("naslov")
        if not naslov:
            continue

        obdobja[naslov] = {
            "leto": obdobje.get("leto", ""),
            "opis": obdobje.get("opis", ""),
            "imena": obdobje.get("imena", []),
        }

        for i_delo, delo in enumerate(obdobje.get("dela", [])):
            img = delo.get("img", "")
            if not img:
                continue

            dela[Path(img).name.lower()] = {
                "title": delo.get("title", ""),
                "artist": delo.get("artist", ""),
                "year": delo.get("year", ""),
                "img": f"images/{Path(img).name}",
                "obdobje": naslov,
                "vrstni_red": (i_obdobje, i_delo),
            }

    return obdobja, dela


def rgb_v_hsv_batch(arr_rgb):
    """Pretvori float32 RGB [0..255] → HSV [H:0..360, S:0..1, V:0..1]."""
    r = arr_rgb[:, 0] / 255.0
    g = arr_rgb[:, 1] / 255.0
    b = arr_rgb[:, 2] / 255.0
    cmax = np.maximum(np.maximum(r, g), b)
    cmin = np.minimum(np.minimum(r, g), b)
    delta = cmax - cmin
    v = cmax
    s = np.divide(delta, cmax, out=np.zeros_like(delta), where=cmax > 0)
    h = np.zeros_like(r)
    mask_r = (delta > 0) & (cmax == r)
    mask_g = (delta > 0) & (cmax == g)
    mask_b = (delta > 0) & (cmax == b)
    h[mask_r] = 60.0 * (((g[mask_r] - b[mask_r]) / delta[mask_r]) % 6)
    h[mask_g] = 60.0 * (((b[mask_g] - r[mask_g]) / delta[mask_g]) + 2)
    h[mask_b] = 60.0 * (((r[mask_b] - g[mask_b]) / delta[mask_b]) + 4)
    return np.stack([h, s, v], axis=1)


def nalozi_piksle(path):
    """
    Naloži sliko in vrne RGB piksle iz dejanske slike.

    Slike ne pomanjšujemo z interpolacijo, ker bi to ustvarilo nove barve,
    ki jih v izvorni sliki ni. Pri zelo velikih slikah vzamemo determinističen
    vzorec realnih pikslov, zato paleta še vedno nastane samo iz obstoječih
    barv.
    """
    try:
        img = Image.open(path)
        img = ImageOps.exif_transpose(img)

        if img.mode in ("RGBA", "LA") or "transparency" in img.info:
            rgba = img.convert("RGBA")
            ozadje = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
            img = Image.alpha_composite(ozadje, rgba).convert("RGB")
        else:
            img = img.convert("RGB")

        arr = np.asarray(img, dtype=np.uint8).reshape(-1, 3)

        if len(arr) > MAX_PIKSLOV_NA_SLIKO:
            rng = np.random.default_rng(20260522)
            idx = rng.choice(len(arr), size=MAX_PIKSLOV_NA_SLIKO, replace=False)
            arr = arr[idx]

        if len(arr) < 20:
            return None
        return arr.astype(np.int16)
    except Exception as e:
        print(f"[NAPAKA] {path.name}: {e}")
        return None


def izracunaj_izrazitost(r, g, b, delez):
    """
    Oceni vizualno izrazitost barve.

    Delež slike je najpomembnejši, nasičenost in svetlost pa pomagata,
    da manjši, a zelo značilni poudarki ne izginejo iz palete.
    """
    import math
    r_, g_, b_ = r / 255.0, g / 255.0, b / 255.0
    cmax = max(r_, g_, b_)
    cmin = min(r_, g_, b_)
    delta = cmax - cmin

    s = (delta / cmax) if cmax > 0 else 0.0
    v = cmax

    return math.sqrt(delez) * (0.55 + 1.20 * s + 0.30 * v + 0.20 * (s ** 2) * v)


def ekstrahiraj_barve(vsi_rgb_raw, n_barv=N_BARV, dopolni_podobne=False):
    """
    Ekstrahira n_barv dominantnih barv, ki so RES prisotne v podanih pikslih.

    Barve najprej združimo v majhne HSV skupine, nato izberemo najmočnejše
    in dovolj različne skupine. Končni HEX vedno nastane iz dejanskega piksla,
    nikoli iz povprečja, centroida ali umetno ustvarjenega odtenka.
    """
    if vsi_rgb_raw is None or len(vsi_rgb_raw) == 0:
        return []

    piksli = np.clip(vsi_rgb_raw, 0, 255).astype(np.int16)

    # ── KORAK 1: HSV bin kvantizacija ───────────────────────────────
    r_ = piksli[:, 0] / 255.0
    g_ = piksli[:, 1] / 255.0
    b_ = piksli[:, 2] / 255.0
    cmax = np.maximum(np.maximum(r_, g_), b_)
    cmin = np.minimum(np.minimum(r_, g_), b_)
    delta = cmax - cmin

    v = cmax
    s = np.divide(delta, cmax, out=np.zeros_like(delta), where=cmax > 0)
    h = np.zeros(len(piksli))
    mr = (delta > 0) & (cmax == r_)
    mg = (delta > 0) & (cmax == g_)
    mb = (delta > 0) & (cmax == b_)
    h[mr] = (60.0 * ((g_[mr] - b_[mr]) / delta[mr])) % 360
    h[mg] = 60.0 * ((b_[mg] - r_[mg]) / delta[mg]) + 120
    h[mb] = 60.0 * ((r_[mb] - g_[mb]) / delta[mb]) + 240

    # Drobni bini ohranijo razlike, hkrati pa združijo JPEG šum.
    H_BIN = 8
    S_BIN = 0.08
    V_BIN = 0.08

    h_bin = np.where(s < 0.12, 0, np.floor(h / H_BIN).astype(np.int32))
    s_bin = np.minimum(np.floor(s / S_BIN).astype(np.int32), int(1 / S_BIN))
    v_bin = np.minimum(np.floor(v / V_BIN).astype(np.int32), int(1 / V_BIN))

    bin_keys = h_bin * 10000 + s_bin * 100 + v_bin

    keys, inverse, counts = np.unique(bin_keys, return_inverse=True, return_counts=True)
    sums_r = np.bincount(inverse, weights=piksli[:, 0], minlength=len(keys))
    sums_g = np.bincount(inverse, weights=piksli[:, 1], minlength=len(keys))
    sums_b = np.bincount(inverse, weights=piksli[:, 2], minlength=len(keys))
    avg_rgb = np.stack([sums_r, sums_g, sums_b], axis=1) / counts[:, None]

    kandidati = []
    skupaj = len(piksli)
    min_pikslov = max(3, int(skupaj * 0.0005))

    for i, key in enumerate(keys):
        stevilo = int(counts[i])
        if stevilo < min_pikslov:
            continue

        avg = avg_rgb[i]
        delez = stevilo / skupaj
        kandidati.append({
            "key": int(key),
            "avg": avg,
            "stevilo": stevilo,
            "delez": delez,
            "izrazitost": izracunaj_izrazitost(avg[0], avg[1], avg[2], delez),
        })

    if not kandidati:
        kandidati = [{
            "key": int(keys[int(np.argmax(counts))]),
            "avg": avg_rgb[int(np.argmax(counts))],
            "stevilo": int(np.max(counts)),
            "delez": float(np.max(counts) / skupaj),
            "izrazitost": 1.0,
        }]

    kandidati.sort(key=lambda x: (x["izrazitost"], x["delez"]), reverse=True)

    def reprezentant_bina(kandidat):
        maska = bin_keys == kandidat["key"]
        px = piksli[maska].astype(np.int32)
        cilj = kandidat["avg"].astype(np.float32)
        razdalje_sq = np.sum((px - cilj) ** 2, axis=1)
        return px[int(np.argmin(razdalje_sq))]

    def razdalja(a, b):
        return float(np.sqrt(np.sum((a.astype(np.float32) - b.astype(np.float32)) ** 2)))

    def barvna_druzina(c):
        r, g, b = [int(x) / 255.0 for x in c]
        cmax = max(r, g, b)
        cmin = min(r, g, b)
        delta = cmax - cmin
        s_c = (delta / cmax) if cmax > 0 else 0.0

        if s_c < 0.14:
            if cmax < 0.22:
                return "nevtralna-temna"
            if cmax > 0.82:
                return "nevtralna-svetla"
            return "nevtralna-srednja"

        if cmax == r:
            h_c = (60.0 * ((g - b) / delta)) % 360
        elif cmax == g:
            h_c = 60.0 * ((b - r) / delta) + 120
        else:
            h_c = 60.0 * ((r - g) / delta) + 240

        return f"hue-{int(h_c // 20)}"

    izbrane_rgb = []
    uporabljeni = set()
    reprezentanti = [(k, reprezentant_bina(k)) for k in kandidati]
    stevilo_po_druzini = Counter()
    stevilo_nevtralnih = 0

    strogi_prehodi = (
        (1, 1, 30),
        (1, 1, 22),
    )
    dopolnilni_prehodi = (
        (2, 1, 18),
        (3, 2, 10),
        (999, 999, 0),
    )
    prehodi = strogi_prehodi + (dopolnilni_prehodi if dopolni_podobne else ())

    for max_na_druzino, max_nevtralnih, min_razmak in prehodi:
        for kandidat, px in reprezentanti:
            if len(izbrane_rgb) >= n_barv:
                break

            kljuc = tuple(int(x) for x in px)
            druzina = barvna_druzina(px)
            je_nevtralna = druzina.startswith("nevtralna")
            if kljuc in uporabljeni:
                continue
            if stevilo_po_druzini[druzina] >= max_na_druzino:
                continue
            if je_nevtralna and stevilo_nevtralnih >= max_nevtralnih:
                continue
            if any(razdalja(px, ze) < min_razmak for ze in izbrane_rgb):
                continue

            izbrane_rgb.append(px.copy())
            uporabljeni.add(kljuc)
            stevilo_po_druzini[druzina] += 1
            if je_nevtralna:
                stevilo_nevtralnih += 1

        if len(izbrane_rgb) >= n_barv:
            break

    return [
        f"#{int(c[0]):02X}{int(c[1]):02X}{int(c[2]):02X}"
        for c in izbrane_rgb[:n_barv]
    ]


# -----------------------------------------
# RAZPOREDI SLIKE PO OBDOBJIH
# -----------------------------------------

def poisci_obdobje(filename):

    ime = filename.lower()

    for obdobje in OBDOBJA:

        for keyword in obdobje["keywords"]:

            if keyword in ime:
                return obdobje

    return None


# -----------------------------------------
# GLAVNA LOGIKA
# -----------------------------------------

def generiraj_json():

    obdobja_katalog, dela_katalog = nalozi_obstojeci_katalog()
    slike = sorted(IMAGES_DIR.glob("*"), key=lambda p: p.name.lower())

    dovoljene = {
        ".jpg", ".jpeg", ".png",
        ".webp", ".gif", ".svg"
    }

    rezultat = []

    for obdobje in OBDOBJA:

        print(f"\nObdelujem: {obdobje['naslov']}")

        obdobje_slike = []

        for slika in slike:

            if slika.suffix.lower() not in dovoljene:
                continue

            katalog_delo = dela_katalog.get(slika.name.lower())
            najdeno = None

            if katalog_delo:
                najdeno = {"naslov": katalog_delo["obdobje"]}
            else:
                najdeno = poisci_obdobje(slika.name)

            if najdeno and najdeno["naslov"] == obdobje["naslov"]:
                obdobje_slike.append(slika)

        obdobje_slike.sort(
            key=lambda slika: dela_katalog.get(
                slika.name.lower(),
                {"vrstni_red": (999, slika.name.lower())}
            )["vrstni_red"]
        )

        print(f"Najdenih slik: {len(obdobje_slike)}")

        vsi_piksli = []

        dela = []

        for slika in obdobje_slike:

            piksli = nalozi_piksle(slika)
            paleta_dela = (
                ekstrahiraj_barve(piksli)
                if piksli is not None
                else []
            )

            if piksli is not None:
                vsi_piksli.append(piksli)

            katalog_delo = dela_katalog.get(slika.name.lower())

            if katalog_delo:
                dela.append({
                    "title": katalog_delo["title"],
                    "artist": katalog_delo["artist"],
                    "year": katalog_delo["year"],
                    "img": f"images/{slika.name}",
                    "paleta": paleta_dela
                })
            else:
                title = re.sub(r'[_-]+', ' ', slika.stem).strip()

                dela.append({
                    "title": title,
                    "artist": "",
                    "year": "",
                    "img": f"images/{slika.name}",
                    "paleta": paleta_dela
                })

        skupni_piksli = (
            np.vstack(vsi_piksli)
            if vsi_piksli else None
        )

        paleta = ekstrahiraj_barve(skupni_piksli, dopolni_podobne=True)
        if not paleta:
            paleta = ["#808080"]

        obdobje_meta = obdobja_katalog.get(obdobje["naslov"], {})

        rezultat.append({
            "naslov": obdobje["naslov"],
            "leto": obdobje_meta.get("leto") or obdobje["leto"],
            "opis": obdobje_meta.get("opis") if "opis" in obdobje_meta else obdobje["opis"],
            "paleta": paleta,
            "imena": [
                poimenuj_barvo(c)
                for c in paleta
            ],
            "dela": dela
        })

    OUTPUT_FILE.write_text(
        json.dumps(
            rezultat,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print("\nKončano.")
    print("JSON shranjen v:", OUTPUT_FILE)


# -----------------------------------------

if __name__ == "__main__":

    if not IMAGES_DIR.exists():
        print("Mapa images ne obstaja:")
        print(IMAGES_DIR)

    else:
        generiraj_json()
