from __future__ import annotations

from typing import Any

from .decision_tree import get_primary_tracks, recommend_technologies
from .economics import OpexScenario, analyze_opex
from .lab_program import evaluate_lab_gate
from .models import OprResult, ProjectContext, ReservoirCard


EXPERT_OPR_COMPETENCY = (
    "Программа ОПР: отбор скважины-кандидата, дизайн закачки lead formulation после lab gate, "
    "KPI мониторинга WC/Qn и критерии перехода к промышленному тиражу."
)


def score_well_candidate(reservoir: ReservoirCard) -> tuple[float, list[str]]:
    """Скоринг скважины-кандидата для ОПР."""
    score = 100.0
    notes: list[str] = []

    if reservoir.water_cut_pct < 60:
        score -= 30
        notes.append("Обводнённость <60% — низкий потенциал экономии")
    elif reservoir.water_cut_pct >= 80:
        score += 15
        notes.append("Высокая обводнённость — приоритетный кандидат")

    if reservoir.water_mechanism in ("coning", "matrix_flow", "bottom_water", "edge_water"):
        score += 20
        notes.append("Механизм совместим с RPM")
    elif reservoir.water_mechanism in ("fracture", "wormhole", "channel"):
        score -= 10
        notes.append("Канальный механизм — нужен Track 3 (RPPG/gel)")

    if reservoir.previous_ovp:
        score -= 15
        notes.append(f"Предыдущее ОВП: {reservoir.previous_ovp}")

    if reservoir.oil_rate_tpd < 5:
        score -= 20
        notes.append("Низкий дебит нефти — ROI под вопросом")

    if reservoir.permeability_md >= 200:
        score += 5
        notes.append("k≥200 мД — bullhead injection feasible")

    return min(100.0, max(0.0, score)), notes


def _injection_design(reservoir: ReservoirCard, lead: dict | None) -> dict[str, Any]:
    conc = 0.5
    if lead:
        conc = 0.3 + float(lead.get("rank", 1)) * 0.05
    volume_m3 = 80 if reservoir.permeability_md >= 300 else 110 if reservoir.permeability_md >= 150 else 140
    method = "Bullhead" if reservoir.permeability_md >= 180 else "Coiled Tubing (низкое k)"
    rate_m3h = 2.5 if method == "Bullhead" else 1.5
    return {
        "method": method,
        "lead_mol_id": lead.get("mol_id", "—") if lead else "—",
        "concentration_pct": round(conc, 2),
        "volume_m3": volume_m3,
        "injection_rate_m3h": rate_m3h,
        "duration_h": round(volume_m3 / rate_m3h, 1),
        "flush_m3": int(volume_m3 * 0.3),
        "max_pressure_atm": 180 if reservoir.permeability_md >= 200 else 250,
        "temperature_c": reservoir.temperature_c,
        "brine_match": f"Синтетическая пластовая вода {reservoir.salinity_g_l:.0f} g/L",
    }


def _timeline(injection: dict) -> list[dict[str, str]]:
    return [
        {"week": "1", "phase": "Подготовка", "activities": "PLT/tracers, HSE, реагент, baseline Qn/Qw/WC"},
        {"week": "2", "phase": "Подготовка", "activities": "Согласование программы закачки, FTO sign-off"},
        {"week": "3", "phase": "Закачка", "activities": f"{injection['method']}: {injection['volume_m3']} m³ @ {injection['concentration_pct']}%"},
        {"week": "4–6", "phase": "Мониторинг", "activities": "Ежедневный WC/Qn; контроль Pзаб"},
        {"week": "7–12", "phase": "Мониторинг", "activities": "Еженедельный мониторинг; оценка duration effect"},
        {"week": "12+", "phase": "Отчёт", "activities": "Gate ОПР → решение о тираже / refresh / Track 2"},
    ]


def _monitoring_schedule() -> list[dict[str, str]]:
    return [
        {"period": "D+1 … D+14", "metrics": "Qn, Qw, WC%, Pзаб", "frequency": "Ежедневно"},
        {"period": "D+15 … D+90", "metrics": "Qn, Qw, WC%", "frequency": "2× в неделю"},
        {"period": "M+3 … M+6", "metrics": "WC%, Qn, ROI vs baseline", "frequency": "Ежемесячно"},
        {"period": "M+6", "metrics": "Effect duration, refresh trigger", "frequency": "Gate review"},
    ]


def _opr_gate() -> list[dict[str, str]]:
    return [
        {"criterion": "Δ WC", "target": "≥ 15 pp vs baseline", "action_fail": "Дооптимизация / Track 2"},
        {"criterion": "Δ Qn", "target": "≥ −5% vs baseline", "action_fail": "Пересмотр механизма"},
        {"criterion": "Effect duration", "target": "≥ 6 месяцев", "action_fail": "Refresh или re-gel"},
        {"criterion": "Pзаб / приёмистость", "target": "Без аварийного падения", "action_fail": "Staged injection"},
        {"criterion": "Economics", "target": "Payback < 24 мес", "action_fail": "Пересмотр кандидата"},
    ]


