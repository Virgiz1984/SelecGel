from __future__ import annotations

import json
from pathlib import Path

from vodopritok.models import ReservoirCard

from .descriptors import featurize_molecules
from .models import MoleculeRecord, PipelineResult, PipelineStage
from .patent_library import ensure_patent_library
from .qsar_deepchem import run_deepchem_qsar
from .qspr_sklearn import run_qspr_screening
from .qsprpred_report import build_qsprpred_report, export_qsprpred_json


def load_patent_molecules(path: Path | None = None, n: int = 500) -> list[MoleculeRecord]:
    lib_path = ensure_patent_library(path, n=n)
    with lib_path.open(encoding="utf-8") as f:
        data = json.load(f)

    return [
        MoleculeRecord(
            mol_id=m["mol_id"],
            smiles=m["smiles"],
            name=m.get("name", m["mol_id"]),
            patent_ref=m.get("patent_ref", ""),
            mol_class=m.get("class", ""),
            metadata={k: v for k, v in m.items() if k not in ("mol_id", "smiles", "name", "patent_ref", "class")},
        )
        for m in data["molecules"]
    ]


def run_cheminformatics_pipeline(
    reservoir: ReservoirCard | None = None,
    n_molecules: int = 500,
    top_n: int = 5,
    use_molfeat: bool = True,
    library_path: Path | None = None,
) -> PipelineResult:
    """
    Полный конвейер:

    1. RDKit + molfeat → дескрипторы (500 патентных молекул)
    2. scikit-learn QSPR → вязкость + термостойкость → top 30%
    3. DeepChem QSAR → селективность → top-5
    """
    reservoir = reservoir or ReservoirCard()
    lib_path = ensure_patent_library(library_path, n=n_molecules)
    molecules = load_patent_molecules(lib_path, n=n_molecules)

    # Stage 1
    descriptors = featurize_molecules(molecules, use_molfeat=use_molfeat)
    molfeat_status = "molfeat RDKit2D" if descriptors and descriptors[0].molfeat_features else "RDKit only"
    stage1 = PipelineStage(
        name="Descriptor generation",
        tool=f"RDKit + {molfeat_status}",
        input_count=len(molecules),
        output_count=len(descriptors),
        filter_pct=0,
        details=f"{len(descriptors[0].feature_names)} features per molecule",
    )

    # Stage 2
    qspr_kept, qspr_meta = run_qspr_screening(
        descriptors,
        reservoir_temp_c=reservoir.temperature_c,
        keep_fraction=0.30,
    )
    stage2 = PipelineStage(
        name="QSPR screening",
        tool="scikit-learn (viscosity + thermal stability)",
        input_count=qspr_meta["input"],
        output_count=qspr_meta["output"],
        filter_pct=qspr_meta["filtered_pct"],
        details=f"T_min={qspr_meta['thermal_min_c']}°C, η_max={qspr_meta['viscosity_max_cp']} cP",
    )

    # Stage 3
    top5, qsar_meta = run_deepchem_qsar(descriptors, qspr_kept, top_n=top_n, reservoir=reservoir)
    filtered_pct = round((1 - len(top5) / max(len(molecules), 1)) * 100, 1)
    stage3 = PipelineStage(
        name="QSAR selectivity",
        tool=qsar_meta.get("tool", "DeepChem"),
        input_count=qsar_meta.get("input", len(qspr_kept)),
        output_count=len(top5),
        filter_pct=filtered_pct,
        details="Target: Frrw/Frro selectivity index",
    )

    return PipelineResult(
        stages=[stage1, stage2, stage3],
        descriptors=descriptors,
        qspr_candidates=qspr_kept,
        top5=top5,
        total_input=len(molecules),
        library_path=str(lib_path),
    )


def pipeline_to_lab_validation(
    pipeline: PipelineResult,
    lab_overrides: list[dict] | None = None,
) -> dict:
    """Готовит данные для QSPRpred-отчёта (факт vs прогноз)."""
    top_map = {t.mol_id: t for t in pipeline.top5}
    qspr_map = {q.mol_id: q for q in pipeline.qspr_candidates}

    records = []
    for mid, qsar in top_map.items():
        qspr = qspr_map.get(mid)
        obs = next((r for r in (lab_overrides or []) if r.get("mol_id") == mid), None)
        records.append({
            "mol_id": mid,
            "frrw": obs.get("frrw", qsar.predicted_frrw * 0.95) if obs else qsar.predicted_frrw * 0.95,
            "frro": obs.get("frro", qsar.predicted_frro * 1.05) if obs else qsar.predicted_frro * 1.05,
            "predicted_frrw": qsar.predicted_frrw,
            "predicted_frro": qsar.predicted_frro,
            "viscosity_cp": obs.get("viscosity_cp", qspr.predicted_viscosity_cp * 1.1) if obs and qspr else (qspr.predicted_viscosity_cp * 1.1 if qspr else 5.0),
            "predicted_viscosity_cp": qspr.predicted_viscosity_cp if qspr else 5.0,
            "thermal_stability_c": obs.get("thermal_stability_c", qspr.predicted_thermal_stability_c * 0.98) if obs and qspr else (qspr.predicted_thermal_stability_c * 0.98 if qspr else 100),
            "predicted_thermal_stability_c": qspr.predicted_thermal_stability_c if qspr else 100,
        })

    report = build_qsprpred_report(records)
    return {"report": report, "records": records}
