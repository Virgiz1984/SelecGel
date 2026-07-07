from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import ProjectContext, OprResult


@dataclass
class OpexScenario:
    name: str
    water_cut_before_pct: float
    water_cut_after_pct: float
    oil_rate_tpd: float
    water_lift_cost_rub_m3: float = 85.0
    water_disposal_cost_rub_m3: float = 120.0
    treatment_cost_rub: float = 900_000.0
    treatment_duration_months: int = 12
    wells_count: int = 1


@dataclass
class OpexAnalysis:
    water_reduction_m3_year: float
    annual_savings_rub: float
    treatment_cost_rub: float
    net_annual_benefit_rub: float
    payback_months: float
    cost_per_ton_reduced_water_rub: float
    npv_3yr_rub: float
    measures: list[dict]
    baseline_water_opex_rub: float = 0.0
    water_opex_after_rub: float = 0.0


def _water_rate_from_cut(oil_tpd: float, water_cut_pct: float) -> float:
    if water_cut_pct >= 99.9:
        return oil_tpd * 100
    oil_fraction = 1 - water_cut_pct / 100
    if oil_fraction <= 0:
        return 0
    total_liquid = oil_tpd / oil_fraction
    return (total_liquid - oil_tpd) * 1.0


def _baseline_water_opex(scenario: OpexScenario) -> tuple[float, float]:
    qw_before = _water_rate_from_cut(scenario.oil_rate_tpd, scenario.water_cut_before_pct)
    qw_after = _water_rate_from_cut(scenario.oil_rate_tpd, scenario.water_cut_after_pct)
    unit = scenario.water_lift_cost_rub_m3 + scenario.water_disposal_cost_rub_m3
    before = qw_before * 365 * unit * scenario.wells_count
    after = qw_after * 365 * unit * scenario.wells_count
    return round(before, 0), round(after, 0)


def _estimate_measure_rub(measure: dict, scenario: OpexScenario, analysis: OpexAnalysis) -> float:
    buckets: dict[str, float] = {
        "water_handling": analysis.annual_savings_rub,
        "reagent": scenario.treatment_cost_rub * 0.18,
        "intervention": scenario.treatment_cost_rub * 0.45,
        "failure_avoidance": analysis.annual_savings_rub * 0.35,
        "operations": analysis.baseline_water_opex_rub * 0.12,
        "energy": analysis.baseline_water_opex_rub * 0.08,
    }
    base = buckets.get(measure["bucket"], analysis.annual_savings_rub * 0.1)
    return round(base * measure["saving_pct"] / 100, 0)


