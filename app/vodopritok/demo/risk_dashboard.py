"""Risk dashboard — оценка готовности проекта для заказчика."""

from __future__ import annotations

from typing import Any

from vodopritok.decision_tree import TechnologyRecommendation
from vodopritok.demo.context_builder import build_fto_rows
from vodopritok.economics import OpexScenario, analyze_opex
from vodopritok.models import ReservoirCard
from vodopritok.opr_program import score_well_candidate


def _level(score: float) -> str:
    if score >= 75:
        return "low"
    if score >= 50:
        return "medium"
    return "high"


def build_risk_dashboard(
    reservoir: ReservoirCard,
    top5: list[dict],
    recommendations: list[TechnologyRecommendation],
    stages: list[dict] | None = None,
    validation_metrics: dict | None = None,
    fto_rows: list[dict] | None = None,
) -> dict[str, Any]:
    well_score, well_notes = score_well_candidate(reservoir)
    tech_score = recommendations[0].score if recommendations else 50.0

    gate_pass = sum(
        1 for m in top5
        if float(m.get("predicted_frrw", 0)) >= 5 and float(m.get("predicted_frro", 99)) <= 2
    )
    lab_readiness = min(100, 40 + gate_pass * 12 + (20 if validation_metrics else 0))

    fto_rows = fto_rows or build_fto_rows(top5)
    fto_issues = sum(1 for r in fto_rows if r.get("risk") != "low")
    fto_score = max(0, 100 - fto_issues * 25)

    wc_after = max(reservoir.water_cut_pct - 18, 55)
    opex = analyze_opex(OpexScenario(
        name=reservoir.field_name,
        water_cut_before_pct=reservoir.water_cut_pct,
        water_cut_after_pct=wc_after,
        oil_rate_tpd=reservoir.oil_rate_tpd,
    ))
    econ_score = min(100, 30 + (opex.payback_months < 24) * 40 + (opex.npv_3yr_rub > 0) * 30)

    ml_notes = []
    ml_score = 85
    if stages:
        for s in stages:
            tool = s.get("tool", "")
            if "fallback" in tool.lower():
                ml_score -= 15
                ml_notes.append(f"{s.get('name')}: fallback mode")

    overall = round((well_score + tech_score + lab_readiness + fto_score + econ_score + ml_score) / 6, 0)

    return {
        "overall_score": overall,
        "overall_level": _level(overall),
        "cards": [
            {
                "id": "well",
                "title": "Скважина-кандидат",
                "score": round(well_score, 0),
                "level": _level(well_score),
                "detail": f"Score {well_score:.0f}/100",
                "notes": well_notes[:2],
            },
            {
                "id": "tech",
                "title": "Track технологии",
                "score": round(tech_score, 0),
                "level": _level(tech_score),
                "detail": recommendations[0].name_ru[:40] if recommendations else "—",
                "notes": [recommendations[0].track] if recommendations else [],
            },
            {
                "id": "lab",
                "title": "Lab readiness",
                "score": round(lab_readiness, 0),
                "level": _level(lab_readiness),
                "detail": f"Gate forecast: {gate_pass}/{len(top5)}",
                "notes": ["Frrw≥5, Frro≤2"],
            },
            {
                "id": "fto",
                "title": "FTO / патенты",
                "score": round(fto_score, 0),
                "level": _level(fto_score),
                "detail": f"Review needed: {fto_issues}",
                "notes": [],
            },
            {
                "id": "econ",
                "title": "Экономика OPEX",
                "score": round(econ_score, 0),
                "level": _level(econ_score),
                "detail": f"Payback {opex.payback_months:.0f} мес · NPV {opex.npv_3yr_rub/1e6:.1f} млн ₽",
                "notes": [],
            },
            {
                "id": "ml",
                "title": "ML pipeline",
                "score": round(ml_score, 0),
                "level": _level(ml_score),
                "detail": "Калибровка lab CSV повышает точность",
                "notes": ml_notes or ["Production models active"],
            },
        ],
        "opex_preview": {
            "annual_savings_rub": opex.annual_savings_rub,
            "payback_months": opex.payback_months,
            "npv_3yr_rub": opex.npv_3yr_rub,
            "wc_after_pct": wc_after,
        },
    }
