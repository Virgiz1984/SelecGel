from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from vodopritok.models import OUTPUT_DIR


@dataclass
class FieldFeedback:
    """Модуль 4: промысловая обратная связь."""

    feedback_id: str
    well_name: str
    mol_id: str
    treatment_date: str
    water_cut_before_pct: float
    water_cut_after_pct: float
    oil_rate_before_tpd: float
    oil_rate_after_tpd: float
    predicted_frrw: float
    predicted_frro: float
    notes: str = ""
    created_at: str = ""


FEEDBACK_DB = OUTPUT_DIR / "selecgel_feedback.json"


def _load_all() -> list[dict]:
    if not FEEDBACK_DB.exists():
        return []
    with FEEDBACK_DB.open(encoding="utf-8") as f:
        return json.load(f).get("records", [])


def _save_all(records: list[dict]) -> None:
    FEEDBACK_DB.parent.mkdir(parents=True, exist_ok=True)
    with FEEDBACK_DB.open("w", encoding="utf-8") as f:
        json.dump({"updated_at": datetime.now().isoformat(), "records": records}, f, ensure_ascii=False, indent=2)


def submit_feedback(data: dict[str, Any]) -> FieldFeedback:
    records = _load_all()
    fb = FieldFeedback(
        feedback_id=f"FB-{len(records)+1:05d}",
        well_name=data.get("well_name", ""),
        mol_id=data.get("mol_id", ""),
        treatment_date=data.get("treatment_date", datetime.now().strftime("%Y-%m-%d")),
        water_cut_before_pct=float(data.get("water_cut_before_pct", 0)),
        water_cut_after_pct=float(data.get("water_cut_after_pct", 0)),
        oil_rate_before_tpd=float(data.get("oil_rate_before_tpd", 0)),
        oil_rate_after_tpd=float(data.get("oil_rate_after_tpd", 0)),
        predicted_frrw=float(data.get("predicted_frrw", 0)),
        predicted_frro=float(data.get("predicted_frro", 0)),
        notes=data.get("notes", ""),
        created_at=datetime.now().isoformat(),
    )
    records.append(asdict(fb))
    _save_all(records)
    return fb


def list_feedback(limit: int = 50) -> list[FieldFeedback]:
    return [FieldFeedback(**r) for r in _load_all()[-limit:]]


def feedback_analytics() -> dict[str, Any]:
    records = _load_all()
    if not records:
        return {"count": 0, "avg_wc_reduction": 0, "success_rate_pct": 0, "retrain_ready": False}

    reductions = [r["water_cut_before_pct"] - r["water_cut_after_pct"] for r in records]
    successes = sum(1 for d in reductions if d >= 15)
    return {
        "count": len(records),
        "avg_wc_reduction": round(sum(reductions) / len(reductions), 1),
        "success_rate_pct": round(successes / len(records) * 100, 1),
        "retrain_ready": len(records) >= 5,
        "message": (
            "Достаточно данных для дообучения QSAR/QSPR" if len(records) >= 5
            else f"Нужно ещё {5 - len(records)} записей для retrain"
        ),
    }


def feedback_to_training_data() -> list[dict]:
    """Конвертация промысловых данных в формат для retrain pipeline."""
    out = []
    for r in _load_all():
        out.append({
            "mol_id": r["mol_id"],
            "frrw": r.get("observed_frrw", r["predicted_frrw"] * 0.95),
            "frro": r.get("observed_frro", r["predicted_frro"] * 1.05),
            "water_cut_delta": r["water_cut_before_pct"] - r["water_cut_after_pct"],
        })
    return out
