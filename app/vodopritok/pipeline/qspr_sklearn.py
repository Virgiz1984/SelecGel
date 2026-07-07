from __future__ import annotations

import math
from typing import Any

from .descriptors import RDKIT_DESCRIPTORS
from .models import DescriptorResult, QSPRScore


def _require_sklearn():
    try:
        import numpy as np
        from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
        from sklearn.preprocessing import StandardScaler
        return np, GradientBoostingRegressor, RandomForestRegressor, StandardScaler
    except ImportError as e:
        raise ImportError("scikit-learn и numpy обязательны для QSPR stage") from e


def _synthetic_training_data(n: int = 200, seed: int = 42):
    """Синтетические QSPR targets для cold-start (до lab calibration)."""
    import random

    rng = random.Random(seed)
    rows = []
    for i in range(n):
        mw = rng.uniform(70, 500)
        logp = rng.uniform(-3, 8)
        tpsa = rng.uniform(0, 200)
        hbd = rng.randint(0, 5)
        hba = rng.randint(0, 8)
        rot = rng.randint(0, 12)
        charge_proxy = hba - hbd

        viscosity = 1.0 + mw / 200 + abs(logp) * 0.3 + rot * 0.1
        thermal = 80 + logp * 5 + tpsa * 0.05 - rot * 2 + charge_proxy * 3

        rows.append({
            "MolWt": mw, "MolLogP": logp, "TPSA": tpsa,
            "NumHDonors": hbd, "NumHAcceptors": hba,
            "NumRotatableBonds": rot, "NumAromaticRings": rng.randint(0, 2),
            "FractionCSP3": rng.uniform(0, 1), "HeavyAtomCount": mw / 14,
            "RingCount": rng.randint(0, 3),
            "viscosity_cp": max(0.5, viscosity),
            "thermal_stability_c": max(40, min(180, thermal)),
        })
    return rows


def _build_feature_matrix(descriptors: list[DescriptorResult]):
    np, _, _, _ = _require_sklearn()
    if not descriptors:
        return np.array([]), []

    names = descriptors[0].feature_names or RDKIT_DESCRIPTORS
    X = np.array([
        [d.rdkit_features.get(n, 0.0) if n in d.rdkit_features else (
            d.molfeat_features.get(n, 0.0) if d.molfeat_features else 0.0
        ) for n in names]
        for d in descriptors
    ])
    return X, names


def train_qspr_models(training_data: list[dict] | None = None):
    """Обучает QSPR-модели вязкости и термостойкости."""
    np, GBR, RF, Scaler = _require_sklearn()
    data = training_data or _synthetic_training_data()
    feature_cols = RDKIT_DESCRIPTORS

    X = np.array([[row.get(c, 0) for c in feature_cols] for row in data])
    scaler = Scaler()
    Xs = scaler.fit_transform(X)

    y_visc = np.array([row["viscosity_cp"] for row in data])
    y_therm = np.array([row["thermal_stability_c"] for row in data])

    model_visc = GBR(n_estimators=80, random_state=42)
    model_therm = RF(n_estimators=80, random_state=42)
    model_visc.fit(Xs, y_visc)
    model_therm.fit(Xs, y_therm)

    return {
        "scaler": scaler,
        "viscosity": model_visc,
        "thermal": model_therm,
        "feature_cols": feature_cols,
    }


def _rule_based_qspr(
    descriptors: list[DescriptorResult],
    reservoir_temp_c: float,
    target_viscosity_max_cp: float,
    thermal_min: float,
    keep_fraction: float,
) -> tuple[list[QSPRScore], dict[str, Any]]:
    scored: list[QSPRScore] = []
    for desc in descriptors:
        r = desc.rdkit_features
        mw = r.get("MolWt", 200)
        logp = r.get("MolLogP", 0)
        rot = r.get("NumRotatableBonds", 0)
        v = 0.5 + mw / 180 + abs(logp) * 0.25 + rot * 0.08
        t = 75 + logp * 4 + r.get("TPSA", 0) * 0.04 - rot * 1.5
        visc_ok = v <= target_viscosity_max_cp
        therm_ok = t >= thermal_min
        qspr = (target_viscosity_max_cp - v) * 2 + (t - thermal_min) * 0.5
        scored.append(QSPRScore(
            mol_id=desc.mol_id,
            predicted_viscosity_cp=round(v, 2),
            predicted_thermal_stability_c=round(t, 1),
            qspr_score=round(qspr, 3),
            passed=visc_ok and therm_ok,
        ))
    scored.sort(key=lambda x: x.qspr_score, reverse=True)
    n_keep = max(5, int(len(scored) * keep_fraction))
    kept = scored[:n_keep]
    return kept, {
        "tool": "rule-based fallback (sklearn unavailable)",
        "input": len(descriptors),
        "output": len(kept),
        "filtered_pct": round((1 - len(kept) / max(len(scored), 1)) * 100, 1),
        "thermal_min_c": thermal_min,
        "viscosity_max_cp": target_viscosity_max_cp,
    }


def run_qspr_screening(
    descriptors: list[DescriptorResult],
    reservoir_temp_c: float = 85.0,
    target_viscosity_max_cp: float = 15.0,
    target_thermal_min_c: float | None = None,
    keep_fraction: float = 0.30,
    models: dict | None = None,
) -> tuple[list[QSPRScore], dict[str, Any]]:
    """
    Stage 2: scikit-learn QSPR.
    Отсеивает ~70% кандидатов по вязкости и термостойкости.
    """
    thermal_min = target_thermal_min_c or (reservoir_temp_c + 15)

    try:
        np, _, _, _ = _require_sklearn()
        models = models or train_qspr_models()
    except (ImportError, AttributeError, ValueError):
        return _rule_based_qspr(
            descriptors, reservoir_temp_c, target_viscosity_max_cp, thermal_min, keep_fraction,
        )

    X, _ = _build_feature_matrix(descriptors)
    if X.size == 0:
        return [], {"error": "empty descriptors"}

    cols = models["feature_cols"]
    X_q = np.array([[d.rdkit_features.get(c, 0.0) for c in cols] for d in descriptors])
    Xs = models["scaler"].transform(X_q)

    visc_pred = models["viscosity"].predict(Xs)
    therm_pred = models["thermal"].predict(Xs)

    scored: list[QSPRScore] = []
    for i, desc in enumerate(descriptors):
        v, t = float(visc_pred[i]), float(therm_pred[i])
        # Чем ниже вязкость (injectivity) и выше T_stab — лучше
        visc_ok = v <= target_viscosity_max_cp
        therm_ok = t >= thermal_min
        qspr = (target_viscosity_max_cp - v) * 2 + (t - thermal_min) * 0.5
        scored.append(QSPRScore(
            mol_id=desc.mol_id,
            predicted_viscosity_cp=round(v, 2),
            predicted_thermal_stability_c=round(t, 1),
            qspr_score=round(qspr, 3),
            passed=visc_ok and therm_ok,
        ))

    scored.sort(key=lambda x: x.qspr_score, reverse=True)
    n_keep = max(5, int(len(scored) * keep_fraction))
    kept = scored[:n_keep]

    meta = {
        "tool": "scikit-learn (GradientBoosting + RandomForest)",
        "input": len(descriptors),
        "output": len(kept),
        "filtered_pct": round((1 - len(kept) / max(len(scored), 1)) * 100, 1),
        "thermal_min_c": thermal_min,
        "viscosity_max_cp": target_viscosity_max_cp,
    }
    return kept, meta
