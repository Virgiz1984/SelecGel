"""Общие функции для Streamlit-версии SelecGel."""

from __future__ import annotations

import json
import sys
import zipfile
from dataclasses import asdict
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parent
APP_DIR = ROOT / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from vodopritok.decision_tree import recommend_technologies, rd_track_strategy  # noqa: E402
from vodopritok.demo.context_builder import build_deliverable_context, build_fto_rows  # noqa: E402
from vodopritok.demo.lab_data import get_active_lab_csv, lab_overrides_for_pipeline, load_lab_measurements  # noqa: E402
from vodopritok.demo.risk_dashboard import build_risk_dashboard  # noqa: E402
from vodopritok.demo.session import PITCH_POINTS, TZ_MAPPING, load_session, save_session  # noqa: E402
from vodopritok.economics import OpexScenario, analyze_opex, build_opex_plan  # noqa: E402
from vodopritok.export import generate_one_pager  # noqa: E402
from vodopritok.lab_program import build_lab_program  # noqa: E402
from vodopritok.models import OUTPUT_DIR, ReservoirCard, load_json  # noqa: E402
from vodopritok.opr_program import build_opr_program  # noqa: E402
from vodopritok.pipeline import export_qsprpred_json, run_cheminformatics_pipeline  # noqa: E402
from vodopritok.pipeline.orchestrator import pipeline_to_lab_validation  # noqa: E402
from vodopritok.pipeline.patent_library import ensure_patent_library  # noqa: E402
from vodopritok.pipeline.descriptors import rdkit_available  # noqa: E402
from vodopritok.reports import (  # noqa: E402
    generate_all_deliverables,
    generate_lab_program_doc,
    generate_opex_plan_doc,
    generate_opr_program_doc,
    generate_synthesis_assessment_doc,
)
from vodopritok.selecgel.config import PRODUCT_NAME, PRODUCT_TAGLINE  # noqa: E402
from vodopritok.selecgel.digital_twin import build_twins_from_pipeline  # noqa: E402
from vodopritok.synthesis_assessment import build_synthesis_assessment  # noqa: E402
from vodopritok.web.viz import build_qsprpred_comparison  # noqa: E402

EXAMPLE_RESERVOIR = APP_DIR / "examples" / "reservoir_example.json"


def form_defaults() -> dict[str, Any]:
    session = load_session()
    if session and session.get("reservoir"):
        return session["reservoir"]
    if EXAMPLE_RESERVOIR.exists():
        with EXAMPLE_RESERVOIR.open(encoding="utf-8") as f:
            return json.load(f)
    return ReservoirCard().to_dict()


def reservoir_from_form(data: dict[str, Any]) -> ReservoirCard:
    return ReservoirCard(
        field_name=data.get("field_name", "Месторождение"),
        well_name=data.get("well_name", ""),
        temperature_c=float(data.get("temperature_c", 80)),
        pressure_mpa=float(data.get("pressure_mpa", 15)),
        salinity_g_l=float(data.get("salinity_g_l", 120)),
        ca2_mg_l=float(data.get("ca2_mg_l", 500)),
        lithology=data.get("lithology", "sandstone"),
        wettability=data.get("wettability", "water_wet"),
        permeability_md=float(data.get("permeability_md", 500)),
        porosity_pct=float(data.get("porosity_pct", 18)),
        water_mechanism=data.get("water_mechanism", "coning"),
        water_cut_pct=float(data.get("water_cut_pct", 85)),
        oil_rate_tpd=float(data.get("oil_rate_tpd", 12)),
        water_rate_m3pd=float(data.get("water_rate_m3pd", 45)),
        api_gravity=float(data.get("api_gravity", 22)),
        has_fracture=bool(data.get("has_fracture")),
        previous_ovp=data.get("previous_ovp", ""),
    )


def library_stats(n: int = 500) -> dict[str, Any]:
    lib = ensure_patent_library(n=n)
    with lib.open(encoding="utf-8") as f:
        data = json.load(f)
    molecules = data.get("molecules", [])
    classes: dict[str, int] = {}
    patents: set[str] = set()
    for mol in molecules:
        classes[mol.get("class", "other")] = classes.get(mol.get("class", "other"), 0) + 1
        if mol.get("patent_ref"):
            patents.add(mol["patent_ref"])
    return {
        "count": len(molecules),
        "classes": classes,
        "unique_patents": len(patents),
        "description": data.get("description", ""),
    }


def pipeline_summary(result) -> dict[str, Any]:
    stats = library_stats(result.total_input)
    return {
        "stages": [asdict(s) for s in result.stages],
        "top5": [asdict(c) for c in result.top5],
        "qspr_candidates": [asdict(q) for q in result.qspr_candidates[:20]],
        "total_input": result.total_input,
        "library_path": result.library_path,
        "library_stats": stats,
    }