def build_opex_reduction_measures(
    scenario: OpexScenario,
    analysis: OpexAnalysis | None = None,
    technology: str = "RPM селективный",
) -> list[dict]:
    raw = [
        {
            "id": 1,
            "category": "Закупки и логистика",
            "measure": "Локализация синтеза мономеров и сшивателей",
            "description": "AM, AMPS, PEI российского происхождения; снижение логистики и валютного риска",
            "bucket": "reagent",
            "saving_pct": 15,
            "horizon": "0–3 мес",
            "owner": "R&D / закупки",
        },
        {
            "id": 2,
            "category": "Закупки и логистика",
            "measure": "Концентрированная поставка (сухой полимер vs эмульсия)",
            "description": "Меньше объём транспорта, складирования и потерь при хранении",
            "bucket": "reagent",
            "saving_pct": 10,
            "horizon": "1–2 мес",
            "owner": "Supply chain",
        },
        {
            "id": 3,
            "category": "Ремонт и закачка",
            "measure": "Bullhead vs Coiled Tubing",
            "description": f"Минимизация стоимости ремонта при {technology}; при k>200 мД — приоритет bullhead",
            "bucket": "intervention",
            "saving_pct": 25,
            "horizon": "ОПР",
            "owner": "Промысловая служба",
        },
        {
            "id": 4,
            "category": "Выбор технологии",
            "measure": "In silico screening + lab gate до поля",
            "description": "Снижение доли неуспешных обработок за счёт Frrw/Frro gate и QSPRpred",
            "bucket": "failure_avoidance",
            "saving_pct": 20,
            "horizon": "0–4 мес",
            "owner": "R&D эксперт",
        },
        {
            "id": 5,
            "category": "Эксплуатация",
            "measure": "Плановое повторное лечение (RPM refresh)",
            "description": "Точечное обновление selective block vs полная re-gel каждые 12–24 мес.",
            "bucket": "intervention",
            "saving_pct": 8,
            "horizon": "6–18 мес",
            "owner": "Геолого-техслужба",
        },
        {
            "id": 6,
            "category": "Эксплуатация",
            "measure": "Оптимизация режима добычи после ОВП",
            "description": "Снижение закачки и подъёма воды при сохранении Qn; debottlenecking УПН",
            "bucket": "water_handling",
            "saving_pct": 12,
            "horizon": "3–6 мес",
            "owner": "Промысел",
        },
        {
            "id": 7,
            "category": "Подготовка нефти",
            "measure": "Совместимость с демульсификатором",
            "description": "Избежание повторных химобработок и перерасхода ПАВ после gel/RPM",
            "bucket": "operations",
            "saving_pct": 5,
            "horizon": "ОПР",
            "owner": "Химлаборатория",
        },
        {
            "id": 8,
            "category": "Энергетика",
            "measure": "Снижение энергозатрат на подъём воды",
            "description": "Эффект от сокращения Qw: насосы, ЭЦН, компрессоры закачки",
            "bucket": "energy",
            "saving_pct": 10,
            "horizon": "После ОПР",
            "owner": "Энергетическая служба",
        },
        {
            "id": 9,
            "category": "Масштабирование",
            "measure": "Стандарт lead recipe + QC protocol",
            "description": "Тиражирование успешной ОПР без повторного полного R&D цикла",
            "bucket": "failure_avoidance",
            "saving_pct": 15,
            "horizon": "4–12 мес",
            "owner": "R&D + промысел",
        },
        {
            "id": 10,
            "category": "Мониторинг",
            "measure": "Dashboard WC/Qw и ранний триггер повторного лечения",
            "description": "Предотвращение «тихого» роста WC и аварийных внеплановых ремонтов",
            "bucket": "failure_avoidance",
            "saving_pct": 7,
            "horizon": "Постоянно",
            "owner": "Диспетчеризация",
        },
    ]
    if analysis is None:
        return raw

    enriched: list[dict] = []
    for m in raw:
        item = dict(m)
        item["estimated_annual_rub"] = _estimate_measure_rub(m, scenario, analysis)
        enriched.append(item)
    return enriched


def _cost_breakdown(scenario: OpexScenario, analysis: OpexAnalysis) -> list[dict[str, Any]]:
    lift = analysis.baseline_water_opex_rub * scenario.water_lift_cost_rub_m3 / (
        scenario.water_lift_cost_rub_m3 + scenario.water_disposal_cost_rub_m3
    )
    disposal = analysis.baseline_water_opex_rub - lift
    return [
        {"item": "Подъём воды", "before_rub": round(lift, 0), "after_rub": round(lift * (1 - analysis.annual_savings_rub / max(analysis.baseline_water_opex_rub, 1)), 0)},
        {"item": "Подготовка / сброс воды", "before_rub": round(disposal, 0), "after_rub": round(disposal * (1 - analysis.annual_savings_rub / max(analysis.baseline_water_opex_rub, 1)), 0)},
        {"item": "Обработка скважины (амортизация/год)", "before_rub": 0, "after_rub": round(scenario.treatment_cost_rub / max(scenario.treatment_duration_months / 12, 0.25), 0)},
        {"item": "Итого OPEX воды", "before_rub": analysis.baseline_water_opex_rub, "after_rub": analysis.water_opex_after_rub},
    ]


