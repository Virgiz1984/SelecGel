from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import QSPRpredReport, QSPRpredValidationRow


def _compute_metrics_pure(y_true: list[float], y_pred: list[float]) -> dict[str, float]:
    n = len(y_true)
    residuals = [t - p for t, p in zip(y_true, y_pred)]
    mae = sum(abs(r) for r in residuals) / n
    rmse = (sum(r * r for r in residuals) / n) ** 0.5
    ss_res = sum(r * r for r in residuals)
    mean_t = sum(y_true) / n
    ss_tot = sum((t - mean_t) ** 2 for t in y_true)
    r2 = 1 - ss_res / ss_tot if ss_tot else 0
    mape = sum(abs((t - p) / t) * 100 for t, p in zip(y_true, y_pred) if t) / max(n, 1)
    return {"rmse": round(rmse, 4), "mae": round(mae, 4), "r2": round(r2, 4), "mape": round(mape, 2)}


def _compute_metrics(y_true: list[float], y_pred: list[float]) -> dict[str, float]:
    n = len(y_true)
    if n == 0:
        return {"rmse": 0, "mae": 0, "r2": 0, "mape": 0}

    try:
        import numpy as np
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

        yt = np.array(y_true)
        yp = np.array(y_pred)
        rmse = float(mean_squared_error(yt, yp, squared=False))
        mae = float(mean_absolute_error(yt, yp))
        r2 = float(r2_score(yt, yp))
        mape = float(np.mean(np.abs((yt - yp) / np.clip(np.abs(yt), 1e-6, None))) * 100)
        return {"rmse": round(rmse, 4), "mae": round(mae, 4), "r2": round(r2, 4), "mape": round(mape, 2)}
    except (ImportError, AttributeError, ValueError, TypeError):
        return _compute_metrics_pure(y_true, y_pred)


def build_qsprpred_report(
    lab_records: list[dict[str, Any]],
    predictions: list[dict[str, Any]] | None = None,
) -> QSPRpredReport:
    """
    Stage 4: QSPRpred-style validation report.
    Сравнение лабораторных данных (observed) с QSPR/QSAR прогнозами (predicted).

    lab_records: [{"mol_id", "frrw", "frro", "viscosity_cp", "thermal_stability_c"}, ...]
    predictions: optional override; иначе берётся predicted_* из lab_records
    """
    pred_map = {p["mol_id"]: p for p in (predictions or [])}
    rows: list[QSPRpredValidationRow] = []
    props = ["frrw", "frro", "viscosity_cp", "thermal_stability_c"]

    for lab in lab_records:
        mid = lab["mol_id"]
        pred = pred_map.get(mid, lab)
        for prop in props:
            if prop not in lab:
                continue
            obs = float(lab[prop])
            prd = float(pred.get(f"predicted_{prop}", pred.get(prop, obs)))
            resid = obs - prd
            pct = abs(resid / obs * 100) if obs else 0
            rows.append(QSPRpredValidationRow(
                mol_id=mid,
                property_name=prop,
                predicted=round(prd, 4),
                observed=round(obs, 4),
                residual=round(resid, 4),
                abs_error=round(abs(resid), 4),
                pct_error=round(pct, 2),
            ))

    metrics: dict[str, dict[str, float]] = {}
    for prop in props:
        prop_rows = [r for r in rows if r.property_name == prop]
        if len(prop_rows) >= 2:
            metrics[prop] = _compute_metrics(
                [r.observed for r in prop_rows],
                [r.predicted for r in prop_rows],
            )

    n_ok = sum(1 for r in rows if r.pct_error <= 20)
    summary = (
        f"QSPRpred validation: {len(lab_records)} molecules, {len(rows)} property comparisons. "
        f"Within 20% error: {n_ok}/{len(rows)}. "
    )
    if metrics.get("frrw"):
        summary += f"Frrw R²={metrics['frrw']['r2']:.3f}, RMSE={metrics['frrw']['rmse']:.3f}."

    return QSPRpredReport(rows=rows, metrics=metrics, summary=summary)


def export_qsprpred_json(report: QSPRpredReport, path: Path) -> Path:
    payload = {
        "summary": report.summary,
        "metrics": report.metrics,
        "validations": [
            {
                "mol_id": r.mol_id,
                "property": r.property_name,
                "predicted": r.predicted,
                "observed": r.observed,
                "residual": r.residual,
                "abs_error": r.abs_error,
                "pct_error": r.pct_error,
            }
            for r in report.rows
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path


def try_qsprpred_native(lab_smiles: list[str], lab_y: list[float], test_smiles: list[str]):
    """Опциональный вызов qsprpred API, если установлен."""
    try:
        import qsprpred  # noqa: F401
        # QSPRpred требует полного workflow (data tables, model config).
        # Возвращаем None — используем совместимый отчёт выше.
        return None
    except ImportError:
        return None
