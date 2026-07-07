from __future__ import annotations

from typing import Any

from .cheminformatics import RecipeCandidate, generate_doe_matrix, generate_recipe_grid
from .decision_tree import get_primary_tracks
from .models import LabResult, ProjectContext, ReservoirCard


def _brine_spec(reservoir: ReservoirCard) -> dict[str, Any]:
    return {
        "field": reservoir.field_name,
        "well": reservoir.well_name or "—",
        "temperature_c": reservoir.temperature_c,
        "pressure_mpa": reservoir.pressure_mpa,
        "salinity_g_l": reservoir.salinity_g_l,
        "ca2_mg_l": reservoir.ca2_mg_l,
        "lithology": reservoir.lithology,
        "permeability_md": reservoir.permeability_md,
        "porosity_pct": reservoir.porosity_pct,
        "wettability": reservoir.wettability,
        "api_gravity": reservoir.api_gravity,
        "brine_recipe": (
            f"Синтетическая пластовая вода: NaCl до {reservoir.salinity_g_l:.0f} г/л, "
            f"Ca²⁺ ≈ {reservoir.ca2_mg_l:.0f} мг/л; pH 6.5–7.0; дегазация N₂"
        ),
        "core_flood_note": (
            f"Образцы: {reservoir.lithology}, k={reservoir.permeability_md:.0f} мД, "
            f"φ≈{reservoir.porosity_pct:.0f}%; насыщение нефтью API {reservoir.api_gravity:.0f}°; "
            f"T={reservoir.temperature_c:.0f}°C"
        ),
    }


def _gate_criteria() -> list[dict[str, str]]:
    return [
        {"metric": "Frrw", "phase1": "≥ 3", "phase2": "≥ 5", "note": "RPM selective water block"},
        {"metric": "Frro", "phase1": "≤ 2.5", "phase2": "≤ 2.0", "note": "Минимальное снижение проницаемости по нефти"},
        {"metric": "Oil regain", "phase1": "≥ 60%", "phase2": "≥ 70%", "note": "После обработки и промывки"},
        {"metric": "Water regain", "phase1": "≤ 35%", "phase2": "≤ 30%", "note": "Селективность блокировки воды"},
        {"metric": "Aging ΔFrrw", "phase1": "—", "phase2": "< 20%", "note": "30 сут @ T_plast"},
    ]


def _timeline() -> list[dict[str, str]]:
    return [
        {"week": "1", "track1": "Синтез top-5 RPM, QC MW/мономер", "track2": "Подбор 2–3 gel-композиций", "milestone": "—"},
        {"week": "2", "track1": "Rheology + TGA/DSC", "track2": "Gelation curve vs T", "milestone": "—"},
        {"week": "3", "track1": "Adsorption + contact angle", "track2": "Статика gel block", "milestone": "—"},
        {"week": "4", "track1": "Core flood screening (6 точек)", "track2": "Core flood backup (3 точки)", "milestone": "Gate Phase 1"},
        {"week": "5", "track1": "DoE top-3 → 15 прогонов", "track2": "Параллель при fail Track 1", "milestone": "—"},
        {"week": "6", "track1": "Aging 30 сут (3 образца)", "track2": "Aging gel (при необходимости)", "milestone": "—"},
        {"week": "7", "track1": "Повтор core flood post-aging", "track2": "—", "milestone": "—"},
        {"week": "8", "track1": "Lead recipe card + протокол", "track2": "Backup card", "milestone": "Gate Phase 2 → ОПР"},
    ]


def _track2_backup(reservoir: ReservoirCard, n: int = 3) -> list[RecipeCandidate]:
    grid = generate_recipe_grid(reservoir, n_candidates=12)
    backup = [c for c in grid if c.track == "Track 2"]
    return backup[:n] if backup else grid[-n:]


