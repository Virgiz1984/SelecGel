from __future__ import annotations

import itertools
import random
from dataclasses import dataclass

from .models import ReservoirCard, load_json


@dataclass
class RecipeCandidate:
    recipe_id: str
    name_ru: str
    track: str
    monomer_ratios: dict[str, float]
    target_mw_kda: float
    concentration_pct: float
    charge_density: float
    hydrophobe_pct: float
    predicted_frrw: float
    predicted_frro: float
    predicted_score: float
    rank: int = 0
    hypothesis: str = ""


HYDROPHOBES = {"C18AM", "C12AM"}
ANIONIC = {"AMPS", "AA"}
CATIONIC = {"ATAC"}


def _charge_density(ratios: dict[str, float], monomer_db: dict[str, dict]) -> float:
    total = sum(ratios.values()) or 1.0
    charge = 0.0
    for mid, frac in ratios.items():
        m = monomer_db.get(mid, {})
        charge += frac * m.get("charge", 0)
    return charge / total


def _hydrophobe_pct(ratios: dict[str, float]) -> float:
    return sum(ratios.get(h, 0) for h in HYDROPHOBES) * 100


def _rule_based_frrw(
    ratios: dict[str, float],
    reservoir: ReservoirCard,
    concentration: float,
    mw: float,
    monomer_db: dict[str, dict],
) -> tuple[float, float]:
    """Эвристическая модель Frrw/Frro до калибровки на lab data."""
    cd = _charge_density(ratios, monomer_db)
    hydro = _hydrophobe_pct(ratios)

    frrw = 2.0 + abs(cd) * 3.5 + hydro * 0.15 + concentration * 2.0
    frrw *= 1.0 + max(0, reservoir.salinity_g_l - 100) / 200
    frrw *= 1.0 + max(0, reservoir.temperature_c - 90) / 100

    if reservoir.lithology == "sandstone" and cd < 0:
        frrw *= 1.15
    if reservoir.wettability == "oil_wet":
        frrw *= 0.85

    frro = 1.2 + hydro * 0.08 + concentration * 0.5
    if mw > 1500:
        frro *= 1.1
    if reservoir.permeability_md < 200:
        frro *= 1.15

    return round(frrw, 2), round(frro, 2)


def _composite_score(frrw: float, frro: float, cost_index: float, available_rf: bool) -> float:
    selectivity = frrw / max(frro, 0.5)
    score = selectivity * 10 - cost_index * 2
    if available_rf:
        score += 5
    return round(score, 2)