def _monitoring_kpi() -> list[dict[str, str]]:
    return [
        {"kpi": "WC, %", "target": "Δ ≥ 15 pp vs baseline", "frequency": "еженедельно"},
        {"kpi": "Qw, m³/сут", "target": "снижение ≥ целевого", "frequency": "еженедельно"},
        {"kpi": "Qn, t/сут", "target": "не ниже −5% vs до ОВП", "frequency": "еженедельно"},
        {"kpi": "₽/m³ поднятой воды", "target": "тренд вниз", "frequency": "ежемесячно"},
        {"kpi": "Effect duration", "target": "≥ 6 мес до refresh", "frequency": "ежеквартально"},
        {"kpi": "Cost per ton reduced water", "target": "< benchmark ПГС/ВУС", "frequency": "на каждую ОПР"},
    ]


def analyze_opex(scenario: OpexScenario, discount_rate: float = 0.12) -> OpexAnalysis:
    qw_before = _water_rate_from_cut(scenario.oil_rate_tpd, scenario.water_cut_before_pct)
    qw_after = _water_rate_from_cut(scenario.oil_rate_tpd, scenario.water_cut_after_pct)
    delta_qw = max(0, qw_before - qw_after) * 365 * scenario.wells_count

    unit_water_cost = scenario.water_lift_cost_rub_m3 + scenario.water_disposal_cost_rub_m3
    annual_savings = delta_qw * unit_water_cost
    treatment = scenario.treatment_cost_rub * scenario.wells_count
    net_annual = annual_savings - treatment / max(scenario.treatment_duration_months / 12, 0.25)

    payback = (treatment / annual_savings * 12) if annual_savings > 0 else float("inf")
    cost_per_ton = treatment / (delta_qw * 1.0) if delta_qw > 0 else 0

    npv = -treatment
    for year in range(1, 4):
        npv += annual_savings / ((1 + discount_rate) ** year)

    baseline, after = _baseline_water_opex(scenario)
    partial = OpexAnalysis(
        water_reduction_m3_year=round(delta_qw, 0),
        annual_savings_rub=round(annual_savings, 0),
        treatment_cost_rub=treatment,
        net_annual_benefit_rub=round(net_annual, 0),
        payback_months=round(payback, 1),
        cost_per_ton_reduced_water_rub=round(cost_per_ton, 0),
        npv_3yr_rub=round(npv, 0),
        measures=[],
        baseline_water_opex_rub=baseline,
        water_opex_after_rub=after,
    )
    partial.measures = build_opex_reduction_measures(scenario, partial)
    return partial


EXPERT_ECONOMICS_COMPETENCY = (
    "Понимание экономических аспектов внедрения новых технологий ОВП: "
    "баланс CAPEX обработки и OPEX воды, NPV/payback, риск неуспешной обработки, "
    "тиражирование lead recipe и мониторинг ROI после ОПР."
)


def build_opex_methodology() -> list[dict[str, str]]:
    """Методология разработки мероприятий по сокращению OPEX (для ТЗ и pitch)."""
    return [
        {
            "step": "1",
            "title": "Baseline OPEX",
            "detail": "Декомпозиция затрат: Qw, подъём, подготовка/сброс, энергия, химия; ₽/m³ воды по скважине",
        },
        {
            "step": "2",
            "title": "Целевой эффект технологии",
            "detail": "WC/Qw после ОВП из механизма обводнения + lab gate (Frrw, Frro, regain)",
        },
        {
            "step": "3",
            "title": "Прямая экономия",
            "detail": "ΔQw → годовая экономия воды; payback и NPV 3 года vs CAPEX обработки",
        },
        {
            "step": "4",
            "title": "Мероприятия по категориям",
            "detail": "Закупки, ремонт, выбор технологии, эксплуатация, мониторинг — с оценкой ₽/год",
        },
        {
            "step": "5",
            "title": "KPI и тираж",
            "detail": "Dashboard WC/Qn; refresh treatment; портфель скважин и синергия закупок",
        },
    ]