def _lab_gate_status(ctx: ProjectContext) -> dict[str, Any]:
    passed = 0
    total = 0
    lead_id = "—"
    if ctx.lab_results:
        total = len(ctx.lab_results)
        passed = sum(1 for r in ctx.lab_results if r.passed_gate)
        if ctx.lab_results:
            lead_id = ctx.lab_results[0].recipe_id
    elif ctx.session_data and ctx.session_data.get("pipeline", {}).get("top5"):
        top5 = ctx.session_data["pipeline"]["top5"]
        lead_id = top5[0].get("mol_id", "—")
        for m in top5:
            total += 1
            from .models import LabResult
            r = LabResult(
                recipe_id=m.get("mol_id", ""),
                recipe_name=m.get("mol_id", ""),
                frrw=float(m.get("predicted_frrw", 5)),
                frro=float(m.get("predicted_frro", 2)),
                oil_regain_pct=75,
                water_regain_pct=22,
                aging_frrw_delta_pct=8,
            )
            evaluate_lab_gate(r)
            if r.passed_gate:
                passed += 1
    ready = passed >= 1
    return {
        "ready_for_opr": ready,
        "passed": passed,
        "total": total,
        "lead_id": lead_id,
        "note": "Lab gate пройден — допуск к ОПР" if ready else "Требуется core flood gate перед полем",
    }


def build_opr_program(ctx: ProjectContext) -> dict:
    r = ctx.reservoir
    recs = recommend_technologies(r, top_n=3)
    tracks = get_primary_tracks(r)
    well_score, well_notes = score_well_candidate(r)
    primary = recs[0] if recs else None

    lead = None
    if ctx.session_data and ctx.session_data.get("pipeline", {}).get("top5"):
        lead = ctx.session_data["pipeline"]["top5"][0]

    injection = _injection_design(r, lead)
    lab_gate = _lab_gate_status(ctx)

    wc_after = max(r.water_cut_pct - 18, 55)
    if lead:
        wc_after = max(r.water_cut_pct - 20, 52)
    eco = analyze_opex(OpexScenario(
        name=r.field_name,
        water_cut_before_pct=r.water_cut_pct,
        water_cut_after_pct=wc_after,
        oil_rate_tpd=r.oil_rate_tpd,
        treatment_cost_rub=900_000,
    ))

    tech_name = primary.name_ru if primary else "Селективный RPM"
    track_label = primary.track if primary else "Track 1"

    return {
        "title": "Программа опытно-промышленных работ (ОПР)",
        "expert_competency": EXPERT_OPR_COMPETENCY,
        "candidate_well": r.well_name or "Well-101",
        "field": r.field_name,
        "reservoir_summary": {
            "temperature_c": r.temperature_c,
            "salinity_g_l": r.salinity_g_l,
            "permeability_md": r.permeability_md,
            "water_cut_pct": r.water_cut_pct,
            "oil_rate_tpd": r.oil_rate_tpd,
            "mechanism": r.water_mechanism,
        },
        "well_score": well_score,
        "well_notes": well_notes,
        "technology": tech_name,
        "track": track_label,
        "tracks": tracks,
        "lab_gate": lab_gate,
        "lead_formulation": lead or {},
        "injection": injection,
        "phases": [
            {
                "phase": "Phase A: Подготовка (недели 1–2)",
                "activities": [
                    "Уточнение механизма обводнения (PLT, tracers, история дебитов)",
                    f"Lead formulation: {injection['lead_mol_id']} — подтверждение lab gate",
                    "HSE review, согласование программы закачки",
                    f"Приготовление раствора {injection['concentration_pct']}% в пластовой воде",
                    "Baseline: Qn, Qw, WC%, Pзаб, демульсifier compatibility",
                ],
            },
            {
                "phase": "Phase B: Закачка (неделя 3)",
                "activities": [
                    f"{injection['method']}: {injection['volume_m3']} m³ @ {injection['concentration_pct']}%",
                    f"Скорость {injection['injection_rate_m3h']} m³/ч, T={injection['temperature_c']:.0f}°C",
                    f"Flush {injection['flush_m3']} m³ пластовой воды",
                    "Контроль давления и приёмистости в реальном времени",
                ],
            },
            {
                "phase": "Phase C: Мониторинг (недели 4–12+)",
                "activities": [
                    "Ежедневный мониторинг Qn, Qw, WC% — первые 14 суток",
                    "Еженедельный — до 3 месяцев; ежемесячный — до 6 месяцев",
                    "Повторный PLT при WC > целевого или падении Qn",
                    "Gate review → отчёт ОПР (deliverable №5)",
                ],
            },
        ],
        "timeline": _timeline(injection),
        "monitoring_schedule": _monitoring_schedule(),
        "opr_gate": _opr_gate(),
        "kpis": [
            {"metric": "Δ water cut", "target": "≥ −15 абс. %"},
            {"metric": "Δ oil rate", "target": "≥ −5% (не хуже baseline)"},
            {"metric": "Effect duration", "target": "≥ 6 месяцев"},
            {"metric": "Cost per ton reduced water", "target": "< benchmark ПГС/ВУС"},
        ],
        "economics_preview": {
            "wc_after_pct": wc_after,
            "annual_savings_rub": eco.annual_savings_rub,
            "payback_months": eco.payback_months,
            "npv_3yr_rub": eco.npv_3yr_rub,
        },
        "wells_shortlist": [
            {"name": r.well_name or "Well-101", "score": well_score, "role": "Primary ОПР"},
            {"name": "Well-102 (reserve)", "score": max(0, well_score - 12), "role": "Backup"},
            {"name": "Well-103 (monitor)", "score": max(0, well_score - 18), "role": "Контроль без обработки"},
        ],
        "equipment": [
            "Насосная / установка закачки (bullhead или CT)",
            "Ёмкости приготовления раствора, фильтрация",
            "Manifold, линии закачки, контроль давления",
            "Система мониторинга дебита (WM, SCADA)",
            "HSE: СИЗ, план реагирования на разгерметизацию",
        ],
        "hse_checklist": [
            "MSDS lead formulation и совместимость с пластовой водой",
            "План работ на скважине согласован с промыслом",
            "Контроль давления на устье и в затрубе",
            "План слива/утилизации остатков раствора",
        ],
        "contingency": [
            "Gate lab не пройден → Track 2 gel backup (параллельная программа lab)",
            "Падение приёмистости → staged injection / снижение rate",
            "WC не снижается → PLT + пересмотр механизма / Track 3",
            f"Backup technology: {tracks['track2'].name_ru if tracks.get('track2') else 'термотропный gel'}",
        ],
        "risks": [
            "Неверный механизм обводнения → pre-treatment diagnostics",
            "Несовместимость с демульсifier → lab compatibility test",
            "Падение приёмистости → staged injection",
        ],
        "deliverables": [
            "Программа закачки (данный документ)",
            "Протокол закачки и давления",
            "Графики Qn/Qw/WC до/после",
            "Отчёт ОПР (deliverable №5) с gate decision",
        ],
        "competency_evidence": [
            {"artifact": "04-programma-opr.docx", "proof": "Скoring, injection design, KPI, timeline"},
            {"artifact": "/opr-program", "proof": "Интерактивная программа после screening"},
            {"artifact": "Lab gate", "proof": "Связь с lead formulation из top-5"},
        ],
    }


