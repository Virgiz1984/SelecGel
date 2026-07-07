from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from vodopritok.models import ReservoirCard
from vodopritok.pipeline import run_cheminformatics_pipeline
from vodopritok.selecgel.config import BUSINESS_MODELS, MARKET_STATS, PRODUCT_NAME, TIERS, get_tier
from vodopritok.selecgel.digital_twin import build_twins_from_pipeline
from vodopritok.selecgel.feedback import feedback_analytics, list_feedback, submit_feedback
from vodopritok.selecgel.service import TierAccessError, run_full_saas_workflow
from vodopritok.selecgel.supply_chain import optimize_supply_chain

router = APIRouter(prefix="/api/v1", tags=["SelecGel AI"])


class ReservoirInput(BaseModel):
    field_name: str = "Месторождение"
    well_name: str = ""
    temperature_c: float = 85.0
    salinity_g_l: float = 130.0
    permeability_md: float = 450.0
    lithology: str = "sandstone"
    water_mechanism: str = "coning"
    water_cut_pct: float = 82.0
    oil_rate_tpd: float = 14.5


class FeedbackInput(BaseModel):
    well_name: str
    mol_id: str
    water_cut_before_pct: float
    water_cut_after_pct: float
    oil_rate_before_tpd: float
    oil_rate_after_tpd: float
    predicted_frrw: float = 5.0
    predicted_frro: float = 1.8
    notes: str = ""


def _tier_from_header(x_tier: str | None) -> str:
    return x_tier or "professional"


def _to_reservoir(data: ReservoirInput) -> ReservoirCard:
    return ReservoirCard(**data.model_dump())


@router.get("/")
def api_info(x_tier: str | None = Header(None, alias="X-Subscription-Tier")):
    tier = get_tier(_tier_from_header(x_tier))
    return {
        "product": PRODUCT_NAME,
        "version": "1.0.0",
        "tier": tier.name_ru,
        "endpoints": [
            "POST /api/v1/screening",
            "POST /api/v1/digital-twin",
            "POST /api/v1/supply-chain",
            "GET  /api/v1/feedback",
            "POST /api/v1/feedback",
            "POST /api/v1/workflow",
            "GET  /api/v1/pricing",
        ],
    }


@router.get("/pricing")
def pricing():
    return {
        "tiers": {k.value: asdict(v) for k, v in TIERS.items()},
        "business_models": BUSINESS_MODELS,
        "market": MARKET_STATS,
    }


@router.post("/screening")
def screening(
    body: ReservoirInput,
    x_tier: str | None = Header(None, alias="X-Subscription-Tier"),
):
    tier = get_tier(_tier_from_header(x_tier))
    if not tier.screening:
        raise HTTPException(403, "Screening недоступен на вашем тарифе")

    result = run_cheminformatics_pipeline(reservoir=_to_reservoir(body), n_molecules=500, top_n=5)
    return {
        "tier": tier.name_ru,
        "stages": [asdict(s) for s in result.stages],
        "top5": [asdict(c) for c in result.top5],
        "library_size": result.total_input,
    }


@router.post("/digital-twin")
def digital_twin_api(
    body: ReservoirInput,
    x_tier: str | None = Header(None, alias="X-Subscription-Tier"),
):
    tier = get_tier(_tier_from_header(x_tier))
    if not tier.digital_twin:
        raise HTTPException(403, "Digital Twin доступен на тарифе Профессиональный+")

    pipeline = run_cheminformatics_pipeline(reservoir=_to_reservoir(body), top_n=5)
    twins = build_twins_from_pipeline(pipeline, _to_reservoir(body))
    return {"twins": [asdict(t) for t in twins]}


@router.post("/supply-chain")
def supply_chain_api(
    monomers: list[str] | None = None,
    batch_kg: float = 500,
    x_tier: str | None = Header(None, alias="X-Subscription-Tier"),
):
    tier = get_tier(_tier_from_header(x_tier))
    if not tier.supply_chain:
        raise HTTPException(403, "Supply Chain доступен на тарифе Профессиональный+")

    plan = optimize_supply_chain(batch_kg=batch_kg, monomers=monomers)
    return asdict(plan)


@router.get("/feedback")
def feedback_list(x_tier: str | None = Header(None, alias="X-Subscription-Tier")):
    tier = get_tier(_tier_from_header(x_tier))
    if not tier.feedback_loop:
        raise HTTPException(403, "Feedback loop недоступен на Базовом тарифе")
    return {"records": [asdict(r) for r in list_feedback()], "analytics": feedback_analytics()}


@router.post("/feedback")
def feedback_submit(
    body: FeedbackInput,
    x_tier: str | None = Header(None, alias="X-Subscription-Tier"),
):
    tier = get_tier(_tier_from_header(x_tier))
    if not tier.feedback_loop:
        raise HTTPException(403, "Feedback loop недоступен на Базовом тарифе")
    fb = submit_feedback(body.model_dump())
    return {"submitted": asdict(fb), "analytics": feedback_analytics()}


@router.post("/workflow")
def full_workflow(
    body: ReservoirInput,
    x_tier: str | None = Header(None, alias="X-Subscription-Tier"),
):
    try:
        return run_full_saas_workflow(_to_reservoir(body), tier_id=_tier_from_header(x_tier))
    except TierAccessError as e:
        raise HTTPException(403, str(e)) from e
