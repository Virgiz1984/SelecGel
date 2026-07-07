from __future__ import annotations

from dataclasses import asdict
from typing import Any

from vodopritok.models import ReservoirCard
from vodopritok.pipeline import export_qsprpred_json, run_cheminformatics_pipeline
from vodopritok.pipeline.orchestrator import pipeline_to_lab_validation

from .config import PRODUCT_NAME, TierFeatures, get_tier
from .digital_twin import build_twins_from_pipeline
from .feedback import feedback_analytics, feedback_to_training_data, list_feedback
from .supply_chain import optimize_supply_chain


class TierAccessError(PermissionError):
    pass


def check_feature(tier: TierFeatures, feature: str) -> None:
    if not getattr(tier, feature, False):
        raise TierAccessError(f"Функция '{feature}' недоступна на тарифе {tier.name_ru}")


def run_full_saas_workflow(
    reservoir: ReservoirCard,
    tier_id: str = "professional",
    batch_kg: float = 500,
) -> dict[str, Any]:
    """Полный цикл SelecGel AI для Professional/Enterprise."""
    tier = get_tier(tier_id)

    pipeline = run_cheminformatics_pipeline(reservoir=reservoir, n_molecules=500, top_n=5)
    validation = pipeline_to_lab_validation(pipeline)

    result: dict[str, Any] = {
        "product": PRODUCT_NAME,
        "tier": tier.name_ru,
        "module_1_screening": {
            "stages": [asdict(s) for s in pipeline.stages],
            "top5": [asdict(c) for c in pipeline.top5],
            "library_size": pipeline.total_input,
        },
        "module_2_digital_twin": None,
        "module_3_supply_chain": None,
        "module_4_feedback": feedback_analytics(),
        "qsprpred_summary": validation["report"].summary,
    }

    if tier.digital_twin:
        twins = build_twins_from_pipeline(pipeline, reservoir)
        result["module_2_digital_twin"] = [asdict(t) for t in twins]

    if tier.supply_chain:
        sc = optimize_supply_chain(batch_kg=batch_kg)
        result["module_3_supply_chain"] = {
            "best_bundle": [asdict(o) for o in sc.best_bundle],
            "total_cost_rub": sc.total_cost_rub,
            "lead_time_days": sc.total_lead_time_days,
            "recommendation": sc.recommendation,
        }

    return result
