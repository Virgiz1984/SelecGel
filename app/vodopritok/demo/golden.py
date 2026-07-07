"""Обновлённый golden demo с cover letter и checklist."""

from __future__ import annotations

import json
import shutil
import zipfile
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from vodopritok.decision_tree import recommend_technologies
from vodopritok.demo.context_builder import build_deliverable_context
from vodopritok.demo.lab_data import DEFAULT_LAB_CSV, lab_overrides_for_pipeline
from vodopritok.demo.session import save_session
from vodopritok.export import generate_cover_letter, generate_one_pager, generate_tz_checklist
from vodopritok.models import OUTPUT_DIR, ReservoirCard
from vodopritok.pipeline import export_qsprpred_json, run_cheminformatics_pipeline
from vodopritok.pipeline.orchestrator import pipeline_to_lab_validation
from vodopritok.pipeline.patent_library import ensure_patent_library
from vodopritok.reports import generate_all_deliverables, generate_synthesis_assessment_doc
from vodopritok.synthesis_assessment import build_synthesis_assessment
from vodopritok.web.viz import build_qsprpred_comparison

GOLDEN_DIR = OUTPUT_DIR / "golden_demo"
EXAMPLE_RESERVOIR = Path(__file__).resolve().parent.parent.parent / "examples" / "reservoir_example.json"


def _library_stats(n: int = 500) -> dict:
    lib = ensure_patent_library(n=n)
    with lib.open(encoding="utf-8") as f:
        data = json.load(f)
    molecules = data.get("molecules", [])
    classes: dict[str, int] = {}
    patents: set[str] = set()
    for m in molecules:
        classes[m.get("class", "other")] = classes.get(m.get("class", "other"), 0) + 1
        if m.get("patent_ref"):
            patents.add(m["patent_ref"])
    return {
        "count": len(molecules),
        "classes": classes,
        "unique_patents": len(patents),
        "description": data.get("description", ""),
        "path": str(lib),
    }


def run_golden_demo(
    reservoir_path: Path | None = None,
    expert: str = "Эксперт по ОВП",
    company: str = "Демо-заказчик (Западная Сибирь)",
) -> dict:
    reservoir_path = reservoir_path or EXAMPLE_RESERVOIR
    with reservoir_path.open(encoding="utf-8") as f:
        form = json.load(f)
    reservoir = ReservoirCard(**form)

    stats = _library_stats(500)
    result = run_cheminformatics_pipeline(reservoir=reservoir, n_molecules=500, top_n=5)
    top5_dicts = [asdict(c) for c in result.top5]
    val_before = pipeline_to_lab_validation(result, [])
    val_after = pipeline_to_lab_validation(result, lab_overrides_for_pipeline(top5_dicts))
    comparison = build_qsprpred_comparison(val_before["report"], val_after["report"])

    summary = {
        "stages": [asdict(s) for s in result.stages],
        "top5": top5_dicts,
        "qspr_candidates": [asdict(q) for q in result.qspr_candidates[:20]],
        "total_input": result.total_input,
        "library_path": result.library_path,
        "library_stats": stats,
    }
    save_session(form, expert, company, summary, lab_csv_path=str(DEFAULT_LAB_CSV), qsprpred_comparison=comparison)
    export_qsprpred_json(val_after["report"], OUTPUT_DIR / "qsprpred_validation.json")

    recs = recommend_technologies(reservoir, top_n=3)
    extra = [
        generate_one_pager(reservoir, recs, top5_dicts, expert=expert, company=company),
        generate_cover_letter(reservoir, expert=expert, company=company),
        generate_tz_checklist(),
    ]
    ctx = build_deliverable_context()
    extra.append(generate_synthesis_assessment_doc(ctx, build_synthesis_assessment(ctx)))
    docx_paths = generate_all_deliverables(ctx)
    all_paths = extra + docx_paths

    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    snapshot = {
        "created_at": datetime.now().isoformat(),
        "reservoir": form,
        "pipeline": summary,
        "docx_files": [p.name for p in all_paths],
        "lab_csv": str(DEFAULT_LAB_CSV),
        "qsprpred_comparison": comparison,
    }
    snapshot_path = GOLDEN_DIR / "snapshot.json"
    with snapshot_path.open("w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    for p in all_paths:
        shutil.copy2(p, GOLDEN_DIR / p.name)
    shutil.copy2(OUTPUT_DIR / "demo_session.json", GOLDEN_DIR / "demo_session.json")
    if (OUTPUT_DIR / "qsprpred_validation.json").exists():
        shutil.copy2(OUTPUT_DIR / "qsprpred_validation.json", GOLDEN_DIR / "qsprpred_validation.json")

    zip_path = GOLDEN_DIR / "selecgel-golden-demo.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in GOLDEN_DIR.iterdir():
            if path.is_file() and path.name != zip_path.name:
                zf.write(path, path.name)

    return {
        "snapshot": snapshot_path,
        "zip": zip_path,
        "docx": all_paths,
        "session": OUTPUT_DIR / "demo_session.json",
    }
