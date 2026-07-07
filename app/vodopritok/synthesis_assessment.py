"""Оценка возможности синтеза новых рецептур с использованием хемоинформатики."""

from __future__ import annotations

from typing import Any

from .cheminformatics import RecipeCandidate, generate_doe_matrix
from .demo.context_builder import build_fto_rows, top5_to_recipe_candidates
from .models import ProjectContext, ReservoirCard, load_json


EXPERT_CHEMINFORMATICS_COMPETENCY = (
    "Оценка возможности синтеза новых рецептур с использованием хемоинформатики: "
    "патентная библиотека → дескрипторы → QSPR/QSAR → FTO → очередь синтеза и DoE."
)


def build_cheminformatics_methodology() -> list[dict[str, str]]:
    return [
        {
            "step": "1",
            "title": "Карточка пласта",
            "detail": "T, salinity, Ca²⁺, lithology, wettability → ограничения на мономеры и MW",
        },
        {
            "step": "2",
            "title": "Библиотека building blocks",
            "detail": "500 патентных SMILES + monomers.json (AM, AMPS, NVP, hydrophobes, crosslinkers)",
        },
        {
            "step": "3",
            "title": "Descriptors + QSPR",
            "detail": "RDKit/molfeat → вязкость, термостойкость; фильтр ~70% кандидатов",
        },
        {
            "step": "4",
            "title": "QSAR селективность",
            "detail": "Physics-informed Frrw/Frro ranking → top-5 для лабораторного синтеза",
        },
        {
            "step": "5",
            "title": "FTO + feasibility",
            "detail": "Патентный риск, доступность мономеров РФ, сложность синтеза MW",
        },
        {
            "step": "6",
            "title": "DoE lab matrix",
            "detail": "10–15 рецептур вместо 100+; response surface → lead formulation",
        },
    ]


def _monomer_db() -> dict[str, dict]:
    data = load_json("monomers.json")
    return {m["id"]: m for m in data["monomers"]}


def _score_synthesis_feasibility(
    candidate: RecipeCandidate,
    reservoir: ReservoirCard,
    fto_risk: str = "low",
) -> dict[str, Any]:
    monomers = _monomer_db()
    ratios = candidate.monomer_ratios

    rf_ok = all(monomers.get(k, {}).get("available_rf", True) for k in ratios if k in monomers)
    import_deps = [k for k in ratios if k in monomers and not monomers[k].get("available_rf", True)]
    exotic = [k for k in ratios if k not in monomers]
    monomer_score = 92 if rf_ok and not exotic else max(45, 92 - 12 * len(import_deps) - 4 * len(exotic))

    mw = candidate.target_mw_kda
    mw_score = max(55, min(92, 94 - abs(mw - 1280) / 22))

    cd = abs(candidate.charge_density)
    salinity_ok = reservoir.salinity_g_l <= 160 or cd >= 0.25
    thermal_ok = reservoir.temperature_c <= 95 or candidate.hydrophobe_pct <= 12
    hydro_penalty = max(0, candidate.hydrophobe_pct - 10) * 0.8
    process_score = max(55, (85 if salinity_ok and thermal_ok else 65) - hydro_penalty)

    if fto_risk == "low":
        fto_score = 90
    elif "medium" in fto_risk:
        fto_score = 62
    elif fto_risk == "review":
        fto_score = 50
    else:
        fto_score = 75

    qsar_bonus = 0.0
    if candidate.predicted_frrw >= 5.0 and candidate.predicted_frro <= 2.0:
        qsar_bonus += 5.0
    qsar_bonus += min(5.0, max(-2.0, (candidate.predicted_frrw - 4.8) * 2.5))
    qsar_bonus += min(3.0, max(-3.0, (2.1 - candidate.predicted_frro) * 2.0))
    qsar_bonus += min(4.0, candidate.predicted_score * 0.6)
    qsar_bonus += max(0.0, (6 - candidate.rank) * 0.9)

    total = (
        monomer_score * 0.30
        + mw_score * 0.22
        + process_score * 0.18
        + fto_score * 0.18
        + qsar_bonus * 0.12
    )
    total = round(max(52, min(96, total)), 0)
    if total >= 78:
        verdict = "Рекомендован к синтезу"
        verdict_class = "ok"
    elif total >= 62:
        verdict = "Условно — синтез с оговорками"
        verdict_class = "warn"
    else:
        verdict = "Требует доработки состава"
        verdict_class = "warn"

    notes: list[str] = []
    if exotic:
        notes.append(f"Экзотические мономеры в составе: {', '.join(exotic)} — проверить supply")
    if import_deps:
        notes.append(f"Импортные мономеры: {', '.join(import_deps)} — рассмотреть замену")
    if mw > 1500:
        notes.append("Высокий MW — удлиняет синтез и QC GPC")
    if "medium" in fto_risk or fto_risk == "review":
        notes.append("FTO review перед масштабным синтезом")
    if not notes:
        notes.append("Состав совместим с T/salinity пласта; локализация мономеров возможна")

    return {
        "recipe_id": candidate.recipe_id,
        "rank": candidate.rank,
        "name": candidate.name_ru,
        "monomers": ", ".join(f"{k}:{v:.0%}" for k, v in ratios.items()),
        "target_mw_kda": mw,
        "feasibility_score": total,
        "monomer_score": monomer_score,
        "mw_score": mw_score,
        "process_score": process_score,
        "fto_score": fto_score,
        "qsar_bonus": round(qsar_bonus, 1),
        "verdict": verdict,
        "verdict_class": verdict_class,
        "fto_risk": fto_risk,
        "notes": "; ".join(notes),
        "synthesis_route": "Radical copolymerization → dialysis → freeze-dry → QC GPC",
        "lab_priority": "Primary" if candidate.rank <= 3 else "Screening",
    }


