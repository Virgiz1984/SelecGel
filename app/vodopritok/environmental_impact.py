"""Экологический эффект технологии ОВП — производные от OPEX и HSE-профиля track."""

from __future__ import annotations

from typing import Any

# Прокси-коэффициенты для демо (не LCA): подъём + подготовка/сброс воды.
LIFT_KWH_PER_M3 = 1.05
GRID_CO2_KG_PER_KWH = 0.45
DISPOSAL_CO2_KG_PER_M3 = 0.85

HSE_PROFILES: dict[str, dict[str, Any]] = {
    "hrpm": {
        "tier": "medium",
        "label": "Средний HSE-профиль (pre-polymerized RPM)",
        "notes": [
            "Контроль residual monomer (AM/AMPS) по MSDS",
            "Low-toxic organic crosslinkers вместо Cr³⁺",
            "Малый объём закачки vs bulk gel",
        ],
        "score_bonus": 18,
    },
    "cationic_rpm": {
        "tier": "medium",
        "label": "Средний HSE-профиль (катионный RPM)",
        "notes": [
            "Совместимость с пластовой водой и демульсifier",
            "Локальный синтез мономеров — меньше логистики",
        ],
        "score_bonus": 17,
    },
    "thermotropic_mega": {
        "tier": "low",
        "label": "Низкий хим. след (термотропный gel, Track 2)",
        "notes": [
            "Меньше полимерной нагрузки vs классический bulk gel",
            "Триггер по T пласта — точечная закачка",
        ],
        "score_bonus": 24,
    },
    "hths_pei_gel": {
        "tier": "medium",
        "label": "Средний HSE (PEI + nano-SiO₂)",
        "notes": [
            "Green nano-SiO₂ vs legacy formulations",
            "HSE review перед закачкой обязателен",
        ],
        "score_bonus": 16,
    },
    "ppg": {
        "tier": "medium",
        "label": "Средний HSE (PPG / particulate)",
        "notes": [
            "Контроль размера частиц и утилизации suspenzii",
            "Подходит при каналах — меньше хим. объёма vs RPM flood",
        ],
        "score_bonus": 15,
    },
    "rppg": {
        "tier": "medium",
        "label": "Средний HSE (RPPG)",
        "notes": ["План утилизации остатков suspenzii после ОПР"],
        "score_bonus": 14,
    },
}

DEFAULT_HSE = {
    "tier": "medium",
    "label": "HSE-профиль уточняется по lead recipe",
    "notes": ["MSDS lead formulation", "План слива/утилизации остатков раствора"],
    "score_bonus": 15,
}


def build_environmental_impact(
    analysis: Any,
    *,
    tech_id: str = "hrpm",
    wc_before: float | None = None,
    wc_after: float | None = None,
    injection_volume_m3: float = 120.0,
) -> dict[str, Any]:
    """Сводка экологического эффекта для UI и отчётов."""
    water = float(analysis.water_reduction_m3_year)
    energy_mwh = round(water * LIFT_KWH_PER_M3 / 1000, 1)
    co2_lift = water * LIFT_KWH_PER_M3 * GRID_CO2_KG_PER_KWH / 1000
    co2_disposal = water * DISPOSAL_CO2_KG_PER_M3 / 1000
    co2_avoided = round(co2_lift + co2_disposal, 1)

    wc_delta = 0.0
    if wc_before is not None and wc_after is not None:
        wc_delta = max(0.0, wc_before - wc_after)

    hse = HSE_PROFILES.get(tech_id, DEFAULT_HSE)
    water_score = min(40, wc_delta * 2.2) if wc_delta else min(40, water / 800)
    co2_score = min(35, co2_avoided * 6)
    eco_score = int(min(100, water_score + co2_score + hse["score_bonus"]))

    tier = hse["tier"]
    tier_ru = {"low": "низкий", "medium": "средний", "high": "повышенный"}.get(tier, tier)

    return {
        "water_reduction_m3_year": round(water, 0),
        "disposal_reduction_m3_year": round(water, 0),
        "energy_savings_mwh_year": energy_mwh,
        "co2_avoided_tons_year": co2_avoided,
        "injection_volume_m3": injection_volume_m3,
        "wc_reduction_pp": round(wc_delta, 1),
        "hse_tier": tier,
        "hse_tier_ru": tier_ru,
        "hse_label": hse["label"],
        "hse_notes": hse["notes"],
        "eco_score": eco_score,
        "methodology_note": (
            "Оценка демо-уровня: сокращение добычи/сброса воды → энергия подъёма и CO₂-прокси; "
            "HSE — по классу технологии (scouting). Не заменяет LCA/ОВОС."
        ),
    }