def compare_technology_economics(reservoir: ReservoirCard) -> list[dict[str, Any]]:
    """Сравнение экономики классов технологий ОВП для обоснования выбора."""
    base_capex = 900_000 if reservoir.permeability_md >= 200 else 1_200_000
    rows = [
        {
            "technology": "Селективный RPM",
            "track": "Track 1",
            "capex_rub": base_capex,
            "annual_reagent_rub": 140_000,
            "intervention": "Bullhead / CT",
            "repeat_months": "12–24",
            "failed_risk_pct": 15,
            "best_for": "coning, bottom water, высокая селективность",
            "recommended": reservoir.water_mechanism in ("coning", "bottom_water", "edge_water"),
        },
        {
            "technology": "Термотропный gel",
            "track": "Track 2",
            "capex_rub": int(base_capex * 0.85),
            "annual_reagent_rub": 95_000,
            "intervention": "Bullhead",
            "repeat_months": "18–36",
            "failed_risk_pct": 20,
            "best_for": "backup при fail RPM, HTHS",
            "recommended": True,
        },
        {
            "technology": "Массовая gel / PPG",
            "track": "Track 3",
            "capex_rub": int(base_capex * 1.4),
            "annual_reagent_rub": 180_000,
            "intervention": "CT / rig",
            "repeat_months": "24+",
            "failed_risk_pct": 25,
            "best_for": "каналы, трещины, высокий WC",
            "recommended": reservoir.water_mechanism in ("fracture", "channel") or reservoir.has_fracture,
        },
        {
            "technology": "Готовый реагент «как есть»",
            "track": "Vendor",
            "capex_rub": int(base_capex * 0.7),
            "annual_reagent_rub": 220_000,
            "intervention": "Сервис под ключ",
            "repeat_months": "12",
            "failed_risk_pct": 35,
            "best_for": "быстрый пилот без R&D",
            "recommended": False,
        },
    ]
    return rows


def build_implementation_lifecycle(
    analysis: OpexAnalysis,
    project_budget_rub: float = 1_500_000,
) -> list[dict[str, Any]]:
    """Экономика жизненного цикла внедрения: R&D → lab → ОПР → масштаб."""
    return [
        {"phase": "R&D + lab (мес. 1–4)", "cost_rub": project_budget_rub, "benefit_rub": 0},
        {"phase": "ОПР (скв. 1)", "cost_rub": analysis.treatment_cost_rub, "benefit_rub": analysis.annual_savings_rub * 0.5},
        {"phase": "Год 1 эксплуатации", "cost_rub": analysis.treatment_cost_rub * 0.15, "benefit_rub": analysis.annual_savings_rub},
        {"phase": "Год 2 (тираж ×3)", "cost_rub": analysis.treatment_cost_rub * 2.5, "benefit_rub": analysis.annual_savings_rub * 3},
        {"phase": "Год 3 (портфель)", "cost_rub": analysis.treatment_cost_rub * 1.5, "benefit_rub": analysis.annual_savings_rub * 5},
    ]


def build_competency_evidence(plan: dict) -> list[dict[str, str]]:
    """Как демонстрируем компетенцию на demo-стенде."""
    a = plan["analysis"]
    return [
        {"artifact": "06-plan-snizheniya-opex.docx", "proof": f"{len(plan['measures'])} мероприятий с ₽/год и roadmap"},
        {"artifact": "/opex-plan", "proof": "Live-калькулятор WC → NPV/payback + структура OPEX"},
        {"artifact": "One-pager", "proof": f"Payback {a.payback_months:.0f} мес · NPV {a.npv_3yr_rub/1e6:.1f} млн ₽"},
        {"artifact": "Screening", "proof": "Экономика привязана к top-5 и механизму обводнения"},
        {"artifact": "Risk dashboard", "proof": "Блок «Экономика OPEX» в скоринге рисков проекта"},
    ]


