"""Загрузка лабораторных измерений из CSV для QSPRpred и отчётов."""

from __future__ import annotations

import csv
from pathlib import Path

from vodopritok.lab_program import evaluate_lab_gate
from vodopritok.models import LabResult

DEFAULT_LAB_CSV = Path(__file__).resolve().parent.parent.parent / "examples" / "lab_measurements.csv"
UPLOADED_LAB_CSV = Path(__file__).resolve().parent.parent.parent / "output" / "uploaded_lab.csv"


def get_active_lab_csv() -> Path:
    from vodopritok.demo.session import load_session
    session = load_session()
    if session and session.get("lab_csv_path"):
        p = Path(session["lab_csv_path"])
        if p.exists():
            return p
    if UPLOADED_LAB_CSV.exists():
        return UPLOADED_LAB_CSV
    return DEFAULT_LAB_CSV


def load_lab_measurements(path: Path | None = None) -> list[dict]:
    csv_path = path or get_active_lab_csv()
    if not csv_path.exists():
        return []
    rows: list[dict] = []
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "rank": int(row.get("rank") or len(rows) + 1),
                "mol_id": row.get("mol_id", "").strip(),
                "frrw": float(row["frrw"]),
                "frro": float(row["frro"]),
                "oil_regain_pct": float(row.get("oil_regain_pct") or 75),
                "water_regain_pct": float(row.get("water_regain_pct") or 22),
                "viscosity_cp": float(row["viscosity_cp"]) if row.get("viscosity_cp") else None,
                "thermal_stability_c": float(row["thermal_stability_c"]) if row.get("thermal_stability_c") else None,
                "aging_frrw_delta_pct": float(row.get("aging_frrw_delta_pct") or 8),
                "patent_ref": row.get("patent_ref", "").strip(),
                "notes": row.get("notes", "").strip(),
            })
    return rows


def _lab_for_mol(mol: dict, index: int, lab_rows: list[dict]) -> dict:
    mid = mol.get("mol_id", "")
    rank = int(mol.get("rank", index + 1))
    by_id = {r["mol_id"]: r for r in lab_rows if r.get("mol_id")}
    by_rank = {r["rank"]: r for r in lab_rows}
    return by_id.get(mid) or by_rank.get(rank) or by_rank.get(index + 1) or {}


def lab_overrides_for_pipeline(top5: list[dict] | None = None, lab_rows: list[dict] | None = None) -> list[dict]:
    rows = lab_rows if lab_rows is not None else load_lab_measurements()
    if not top5:
        return [{"mol_id": r["mol_id"], **r} for r in rows if r.get("mol_id")]
    overrides = []
    for i, mol in enumerate(top5):
        lab = _lab_for_mol(mol, i, rows)
        if not lab:
            continue
        overrides.append({
            "mol_id": mol["mol_id"],
            "frrw": lab["frrw"],
            "frro": lab["frro"],
            "viscosity_cp": lab.get("viscosity_cp"),
            "thermal_stability_c": lab.get("thermal_stability_c"),
        })
    return overrides


def lab_results_from_top5(top5: list[dict], lab_rows: list[dict] | None = None) -> list[LabResult]:
    rows = lab_rows or load_lab_measurements()
    results: list[LabResult] = []
    for i, mol in enumerate(top5):
        mid = mol.get("mol_id", f"MOL-{i+1}")
        lab = _lab_for_mol(mol, i, rows)
        r = LabResult(
            recipe_id=mid,
            recipe_name=mol.get("name", mid),
            frrw=float(lab.get("frrw", mol.get("predicted_frrw", 5) * 0.92)),
            frro=float(lab.get("frro", mol.get("predicted_frro", 1.8) * 1.08)),
            oil_regain_pct=float(lab.get("oil_regain_pct", 78 - i * 2)),
            water_regain_pct=float(lab.get("water_regain_pct", 20 + i * 3)),
            aging_frrw_delta_pct=float(lab.get("aging_frrw_delta_pct", 6 + i * 2)),
            notes=lab.get("notes", "Core flood @ T_reservoir"),
        )
        evaluate_lab_gate(r)
        results.append(r)
    return results