def _synthesis_queue(
    track1: list[RecipeCandidate],
    track2: list[RecipeCandidate],
) -> list[dict[str, str]]:
    queue: list[dict[str, str]] = []
    for c in track1:
        monomers = ", ".join(f"{k}:{v:.0%}" for k, v in c.monomer_ratios.items())
        queue.append({
            "track": "Track 1",
            "id": c.recipe_id,
            "name": c.name_ru,
            "composition": monomers,
            "mw_kda": f"{c.target_mw_kda:.0f}",
            "conc_pct": f"{c.concentration_pct:.1f}",
            "priority": "Primary" if c.rank <= 3 else "Screening",
            "steps": "Radical copolymerization → dialysis → freeze-dry → QC GPC",
        })
    for c in track2:
        monomers = ", ".join(f"{k}:{v:.0%}" for k, v in c.monomer_ratios.items())
        queue.append({
            "track": "Track 2",
            "id": c.recipe_id,
            "name": c.name_ru,
            "composition": monomers,
            "mw_kda": f"{c.target_mw_kda:.0f}",
            "conc_pct": f"{c.concentration_pct:.1f}",
            "priority": "Backup",
            "steps": "Gel precursor mix → rheology → thermotropic test @ T_res",
        })
    return queue


def _lab_progress(ctx: ProjectContext) -> dict[str, Any]:
    results = ctx.lab_results or []
    if not results:
        return {
            "has_data": False,
            "source": ctx.session_data.get("lab_source", "examples/lab_measurements.csv") if ctx.session_data else "—",
            "passed": 0,
            "total": 0,
            "rows": [],
        }
    rows = []
    for r in results:
        rows.append({
            "recipe_id": r.recipe_id,
            "frrw": f"{r.frrw:.1f}",
            "frro": f"{r.frro:.1f}",
            "oil_regain": f"{r.oil_regain_pct:.0f}%",
            "water_regain": f"{r.water_regain_pct:.0f}%",
            "gate": "ДА" if r.passed_gate else "НЕТ",
        })
    passed = sum(1 for r in results if r.passed_gate)
    return {
        "has_data": True,
        "source": ctx.session_data.get("lab_source", "—") if ctx.session_data else "—",
        "passed": passed,
        "total": len(results),
        "rows": rows,
    }