def _pipeline_summary(session: dict | None) -> dict[str, Any]:
    if not session or not session.get("pipeline"):
        return {
            "total_input": 500,
            "after_qspr": 150,
            "top5": 5,
            "reduction_pct": 97,
            "stages": [],
            "has_run": False,
        }
    p = session["pipeline"]
    stages = p.get("stages", [])
    total = int(p.get("total_input", 500))
    top_n = len(p.get("top5", []))
    after_qspr = stages[1]["output_count"] if len(stages) > 1 else 150
    reduction = round(100 * (1 - top_n / max(total, 1)), 0)
    return {
        "total_input": total,
        "after_qspr": after_qspr,
        "top5": top_n,
        "reduction_pct": reduction,
        "stages": stages,
        "has_run": True,
    }


def _monomer_supply(reservoir: ReservoirCard) -> list[dict[str, str]]:
    data = load_json("monomers.json")
    rows = []
    for m in data["monomers"]:
        status = "Доступен РФ" if m.get("available_rf") else "Импорт / аналог"
        fit = "OK"
        if reservoir.temperature_c > 100 and m["id"] in ("C12AM", "C18AM"):
            fit = "Проверить термостойкость"
        if reservoir.salinity_g_l > 150 and m.get("charge", 0) == 0 and m["id"] == "AM":
            fit = "Добавить AMPS"
        rows.append({
            "id": m["id"],
            "name_ru": m.get("name_ru", m["id"]),
            "charge": str(m.get("charge", 0)),
            "supply": status,
            "fit_note": fit,
        })
    return rows


def build_synthesis_assessment(ctx: ProjectContext) -> dict[str, Any]:
    r = ctx.reservoir
    session_like = None
    if ctx.session_data and ctx.session_data.get("pipeline"):
        session_like = {"pipeline": ctx.session_data["pipeline"]}
    pipeline = _pipeline_summary(session_like)

    if ctx.session_data and ctx.session_data.get("top5_recipes"):
        candidates = ctx.session_data["top5_recipes"]
        fto_rows = ctx.session_data.get("fto_rows") or build_fto_rows(
            ctx.session_data.get("pipeline", {}).get("top5", [])
        )
    else:
        candidates = top5_to_recipe_candidates([
            {"mol_id": f"PAT-DEMO-{i}", "rank": i, "predicted_frrw": 5.2, "predicted_frro": 1.9}
            for i in range(1, 6)
        ])
        fto_rows = build_fto_rows([{"mol_id": c.recipe_id, "rank": c.rank} for c in candidates])

    fto_by_id = {row["mol_id"]: row["risk"] for row in fto_rows}
    assessments = [
        _score_synthesis_feasibility(c, r, fto_by_id.get(c.recipe_id, "low"))
        for c in candidates
    ]
    recommended = [a for a in assessments if a["feasibility_score"] >= 78]
    doe = generate_doe_matrix()

    return {
        "title": "Оценка возможности синтеза новых рецептур (хемоинформатика)",
        "expert_competency": EXPERT_CHEMINFORMATICS_COMPETENCY,
        "methodology": build_cheminformatics_methodology(),
        "pipeline": pipeline,
        "candidates": candidates,
        "assessments": assessments,
        "recommended_count": len(recommended),
        "synthesis_queue": assessments,
        "monomer_supply": _monomer_supply(r),
        "doe_runs": len(doe),
        "reduction_story": (
            f"Конвейер сокращает перебор с {pipeline['total_input']} in silico кандидатов "
            f"до {pipeline['top5']} рецептур для синтеза (−{pipeline['reduction_pct']:.0f}%). "
            f"DoE Phase 2: {len(doe)} прогонов вместо полного factorial."
        ),
        "conclusion": (
            f"Для {r.field_name} (T={r.temperature_c}°C, salinity {r.salinity_g_l} g/L) "
            f"рекомендован синтез {len(recommended)} из {len(assessments)} top-кандидатов. "
            "Остальные — backup или FTO/мономерная доработка."
        ),
        "competency_evidence": [
            {"artifact": "01-analyticheskiy-otchet-ovp.docx", "proof": "Раздел «Хемоинформатика» + FTO top-5"},
            {"artifact": "/cheminformatics", "proof": "Feasibility score, monomer supply, pipeline"},
            {"artifact": "/screening", "proof": "Live 500→top-5 + QSPRpred validation"},
            {"artifact": "01b-ocenka-sintez-khemoinformatika.docx", "proof": "Формализованная оценка синтеза"},
        ],
    }
