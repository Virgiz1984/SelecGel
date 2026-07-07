from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import ReservoirCard, load_json


@dataclass
class TechnologyRecommendation:
    technology_id: str
    name_ru: str
    rank: int
    score: float
    track: str
    rationale: str
    warnings: list[str]


def _mechanism_label(mechanism_id: str) -> str:
    data = load_json("technologies.json")
    for m in data["water_mechanisms"]:
        if m["id"] == mechanism_id:
            return m["name_ru"]
    return mechanism_id


def score_technology(tech: dict, reservoir: ReservoirCard) -> tuple[float, list[str], list[str]]:
    score = 0.0
    rationale: list[str] = []
    warnings: list[str] = []

    t = reservoir.temperature_c
    if tech["temp_min_c"] <= t <= tech["temp_max_c"]:
        score += 25
        rationale.append(f"Температура {t}°C в рабочем диапазоне [{tech['temp_min_c']}–{tech['temp_max_c']}]°C")
    else:
        warnings.append(f"Температура {t}°C вне диапазона [{tech['temp_min_c']}–{tech['temp_max_c']}]°C")
        score -= 15

    sal_map = {"low": 50, "medium": 120, "medium_high": 150, "high": 180, "very_high": 220, "variable": 999}
    sal_limit = sal_map.get(tech["salinity"], 150)
    if reservoir.salinity_g_l <= sal_limit:
        score += 15
        rationale.append(f"Минерализация {reservoir.salinity_g_l} г/л совместима")
    else:
        warnings.append(f"Высокая минерализация {reservoir.salinity_g_l} г/л для {tech['name_ru']}")
        score -= 10

    perm = reservoir.permeability_md
    if tech["perm_min_md"] <= perm <= tech["perm_max_md"]:
        score += 20
        rationale.append(f"Проницаемость {perm} мД в диапазоне технологии")
    elif perm > tech["perm_max_md"]:
        warnings.append(f"Проницаемость {perm} мД выше типичного окна")
        score += 5 if tech["id"] in ("ppg", "rppg", "bulk_gel") else -10
    else:
        warnings.append(f"Проницаемость {perm} мД ниже типичного окна")
        score -= 5

    mechanism = reservoir.water_mechanism
    if mechanism in tech.get("water_mechanisms", []):
        score += 30
        rationale.append(f"Механизм «{_mechanism_label(mechanism)}» — целевой для технологии")
    elif mechanism in tech.get("not_for", []):
        score -= 25
        warnings.append(f"Механизм «{_mechanism_label(mechanism)}» — не рекомендуется")
    else:
        score += 5

    if reservoir.has_fracture and tech["id"] in ("hrpm", "cationic_rpm"):
        score -= 20
        warnings.append("Трещины/каналы снижают эффективность RPM")

    if reservoir.lithology == "carbonate" and tech["id"] == "hrpm":
        score -= 10
        warnings.append("Карбонат: RPM менее эффективен без адаптации AMPS/NVP")

    if reservoir.lithology == "carbonate" and tech["id"] in ("cationic_rpm", "ppg"):
        score += 10
        rationale.append("Технология применима для карбонатов")

    if tech["class"] == "selective":
        score += 10
        rationale.append("Селективная технология — приоритет проекта")

    if tech["trl"] >= 8:
        score += 5

    return score, rationale, warnings


def recommend_technologies(reservoir: ReservoirCard, top_n: int = 5) -> list[TechnologyRecommendation]:
    data = load_json("technologies.json")
    ranked: list[TechnologyRecommendation] = []

    for tech in data["technologies"]:
        score, rationale, warnings = score_technology(tech, reservoir)
        track = _assign_track(tech["id"])
        ranked.append(
            TechnologyRecommendation(
                technology_id=tech["id"],
                name_ru=tech["name_ru"],
                rank=0,
                score=score,
                track=track,
                rationale="; ".join(rationale),
                warnings=warnings,
            )
        )

    ranked.sort(key=lambda x: x.score, reverse=True)
    for i, rec in enumerate(ranked[:top_n], start=1):
        rec.rank = i
    return ranked[:top_n]


def _assign_track(tech_id: str) -> str:
    if tech_id in ("hrpm", "cationic_rpm"):
        return "Track 1 (primary RPM)"
    if tech_id == "thermotropic_mega":
        return "Track 2 (backup thermotropic)"
    if tech_id in ("ppg", "rppg"):
        return "Track 3 (conditional fracture)"
    if tech_id == "hths_pei_gel":
        return "Track conditional (HTHS)"
    return "Alternative"


def get_primary_tracks(reservoir: ReservoirCard) -> dict[str, TechnologyRecommendation | None]:
    recs = recommend_technologies(reservoir, top_n=9)
    tracks = {"track1": None, "track2": None, "track3": None}
    for rec in recs:
        if "Track 1" in rec.track and tracks["track1"] is None:
            tracks["track1"] = rec
        elif "Track 2" in rec.track and tracks["track2"] is None:
            tracks["track2"] = rec
        elif "Track 3" in rec.track and tracks["track3"] is None:
            tracks["track3"] = rec
    return tracks


def rd_track_strategy(reservoir: ReservoirCard) -> dict[str, Any]:
    """Primary / backup / conditional tracks для UI и one-pager."""
    tracks = get_primary_tracks(reservoir)
    return {
        "track1": tracks["track1"],
        "track2": tracks["track2"],
        "track3": tracks["track3"],
        "screening_note": (
            "In silico 500→top-5 на стенде — библиотека Track 1 (RPM/copolymer). "
            "Track 2 синтезируется параллельно в lab Phase 1 (2–3 композиции)."
        ),
    }


def decision_tree_text(reservoir: ReservoirCard) -> str:
    mech = _mechanism_label(reservoir.water_mechanism)
    lines = [
        "Дерево решений для выбора технологии ОВП",
        "=" * 50,
        f"Механизм обводнения: {mech}",
        f"Литология: {reservoir.lithology}, T={reservoir.temperature_c}°C, k={reservoir.permeability_md} мД",
        "",
    ]
    recs = recommend_technologies(reservoir, top_n=3)
    for rec in recs:
        lines.append(f"{rec.rank}. {rec.name_ru} (score={rec.score:.0f}, {rec.track})")
        lines.append(f"   {rec.rationale}")
        for w in rec.warnings:
            lines.append(f"   ⚠ {w}")
        lines.append("")
    return "\n".join(lines)
