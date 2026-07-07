"""Данные для Chart.js визуализаций."""

from __future__ import annotations

from typing import Any


def funnel_from_stages(total: int, stages: list[Any], top_n: int) -> dict:
    qspr_out = stages[1].output_count if len(stages) > 1 else top_n * 10
    return {
        "labels": ["Патентная библиотека", "После QSPR (−70%)", "Top-5 (QSAR)"],
        "values": [total, qspr_out, top_n],
        "colors": ["#3b82f6", "#8b5cf6", "#22c55e"],
    }


def top5_chart(top5: list[Any]) -> dict:
    return {
        "labels": [m.mol_id if hasattr(m, "mol_id") else m["mol_id"] for m in top5],
        "frrw": [float(m.predicted_frrw if hasattr(m, "predicted_frrw") else m["predicted_frrw"]) for m in top5],
        "frro": [float(m.predicted_frro if hasattr(m, "predicted_frro") else m["predicted_frro"]) for m in top5],
        "selectivity": [float(m.selectivity_index if hasattr(m, "selectivity_index") else m.get("selectivity_index", 0)) for m in top5],
    }


def tech_scores_chart(recommendations: list[Any]) -> dict:
    return {
        "labels": [r.name_ru[:30] for r in recommendations],
        "scores": [float(r.score) for r in recommendations],
    }


def qsprpred_chart(validation: dict | None) -> dict | None:
    if not validation:
        return None
    report = validation.get("report")
    if not report or not report.rows:
        return None
    frrw_rows = [r for r in report.rows if r.property_name == "frrw"]
    if not frrw_rows:
        return None
    return {
        "labels": [r.mol_id for r in frrw_rows],
        "predicted": [r.predicted for r in frrw_rows],
        "observed": [r.observed for r in frrw_rows],
    }


def _norm_frrw_score(frrw: float) -> float:
    """Frrw 3.5→0, 6.5→10; gate 5.0 ≈ 5 баллов."""
    return round(max(0.0, min(10.0, (frrw - 3.5) / 3.0 * 10)), 2)


def _norm_oil_score(frro: float) -> float:
    """
    Меньше Frro — лучше. Gate Frro≤2.0 ≈ 4.2 балла.
    Frro>2.5 не обнуляем (пол 0.5), чтобы профиль не «схлопывался» на radar.
    """
    lo, gate_frro, hi = 1.35, 2.0, 3.0
    frro = max(lo, min(hi, frro))
    if frro <= gate_frro:
        return round(4.2 + (gate_frro - frro) / (gate_frro - lo) * 5.8, 2)
    return round(max(0.5, 4.2 - (frro - gate_frro) / (hi - gate_frro) * 3.7), 2)


def _norm_selectivity_score(sel: float) -> float:
    return round(max(0.0, min(10.0, (sel - 1.8) / 2.0 * 10)), 2)


def _norm_injectivity_score(inj: float) -> float:
    return round(max(0.0, min(10.0, (inj - 48.0) / 30.0 * 10)), 2)


def _norm_thermal_score(thermal_c: float, reservoir_temp_c: float = 85.0) -> float:
    """Запас по T относительно пласта; gate ~100°C → ~6/10 при T_res=85."""
    margin = thermal_c - reservoir_temp_c
    return round(max(0.0, min(10.0, margin / 25.0 * 10)), 2)


RADAR_LABELS = [
    "Frrw (вода)",
    "Нефть (Frro↓)",
    "Селективность",
    "Инжектируемость",
    "Термостойкость",
]

RADAR_GATE = [5.0, 4.2, 3.5, 6.0, 6.0]


def _injectivity_from_viscosity(visc_eff: float, frro: float) -> float:
    inj = 72.0 - (visc_eff - 5.0) * 3.2 - max(0.0, frro - 1.6) * 4.0
    return round(max(48.0, min(78.0, inj)), 1)