def build_lab_program(ctx: ProjectContext) -> dict:
    tracks = get_primary_tracks(ctx.reservoir)
    if ctx.session_data and ctx.session_data.get("top5_recipes"):
        track1 = ctx.session_data["top5_recipes"]
    else:
        candidates = generate_recipe_grid(ctx.reservoir, n_candidates=15)
        track1 = [c for c in candidates if c.track == "Track 1"][:5] or candidates[:5]

    track2 = _track2_backup(ctx.reservoir)
    doe = generate_doe_matrix()
    brine = _brine_spec(ctx.reservoir)

    phases = [
        {
            "name": "Phase 1: Screening (недели 1–4)",
            "tasks": [
                f"Подготовка пластовой воды: {brine['brine_recipe']}",
                f"Синтез {len(track1)} полимеров Track 1 + {len(track2)} композиций Track 2 (backup)",
                "QC: MW (GPC), остаточный мономер, вязкость",
                f"Rheology vs T ({brine['temperature_c']:.0f}°C) и salinity",
                "TGA / термостойкость",
                "Статическая адсорбция (Langmuir) + contact angle",
                f"Core flood screening — мин. {6 + len(track2)} точек ({brine['core_flood_note']})",
            ],
            "gate": "Frrw/Frrо ≥ 3 (RPM) или selective water block ≥ 70%",
        },
        {
            "name": "Phase 2: Optimization (недели 5–8)",
            "tasks": [
                "DoE-матрица по Top-3 рецептурам Track 1",
                f"Long-term aging 30 суток при T_plast={brine['temperature_c']:.0f}°C",
                "Повтор core flood после aging",
                "Выбор 1–2 lead formulations; Track 2 — если gate RPM не пройден",
            ],
            "gate": "Frrw ≥ 5, Frro ≤ 2, oil regain ≥ 70%, ΔFrrw aging < 20%",
        },
    ]

    tests = [
        {"id": "T01", "name": "Rheology", "method": "Rotational rheometer", "samples": len(track1) + len(track2)},
        {"id": "T02", "name": "TGA / DSC", "method": "Termogravimetry", "samples": len(track1)},
        {"id": "T03", "name": "Adsorption isotherm", "method": "Static batch on core powder", "samples": 5},
        {"id": "T04", "name": "Contact angle", "method": "Goniometer oil/water/brine", "samples": 5},
        {"id": "T05", "name": "Core flood — water", "method": f"Steady-state @ {brine['temperature_c']:.0f}°C", "samples": 12},
        {"id": "T06", "name": "Core flood — oil regain", "method": "Post-treatment oil flood", "samples": 12},
        {"id": "T07", "name": "Aging cell", "method": f"30 days @ {brine['temperature_c']:.0f}°C in brine", "samples": 3},
        {"id": "T08", "name": "Injectivity", "method": "Pressure drop vs flow rate", "samples": 3},
    ]

    return {
        "title": "Программа лабораторных исследований селективного ОВП",
        "tracks": tracks,
        "track1_candidates": track1,
        "track2_backup": track2,
        "candidates": track1,
        "synthesis_queue": _synthesis_queue(track1, track2),
        "brine_spec": brine,
        "gate_criteria": _gate_criteria(),
        "timeline": _timeline(),
        "doe_runs": doe,
        "phases": phases,
        "tests": tests,
        "lab_progress": _lab_progress(ctx),
        "equipment": [
            "Установка core flood (линейные/линейно-радиальные образцы)",
            "Реометр",
            "TGA / DSC",
            "Сушильный шкаф / термостат",
            "Goniometer",
            "GPC для определения MW",
        ],
        "deliverables": [
            "Протоколы синтеза и QC (Track 1 + Track 2)",
            "Матрица core flood (Frrw, Frro, regain)",
            "DoE response surface (Phase 2)",
            "1–2 lead recipe cards",
            "Отчёт QSPRpred validation (in silico vs lab)",
        ],
    }


def evaluate_lab_gate(result: LabResult, technology: str = "rpm") -> LabResult:
    if technology == "rpm":
        passed = (
            result.frrw >= 5.0
            and result.frro <= 2.0
            and result.oil_regain_pct >= 70.0
            and result.water_regain_pct <= 30.0
            and result.aging_frrw_delta_pct < 20.0
        )
    else:
        passed = result.water_regain_pct <= 20.0 and result.oil_regain_pct >= 50.0
    result.passed_gate = passed
    return result


def build_lab_report(ctx: ProjectContext) -> dict:
    results = ctx.lab_results
    if not results:
        results = _demo_lab_results()

    passed = [r for r in results if r.passed_gate]
    return {
        "title": "Отчёт по результатам лабораторных исследований",
        "results": results,
        "passed_count": len(passed),
        "total_count": len(results),
        "lead_recipes": passed[:2] if passed else results[:1],
        "conclusion": (
            f"Из {len(results)} протестированных рецептур gate прошли {len(passed)}. "
            "Рекомендуется переход к ОПР с lead formulation #1."
            if passed
            else "Gate не пройден — требуется дополнительная оптимизация Track 2."
        ),
    }


def _demo_lab_results() -> list[LabResult]:
    from .models import ReservoirCard

    candidates = generate_recipe_grid(ReservoirCard(), n_candidates=5)
    demo = []
    for i, c in enumerate(candidates):
        r = LabResult(
            recipe_id=c.recipe_id,
            recipe_name=c.name_ru,
            frrw=c.predicted_frrw * (0.9 + i * 0.05),
            frro=c.predicted_frro * (1.0 + i * 0.03),
            oil_regain_pct=75 - i * 3,
            water_regain_pct=25 + i * 4,
            aging_frrw_delta_pct=5 + i * 4,
        )
        evaluate_lab_gate(r)
        demo.append(r)
    return demo
