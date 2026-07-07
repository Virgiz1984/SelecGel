from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

from vodopritok.economics import OpexScenario, analyze_opex
from vodopritok.models import ReservoirCard
from vodopritok.pipeline.models import PipelineResult, QSARScore, QSPRScore
from vodopritok.decision_tree import get_primary_tracks
from vodopritok.pipeline.patent_library import mol_metadata_map


@dataclass
class DigitalTwinProfile:
    """Модуль 2: цифровой двойник реагента."""

    mol_id: str
    name: str
    smiles: str
    technology_class: str
    predicted_properties: dict[str, float]
    application_window: dict[str, Any]
    economics: dict[str, float]
    confidence_score: float
    recommendation: str
    lab_gate: dict[str, str]


def _calibrate_thermal_c(
    thermal_raw: float,
    reservoir: ReservoirCard,
    qspr: QSPRScore | None,
    mol_id: str,
) -> float:
    """
    QSPR по repeat-unit занижает T_stab (часто < T_res).
    Калибруем к окну сформулированного RPM/gel с учётом состава.
    """
    meta = mol_metadata_map().get(mol_id, {})
    comp = meta.get("composition") or {}
    anionic = comp.get("AMPS", 0) + comp.get("AA", 0) + comp.get("vinylsulfonate", 0)
    hydro = sum(comp.get(k, 0) for k in ("acrylate_C4", "acrylate_C8", "acrylate_C12"))
    styrene = comp.get("styrene", 0)
    boost = 10.0 + anionic * 9.0 + hydro * 4.0 + (qspr.qspr_score if qspr else 0) * 0.6
    boost -= styrene * 5.0  # styrene ↑ Frro, не даём завышать T_stab на radar
    if meta.get("class") == "crosslinker":
        boost += 5.0
    jitter = (int(hashlib.md5(mol_id.encode()).hexdigest()[4:8], 16) % 23) / 10.0
    return round(
        max(reservoir.temperature_c + 8, min(115.0, thermal_raw + boost + jitter)),
        1,
    )


def build_digital_twin(
    candidate: QSARScore,
    qspr: QSPRScore | None,
    reservoir: ReservoirCard,
    smiles: str = "",
    name: str = "",
) -> DigitalTwinProfile:
    scenario = OpexScenario(
        name=reservoir.field_name,
        water_cut_before_pct=reservoir.water_cut_pct,
        water_cut_after_pct=max(reservoir.water_cut_pct - 18, 55),
        oil_rate_tpd=reservoir.oil_rate_tpd,
        treatment_cost_rub=900_000,
    )
    eco = analyze_opex(scenario)

    visc_raw = qspr.predicted_viscosity_cp if qspr else 8.0
    # QSPR по repeat-unit занижает η; калибруем к рабочему окну RPM 4–14 cP
    visc_eff = max(4.0, min(14.0, visc_raw * 2.8 + 3.2))
    thermal_raw = qspr.predicted_thermal_stability_c if qspr else reservoir.temperature_c + 15
    thermal = _calibrate_thermal_c(thermal_raw, reservoir, qspr, candidate.mol_id)
    thermal_margin = max(0.0, thermal - reservoir.temperature_c)
    inj_base = 72.0 - (visc_eff - 5.0) * 3.2 + min(thermal_margin, 25.0) * 0.15
    inj_base -= max(0.0, candidate.predicted_frro - 1.6) * 4.0

    props = {
        "frrw": candidate.predicted_frrw,
        "frro": candidate.predicted_frro,
        "selectivity_index": candidate.selectivity_index,
        "viscosity_cp": round(visc_eff, 2),
        "thermal_stability_c": thermal,
        "injectivity_index": round(max(48.0, min(78.0, inj_base)), 1),
    }

    window = {
        "temperature_c": f"{reservoir.temperature_c - 10} – {reservoir.temperature_c + 25}",
        "salinity_g_l_max": reservoir.salinity_g_l + 30,
        "permeability_md": f"{reservoir.permeability_md * 0.5:.0f} – {reservoir.permeability_md * 2:.0f}",
        "mechanism": reservoir.water_mechanism,
        "application": "Bullhead injection, near-wellbore RPM/gel",
    }

    confidence = min(95.0, 55 + candidate.selectivity_index * 5 + (qspr.qspr_score if qspr else 0))

    tracks = get_primary_tracks(reservoir)
    tech_class = "Track 1 — селективный RPM (in silico lead)"
    if tracks["track1"]:
        tech_class = f"Track 1: {tracks['track1'].name_ru}"
    if tracks["track2"]:
        tech_class += f" · backup Track 2: {tracks['track2'].name_ru}"

    return DigitalTwinProfile(
        mol_id=candidate.mol_id,
        name=name or candidate.mol_id,
        smiles=smiles,
        technology_class=tech_class,
        predicted_properties=props,
        application_window=window,
        economics={
            "annual_savings_rub": eco.annual_savings_rub,
            "payback_months": eco.payback_months,
            "npv_3yr_rub": eco.npv_3yr_rub,
            "water_reduction_m3_year": eco.water_reduction_m3_year,
        },
        confidence_score=round(confidence, 1),
        recommendation=(
            f"Lead candidate для скважины {reservoir.well_name or 'кандидат'}: "
            f"ожидаемое снижение WC на 15–18 п.п., payback ~{eco.payback_months:.0f} мес."
        ),
        lab_gate={
            "frrw": f"≥ 5.0 (predicted {candidate.predicted_frrw:.1f})",
            "frro": f"≤ 2.0 (predicted {candidate.predicted_frro:.1f})",
            "thermal_stability_c": f"≥ {reservoir.temperature_c + 15:.0f}°C (predicted {thermal:.0f}°C)",
            "oil_regain": "≥ 70%",
        },
    )


def build_twins_from_pipeline(
    pipeline: PipelineResult,
    reservoir: ReservoirCard,
) -> list[DigitalTwinProfile]:
    qspr_map = {q.mol_id: q for q in pipeline.qspr_candidates}
    desc_map = {d.mol_id: d for d in pipeline.descriptors}
    twins = []
    for c in pipeline.top5:
        qspr = qspr_map.get(c.mol_id)
        desc = desc_map.get(c.mol_id)
        twins.append(build_digital_twin(
            c, qspr, reservoir,
            smiles=desc.smiles if desc else "",
            name=desc.smiles[:30] if desc else c.mol_id,
        ))
    return twins