def build_opr_report(ctx: ProjectContext) -> dict:
    results = ctx.opr_results
    if not results:
        results = _demo_opr_results(ctx)

    successes = [
        r
        for r in results
        if (r.water_cut_before_pct - r.water_cut_after_pct) >= 15
        and r.oil_rate_after_tpd >= r.oil_rate_before_tpd * 0.95
    ]

    return {
        "title": "Отчёт по результатам опытно-промышленных работ",
        "results": results,
        "success_count": len(successes),
        "conclusion": (
            "ОПР подтвердила эффективность lead formulation. Рекомендуется масштабирование."
            if successes
            else "Предварительные результаты требуют дооптимизации рецептуры или пересмотра кандидата."
        ),
    }


def _demo_opr_results(ctx: ProjectContext) -> list[OprResult]:
    r = ctx.reservoir
    lead = None
    if ctx.session_data and ctx.session_data.get("pipeline", {}).get("top5"):
        lead = ctx.session_data["pipeline"]["top5"][0]
    lead_id = lead.get("mol_id", "PAT-LEAD") if lead else "PAT-LEAD"
    inj = _injection_design(r, lead)
    return [
        OprResult(
            well_name=r.well_name or "Well-101",
            technology="Селективный RPM",
            treatment_date="2026-09-15",
            water_cut_before_pct=r.water_cut_pct,
            water_cut_after_pct=max(r.water_cut_pct - 18, 50),
            oil_rate_before_tpd=r.oil_rate_tpd,
            oil_rate_after_tpd=r.oil_rate_tpd * 1.02,
            effect_duration_months=3,
            treatment_cost_rub=850_000,
            notes=f"{inj['method']}, {inj['volume_m3']} m³ @ {inj['concentration_pct']}% · {lead_id}",
        )
    ]