def radar_profile_from_props(
    props: dict[str, float],
    reservoir_temp_c: float = 85.0,
) -> dict[str, Any]:
    frrw = float(props.get("frrw", 5.0))
    frro = max(float(props.get("frro", 1.8)), 0.1)
    sel = float(props.get("selectivity_index", frrw / frro))
    inj = float(props.get("injectivity_index", 65.0))
    thermal = float(props.get("thermal_stability_c", reservoir_temp_c + 10))

    values = [
        _norm_frrw_score(frrw),
        _norm_oil_score(frro),
        _norm_selectivity_score(sel),
        _norm_injectivity_score(inj),
        _norm_thermal_score(thermal, reservoir_temp_c),
    ]
    raw = {
        "frrw": round(frrw, 2),
        "frro": round(frro, 2),
        "selectivity_index": round(sel, 2),
        "injectivity_index": round(inj, 1),
        "thermal_stability_c": round(thermal, 1),
    }
    summary = [
        {
            "axis": label,
            "score": score,
            "gate": gate,
            "pass": score >= gate,
        }
        for label, score, gate in zip(RADAR_LABELS, values, RADAR_GATE)
    ]
    return {"values": values, "raw": raw, "summary": summary}


def radar_profile_from_lab_row(row: dict, reservoir_temp_c: float = 85.0) -> dict[str, Any]:
    visc_raw = float(row.get("viscosity_cp") or 6.0)
    visc_eff = max(4.0, min(14.0, visc_raw))
    frro = float(row["frro"])
    props = {
        "frrw": float(row["frrw"]),
        "frro": frro,
        "selectivity_index": float(row["frrw"]) / max(frro, 0.1),
        "injectivity_index": _injectivity_from_viscosity(visc_eff, frro),
        "thermal_stability_c": float(row.get("thermal_stability_c") or reservoir_temp_c + 12),
    }
    return radar_profile_from_props(props, reservoir_temp_c)


def build_twin_radar_bundle(
    twins: list[Any],
    lab_rows: list[dict] | None = None,
    reservoir_temp_c: float = 85.0,
) -> dict[str, Any]:
    """Интерактивный radar: Top-5 in silico + опционально lab overlay по rank."""
    candidates: list[dict[str, Any]] = []
    for i, twin in enumerate(twins):
        p = twin.predicted_properties if hasattr(twin, "predicted_properties") else twin["predicted_properties"]
        profile = radar_profile_from_props(p, reservoir_temp_c)
        candidates.append({
            "mol_id": twin.mol_id if hasattr(twin, "mol_id") else twin["mol_id"],
            "rank": i + 1,
            "default_visible": i == 0,
            **profile,
        })

    lab_by_rank = {int(r["rank"]): r for r in (lab_rows or []) if r.get("rank")}
    lab_profiles: list[dict[str, Any]] = []
    for cand in candidates:
        row = lab_by_rank.get(cand["rank"])
        if not row:
            continue
        profile = radar_profile_from_lab_row(row, reservoir_temp_c)
        lab_profiles.append({
            "rank": cand["rank"],
            "mol_id": row.get("mol_id") or cand["mol_id"],
            "notes": row.get("notes", ""),
            **profile,
        })

    return {
        "labels": RADAR_LABELS,
        "gate": RADAR_GATE,
        "candidates": candidates,
        "lab": lab_profiles,
        "has_lab": bool(lab_profiles),
        "reservoir_temp_c": reservoir_temp_c,
    }


def twin_radar(twin: Any, reservoir_temp_c: float = 85.0) -> dict:
    p = twin.predicted_properties if hasattr(twin, "predicted_properties") else twin["predicted_properties"]
    profile = radar_profile_from_props(p, reservoir_temp_c)
    return {
        "labels": RADAR_LABELS,
        "values": profile["values"],
        "gate": RADAR_GATE,
        "raw": profile["raw"],
        "summary": profile["summary"],
    }


def economics_chart(twin: Any) -> dict:
    e = twin.economics if hasattr(twin, "economics") else twin["economics"]
    return {
        "labels": ["Экономия/год", "NPV 3 года", "Payback мес."],
        "values": [
            float(e.get("annual_savings_rub", 0)) / 1_000_000,
            float(e.get("npv_3yr_rub", 0)) / 1_000_000,
            float(e.get("payback_months", 0)),
        ],
        "units": ["млн ₽", "млн ₽", "мес."],
    }


