"""Сборка ProjectContext из demo session + pipeline + lab CSV."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from vodopritok.cheminformatics import RecipeCandidate
from vodopritok.demo.lab_data import get_active_lab_csv, lab_overrides_for_pipeline, lab_results_from_top5, load_lab_measurements
from vodopritok.demo.session import get_context_from_session, load_session
from vodopritok.models import OUTPUT_DIR, ProjectContext, ReservoirCard, load_json
from vodopritok.pipeline.orchestrator import pipeline_to_lab_validation
from vodopritok.pipeline.models import PipelineResult, PipelineStage, QSARScore, QSPRScore

PATENT_LIBRARY = Path(__file__).resolve().parent.parent / "data" / "patent_molecules.json"


def _mol_lookup() -> dict[str, dict]:
    if not PATENT_LIBRARY.exists():
        return {}
    with PATENT_LIBRARY.open(encoding="utf-8") as f:
        data = json.load(f)
    return {m["mol_id"]: m for m in data.get("molecules", [])}


def top5_to_recipe_candidates(top5: list[dict], track: str = "Track 1 RPM") -> list[RecipeCandidate]:
    lookup = _mol_lookup()
    candidates: list[RecipeCandidate] = []
    for i, mol in enumerate(top5):
        mid = mol.get("mol_id", f"MOL-{i+1}")
        meta = lookup.get(mid, {})
        cls = meta.get("class", "copolymer")
        ratios = {"AM": 0.65, "AMPS": 0.25, "NVP": 0.10}
        if "PEI" in mid:
            ratios = {"PEI": 0.8, "AMPS": 0.2}
        candidates.append(RecipeCandidate(
            recipe_id=mid,
            name_ru=meta.get("name", mid),
            track=track,
            monomer_ratios=ratios,
            target_mw_kda=1200 + i * 100,
            concentration_pct=1.5 + i * 0.1,
            charge_density=-0.3,
            hydrophobe_pct=8.0 + i,
            predicted_frrw=float(mol.get("predicted_frrw", 5)),
            predicted_frro=float(mol.get("predicted_frro", 2)),
            predicted_score=float(mol.get("selectivity_index", mol.get("qsar_score", 5))),
            rank=int(mol.get("rank", i + 1)),
            hypothesis=f"In silico selectivity ({cls}); patent {meta.get('patent_ref', '—')}",
        ))
    return candidates


def build_fto_rows(top5: list[dict]) -> list[dict]:
    lookup = _mol_lookup()
    rows = []
    for mol in top5:
        mid = mol.get("mol_id", "")
        meta = lookup.get(mid, {})
        patent = meta.get("patent_ref", "—")
        risk = "low"
        if not patent or patent == "—":
            risk = "review"
        elif patent.startswith("US") and len(patent) >= 6 and patent[2:6].isdigit():
            if int(patent[2:6]) < 2000:
                risk = "medium — verify expiry"
        rows.append({
            "mol_id": mid,
            "name": meta.get("name", mid),
            "patent_ref": patent,
            "class": meta.get("class", "—"),
            "risk": risk,
            "recommendation": "Proceed to lab" if risk == "low" else "FTO review before synthesis",
        })
    return rows


def _pipeline_from_session(session: dict) -> PipelineResult | None:
    p = session.get("pipeline")
    if not p or not p.get("top5"):
        return None
    stages = [
        PipelineStage(**{k: s[k] for k in ("name", "tool", "input_count", "output_count", "filter_pct", "details") if k in s})
        for s in p.get("stages", [])
    ]
    top5 = [
        QSARScore(
            mol_id=m["mol_id"],
            predicted_frrw=float(m["predicted_frrw"]),
            predicted_frro=float(m["predicted_frro"]),
            selectivity_index=float(m.get("selectivity_index", m["predicted_frrw"] / max(m["predicted_frro"], 0.1))),
            qsar_score=float(m.get("qsar_score", 0)),
            rank=int(m.get("rank", i + 1)),
        )
        for i, m in enumerate(p["top5"])
    ]
    qspr = [
        QSPRScore(
            mol_id=m["mol_id"],
            predicted_viscosity_cp=float(m.get("predicted_viscosity_cp", 5)),
            predicted_thermal_stability_c=float(m.get("predicted_thermal_stability_c", 100)),
            qspr_score=float(m.get("qspr_score", 1)),
            passed=True,
        )
        for m in p.get("qspr_candidates", p["top5"])
    ]
    return PipelineResult(
        stages=stages or [],
        descriptors=[],
        qspr_candidates=qspr,
        top5=top5,
        total_input=int(p.get("total_input", 500)),
        library_path=p.get("library_path", ""),
    )


def build_deliverable_context(
    session: dict | None = None,
    lab_csv: Path | None = None,
) -> ProjectContext:
    """ProjectContext с данными screening session для генерации docx."""
    session = session or load_session()
    if session:
        ctx = ProjectContext(
            expert_name=session.get("expert", "Эксперт по ОВП"),
            company_name=session.get("company", "Заказчик"),
            reservoir=ReservoirCard(**session["reservoir"]),
        )
    else:
        ctx = get_context_from_session() or ProjectContext()

    if not session or not session.get("pipeline"):
        return ctx

    top5 = session["pipeline"]["top5"]
    lab_csv = lab_csv or get_active_lab_csv()
    lab_rows = load_lab_measurements(lab_csv)
    ctx.lab_results = lab_results_from_top5(top5, lab_rows)

    pipeline = _pipeline_from_session(session)
    validation = None
    if pipeline:
        validation = pipeline_to_lab_validation(pipeline, lab_overrides_for_pipeline(top5, lab_rows))

    ctx.session_data = {
        "pipeline": session["pipeline"],
        "top5_recipes": top5_to_recipe_candidates(top5),
        "fto_rows": build_fto_rows(top5),
        "qsprpred": validation,
        "lab_source": str(lab_csv or "examples/lab_measurements.csv"),
        "library_stats": session["pipeline"].get("library_stats", {}),
    }
    return ctx