def generate_recipe_grid(
    reservoir: ReservoirCard,
    n_candidates: int = 15,
    seed: int = 42,
) -> list[RecipeCandidate]:
    mono_data = load_json("monomers.json")
    monomers = {m["id"]: m for m in mono_data["monomers"]}
    templates = mono_data["recipe_templates"]

    rng = random.Random(seed)
    candidates: list[RecipeCandidate] = []

    am_variants = [
        {"AM": 0.65, "AMPS": 0.30, "C12AM": 0.05},
        {"AM": 0.70, "AMPS": 0.25, "C12AM": 0.05},
        {"AM": 0.60, "AMPS": 0.35, "C12AM": 0.05},
        {"AM": 0.55, "AMPS": 0.35, "NVP": 0.10},
        {"AM": 0.50, "AMPS": 0.40, "ATAC": 0.10},
        {"AM": 0.65, "AMPS": 0.20, "C18AM": 0.05, "NVP": 0.10},
    ]
    mw_list = [800, 1000, 1200, 1500, 2000]
    conc_list = [0.3, 0.5, 0.7, 0.8]

    idx = 0
    for ratios in am_variants:
        for mw, conc in itertools.product(mw_list[:3], conc_list[:2]):
            if idx >= n_candidates:
                break
            frrw, frro = _rule_based_frrw(ratios, reservoir, conc, mw, monomers)
            cost = sum(monomers[k]["cost_index"] * v for k, v in ratios.items() if k in monomers)
            avail = all(monomers.get(k, {}).get("available_rf", True) for k in ratios)
            score = _composite_score(frrw, frro, cost, avail)
            candidates.append(
                RecipeCandidate(
                    recipe_id=f"RPM-{idx+1:03d}",
                    name_ru=f"RPM copolymer #{idx+1}",
                    track="Track 1",
                    monomer_ratios=ratios,
                    target_mw_kda=float(mw),
                    concentration_pct=conc,
                    charge_density=round(_charge_density(ratios, monomers), 3),
                    hydrophobe_pct=round(_hydrophobe_pct(ratios), 2),
                    predicted_frrw=frrw,
                    predicted_frro=frro,
                    predicted_score=score,
                    hypothesis="A",
                )
            )
            idx += 1

    for tmpl in templates:
        if tmpl["track"] != "rpm_track1" and len(candidates) < n_candidates:
            ratios = tmpl["monomer_ratios"]
            mw = rng.choice(mw_list)
            conc = rng.choice(conc_list)
            frrw, frro = _rule_based_frrw(ratios, reservoir, conc, mw, monomers)
            cost = sum(monomers[k]["cost_index"] * v for k, v in ratios.items() if k in monomers)
            avail = all(monomers.get(k, {}).get("available_rf", True) for k in ratios)
            track = "Track 2" if "thermotropic" in tmpl["track"] else "Track conditional"
            candidates.append(
                RecipeCandidate(
                    recipe_id=f"{tmpl['track'].upper()}-001",
                    name_ru=tmpl["name_ru"],
                    track=track,
                    monomer_ratios=ratios,
                    target_mw_kda=float(mw),
                    concentration_pct=conc,
                    charge_density=round(_charge_density(ratios, monomers), 3),
                    hydrophobe_pct=round(_hydrophobe_pct(ratios), 2),
                    predicted_frrw=frrw,
                    predicted_frro=frro,
                    predicted_score=_composite_score(frrw, frro, cost, avail),
                    hypothesis=tmpl.get("hypothesis", ""),
                )
            )

    candidates.sort(key=lambda c: c.predicted_score, reverse=True)
    for i, c in enumerate(candidates[:n_candidates], start=1):
        c.rank = i
    return candidates[:n_candidates]


def generate_doe_matrix(
    factors: dict[str, list[float]] | None = None,
    design: str = "box_behnken",
) -> list[dict[str, float]]:
    """Генерация DoE-матрицы для лабораторной оптимизации."""
    if factors is None:
        factors = {
            "polymer_conc_pct": [0.3, 0.5, 0.8],
            "crosslinker_ppm": [50, 150, 300],
            "salinity_match": [0, 1],
            "temperature_c": [80, 100],
            "hydrophobe_mol_pct": [3, 5, 8],
        }

    if design == "full_factorial":
        keys = list(factors.keys())
        combos = list(itertools.product(*[factors[k] for k in keys]))
        return [dict(zip(keys, combo)) for combo in combos]

    # Reduced Box-Behnken-like subset (15 runs)
    keys = list(factors.keys())
    runs: list[dict[str, float]] = []
    mid = {k: factors[k][len(factors[k]) // 2] for k in keys}
    runs.append(dict(mid))

    for i, key in enumerate(keys):
        for level in factors[key]:
            run = dict(mid)
            run[key] = level
            runs.append(run)

    # Deduplicate
    seen: set[tuple] = set()
    unique: list[dict[str, float]] = []
    for run in runs:
        t = tuple(sorted(run.items()))
        if t not in seen:
            seen.add(t)
            unique.append(run)
    return unique[:25]


def train_ml_ranker(lab_data: list[dict], target: str = "frrw"):
    """Калибровка ML-модели на результатах лаборатории (Phase 2).

    Требует scikit-learn. При недоступности возвращает None.
    """
    if len(lab_data) < 5:
        return None

    try:
        import numpy as np
        from sklearn.ensemble import GradientBoostingRegressor
    except ImportError:
        return None

    feature_cols = [
        "charge_density",
        "hydrophobe_pct",
        "concentration_pct",
        "target_mw_kda",
        "salinity_g_l",
        "temperature_c",
    ]
    X = np.array([[row.get(c, 0) for c in feature_cols] for row in lab_data])
    y = np.array([row[target] for row in lab_data])

    model = GradientBoostingRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    return model