def qsprpred_comparison_metrics(report) -> dict | None:
    if not report or not report.metrics.get("frrw"):
        return None
    m = report.metrics["frrw"]
    return {"rmse": m.get("rmse"), "mae": m.get("mae"), "r2": m.get("r2"), "mape": m.get("mape")}


def build_qsprpred_comparison(before_report, after_report) -> dict:
    b = qsprpred_comparison_metrics(before_report) or {}
    a = qsprpred_comparison_metrics(after_report) or {}
    return {
        "before": b,
        "after": a,
        "improved": (a.get("mape", 999) < b.get("mape", 999)) if a and b else False,
    }


def qsprpred_mape_chart(comparison: dict | None) -> dict | None:
    if not comparison or not comparison.get("before") or not comparison.get("after"):
        return None
    return {
        "labels": ["До lab CSV", "После lab CSV"],
        "values": [
            float(comparison["before"].get("mape", 0)),
            float(comparison["after"].get("mape", 0)),
        ],
    }


def build_screening_charts(result, recommendations, validation=None, comparison=None) -> dict:
    charts = {
        "funnel": funnel_from_stages(result.total_input, result.stages, len(result.top5)),
        "top5": top5_chart(result.top5),
        "tech": tech_scores_chart(recommendations),
        "qsprpred": qsprpred_chart(validation),
        "stages": stages_chart([
            {"name": s.name, "tool": s.tool, "output_count": s.output_count}
            for s in result.stages
        ]),
    }
    mape = qsprpred_mape_chart(comparison)
    if mape:
        charts["qsprpred_mape"] = mape
    return charts


def build_home_charts(session: dict | None, recommendations: list | None = None) -> dict | None:
    charts: dict = {}
    if session and session.get("pipeline"):
        p = session["pipeline"]
        stages_raw = p.get("stages", [])

        class S:
            def __init__(self, d):
                self.output_count = d.get("output_count", 0)

        stages = [S(s) for s in stages_raw]
        top5 = p.get("top5", [])
        charts["funnel"] = funnel_from_stages(p.get("total_input", 500), stages, len(top5))
        if top5:
            charts["top5"] = top5_chart(top5)
        charts["stages"] = stages_chart(stages_raw)
    if recommendations:
        charts["tech"] = tech_scores_chart(recommendations)
    return charts or None


def stages_chart(stages: list[Any]) -> dict:
    return {
        "labels": [s.get("name", s.get("tool", "Stage"))[:22] for s in stages],
        "values": [int(s.get("output_count", 0)) for s in stages],
    }


def deliverables_chart(docx_count: int, total: int = 6) -> dict:
    done = min(docx_count, total)
    return {
        "labels": ["Готово", "Не создано"],
        "values": [done, max(0, total - done)],
        "colors": ["#22c55e", "#374151"],
    }


def technology_economics_chart(comparison: list[dict]) -> dict:
    return {
        "labels": [t["technology"][:18] for t in comparison],
        "capex": [t["capex_rub"] / 1_000_000 for t in comparison],
        "annual_opex": [t["annual_reagent_rub"] / 1_000_000 for t in comparison],
    }


def build_pitch_charts(session: dict | None, recommendations: list | None, reservoir=None) -> dict | None:
    charts = build_home_charts(session, recommendations) or {}
    if reservoir is not None:
        from vodopritok.economics import compare_technology_economics
        charts["tech_economics"] = technology_economics_chart(compare_technology_economics(reservoir))
    return charts or None


def build_reports_charts(session: dict | None, docx_count: int) -> dict:
    charts: dict = {"deliverables": deliverables_chart(docx_count)}
    if session and session.get("pipeline"):
        p = session["pipeline"]
        stages_raw = p.get("stages", [])

        class S:
            def __init__(self, d):
                self.output_count = d.get("output_count", 0)

        stages = [S(s) for s in stages_raw]
        top5 = p.get("top5", [])
        charts["funnel"] = funnel_from_stages(p.get("total_input", 500), stages, len(top5))
        if top5:
            charts["top5"] = top5_chart(top5)
        charts["stages"] = stages_chart(stages_raw)
    return charts