def build_opex_plan(ctx: ProjectContext) -> dict:
    r = ctx.reservoir
    wc_after = max(r.water_cut_pct - 18, 55)
    technology = "селективный RPM"
    if ctx.session_data and ctx.session_data.get("pipeline", {}).get("top5"):
        wc_after = max(r.water_cut_pct - 20, 52)
    if r.water_mechanism in ("fracture", "channel"):
        technology = "PPG / gel (условный Track 3)"
        wc_after = max(r.water_cut_pct - 15, 58)

    scenario = OpexScenario(
        name=r.field_name,
        water_cut_before_pct=r.water_cut_pct,
        water_cut_after_pct=wc_after,
        oil_rate_tpd=r.oil_rate_tpd,
        treatment_cost_rub=900_000,
        wells_count=1,
    )
    analysis = analyze_opex(scenario)
    measures = analysis.measures
    incremental = sum(m["estimated_annual_rub"] for m in measures)
    cost_breakdown = _cost_breakdown(scenario, analysis)
    methodology = build_opex_methodology()
    tech_compare = compare_technology_economics(r)
    lifecycle = build_implementation_lifecycle(analysis)

    plan_core = {
        "title": "План мероприятий по сокращению операционных затрат",
        "technology": technology,
        "expert_competency": EXPERT_ECONOMICS_COMPETENCY,
        "methodology": methodology,
        "technology_comparison": tech_compare,
        "implementation_lifecycle": lifecycle,
        "scenario": scenario,
        "analysis": analysis,
        "cost_breakdown": cost_breakdown,
        "measures": measures,
        "measures_by_category": _group_measures(measures),
        "incremental_savings_rub": incremental,
        "total_potential_rub": analysis.annual_savings_rub + incremental,
        "monitoring_kpi": _monitoring_kpi(),
        "implementation_roadmap": [
            {"month": 1, "action": "Baseline OPEX: WC, Qw, ₽/m³ воды по скважине-кандидату"},
            {"month": 1, "action": "In silico + FTO → lead recipe; локализация мономеров"},
            {"month": 2, "action": "Lab gate → bullhead ОПР на 1 скважине; мониторинг WC"},
            {"month": 3, "action": "Стандартизация lead recipe, QC, concentrate supply"},
            {"month": 4, "action": "Тираж на 2–3 скважины; dashboard ROI и KPI OPEX"},
            {"month": 6, "action": "План RPM refresh / повторного лечения по триггеру WC"},
        ],
        "portfolio_note": (
            f"При тиражировании на 5 скважин годовой эффект ×5 ≈ "
            f"{analysis.annual_savings_rub * 5:,.0f} ₽/год (без учёта синергии закупок)."
        ),
    }
    plan_core["competency_evidence"] = build_competency_evidence(plan_core)
    from .decision_tree import recommend_technologies
    from .environmental_impact import build_environmental_impact

    tech_id = "hrpm"
    primary = recommend_technologies(r, top_n=1)
    if primary:
        tech_id = primary[0].technology_id
    plan_core["environmental_impact"] = build_environmental_impact(
        analysis,
        tech_id=tech_id,
        wc_before=r.water_cut_pct,
        wc_after=wc_after,
    )
    return plan_core


def _group_measures(measures: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for m in measures:
        grouped.setdefault(m["category"], []).append(m)
    return grouped


def compare_treatment_economics(
    opr: OprResult,
    water_lift_cost: float = 85.0,
    disposal_cost: float = 120.0,
) -> dict:
    wc_delta = opr.water_cut_before_pct - opr.water_cut_after_pct
    oil_delta_pct = (opr.oil_rate_after_tpd / opr.oil_rate_before_tpd - 1) * 100 if opr.oil_rate_before_tpd else 0
    return {
        "well": opr.well_name,
        "wc_reduction_pct": wc_delta,
        "oil_change_pct": round(oil_delta_pct, 1),
        "treatment_cost_rub": opr.treatment_cost_rub,
        "estimated_payback_months": round(opr.treatment_cost_rub / max(wc_delta * 5000, 1), 1),
        "success": wc_delta >= 15 and oil_delta_pct >= -5,
    }