def validation_with_lab(result, top5_dicts, lab_rows=None):
    validation_before = pipeline_to_lab_validation(result, [])
    overrides = lab_overrides_for_pipeline(top5_dicts, lab_rows or load_lab_measurements())
    validation_after = pipeline_to_lab_validation(result, overrides)
    comparison = build_qsprpred_comparison(validation_before["report"], validation_after["report"])
    return validation_after, comparison


def run_screening(form: dict[str, Any], expert: str, company: str) -> dict[str, Any]:
    reservoir = reservoir_from_form(form)
    recs = recommend_technologies(reservoir, top_n=3)
    result = run_cheminformatics_pipeline(reservoir=reservoir, n_molecules=500, top_n=5)
    top5_dicts = [asdict(c) for c in result.top5]
    validation, comparison = validation_with_lab(result, top5_dicts)
    summary = pipeline_summary(result)
    save_session(
        form,
        expert,
        company,
        summary,
        lab_csv_path=str(get_active_lab_csv()),
        qsprpred_comparison=comparison,
    )
    export_qsprpred_json(validation["report"], OUTPUT_DIR / "qsprpred_validation.json")
    generate_one_pager(reservoir, recs, top5_dicts, expert=expert, company=company)
    twins = build_twins_from_pipeline(result, reservoir)
    if twins:
        summary["lead_twin"] = asdict(twins[0])
        save_session(
            form,
            expert,
            company,
            summary,
            lab_csv_path=str(get_active_lab_csv()),
            qsprpred_comparison=comparison,
        )
    fto = build_fto_rows(top5_dicts)
    risk = build_risk_dashboard(
        reservoir,
        top5_dicts,
        recs,
        stages=[asdict(s) for s in result.stages],
        validation_metrics=comparison.get("after"),
        fto_rows=fto,
    )
    return {
        "stages": [asdict(s) for s in result.stages],
        "top5": top5_dicts,
        "validation": validation,
        "comparison": comparison,
        "recommendations": recs,
        "rd_tracks": rd_track_strategy(reservoir),
        "fto_rows": fto,
        "risk_dashboard": risk,
        "library_stats": summary.get("library_stats"),
    }


def payload_from_session(
    session: dict[str, Any],
    reservoir: ReservoirCard,
    recs: list[Any],
    lib_stats: dict[str, Any],
) -> dict[str, Any] | None:
    pipe = session.get("pipeline")
    if not pipe:
        return None
    top5_dicts = pipe.get("top5", [])
    if not top5_dicts:
        return None
    stages = pipe.get("stages", [])
    return {
        "stages": stages,
        "top5": top5_dicts,
        "recommendations": recs,
        "fto_rows": build_fto_rows(top5_dicts),
        "risk_dashboard": build_risk_dashboard(
            reservoir,
            top5_dicts,
            recs,
            stages=stages,
        ),
        "library_stats": pipe.get("library_stats") or lib_stats,
    }


def top5_dataframe(top5: list[dict]) -> pd.DataFrame:
    rows = []
    for mol in top5:
        rows.append(
            {
                "Rank": mol.get("rank"),
                "ID": mol.get("mol_id"),
                "Frrw": round(float(mol.get("predicted_frrw", 0)), 2),
                "Frro": round(float(mol.get("predicted_frro", 0)), 2),
                "Селективность": round(float(mol.get("selectivity_index", 0)), 2),
            }
        )
    return pd.DataFrame(rows)


def funnel_dataframe(stages: list[dict], top_n: int = 5) -> pd.DataFrame:
    qspr_out = stages[1]["output_count"] if len(stages) > 1 else top_n * 10
    return pd.DataFrame(
        {
            "Этап": ["Патентная библиотека", "После QSPR (−70%)", f"Top-{top_n} (QSAR)"],
            "Молекул": [stages[0]["output_count"] if stages else 500, qspr_out, top_n],
        }
    )


def deliverable_context():
    return build_deliverable_context()


def generate_reports_zip() -> bytes:
    ctx = deliverable_context()
    paths = generate_all_deliverables(ctx)
    generate_synthesis_assessment_doc(ctx)
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in paths:
            if path.exists():
                zf.write(path, path.name)
        extra = OUTPUT_DIR / "01b-ocenka-sintez-khemoinformatika.docx"
        if extra.exists():
            zf.write(extra, extra.name)
    buf.seek(0)
    return buf.read()


def file_download_bytes(path: Path) -> bytes | None:
    if path.exists():
        return path.read_bytes()
    return None


def mechanisms() -> list[dict]:
    return load_json("technologies.json")["water_mechanisms"]
