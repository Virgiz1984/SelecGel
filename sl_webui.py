"""UI как на FastAPI :8080 — CSS, навигация, Chart.js."""

from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent
WEB_STATIC = ROOT / "app" / "vodopritok" / "web" / "static"

NAV_ITEMS = [
    ("streamlit_app.py", "Обзор", "home"),
    ("pages/1_Скрининг.py", "Screening", "screening"),
    ("pages/6_Хемоинформатика.py", "Хемоинформ.", "chem"),
    ("pages/2_Лаборатория.py", "Лаборатория", "lab"),
    ("pages/3_OPEX.py", "OPEX", "opex"),
    ("pages/9_Экология.py", "Экология", "environment"),
    ("pages/4_ОПР.py", "ОПР", "opr"),
    ("pages/5_Профиль.py", "Профиль", "twin"),
    ("pages/7_Отчёты.py", "Отчёты", "reports"),
    ("pages/8_Для_заказчика.py", "Для заказчика", "pitch"),
]


@lru_cache(maxsize=1)
def _charts_js() -> str:
    return (WEB_STATIC / "charts.js").read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def _embed_css() -> str:
    css = (WEB_STATIC / "style.css").read_text(encoding="utf-8")
    streamlit_overrides = """
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="stSidebarCollapsedControl"] { display: none !important; }
    .block-container { padding-top: 0.5rem !important; max-width: 1100px !important; }
    header[data-testid="stHeader"] { background: transparent !important; }
    .feas-chart { display: flex; align-items: flex-end; gap: 0.5rem; height: 240px; padding: 0.5rem 0 0; border-bottom: 1px solid var(--border); margin-top: 0.5rem; }
    .feas-col { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; min-width: 0; }
    .feas-bar { width: 72%; min-height: 12px; border-radius: 4px 4px 0 0; }
    .feas-id { font-size: 0.62rem; color: var(--muted); margin-top: 0.4rem; text-align: center; line-height: 1.2; word-break: break-word; }
    .feas-score { font-size: 0.85rem; font-weight: 700; margin-bottom: 0.2rem; }
    .feas-score.ok { color: var(--green); }
    .feas-score.warn { color: #8b5cf6; }
    """
    return css + streamlit_overrides


def setup_page(active: str, title: str | None = None) -> None:
    """Общий каркас страницы как base.html."""
    if title:
        st.set_page_config(
            page_title=f"SelecGel — {title}",
            page_icon="🧪",
            layout="wide",
            initial_sidebar_state="collapsed",
        )
    st.markdown(f"<style>{_embed_css()}</style>", unsafe_allow_html=True)
    _render_header(active)


def _render_header(active: str) -> None:
    st.markdown(
        """
        <header class="header">
          <div class="container header-inner">
            <div class="brand">
              <span class="brand-icon">SG</span>
              <div>
                <h1>SelecGel</h1>
                <p class="subtitle">Хемоинформатический конвейер для селективного ОВП</p>
              </div>
            </div>
          </div>
          <div class="container tier-bar">
            <span class="muted">RDKit · molfeat · scikit-learn QSPR · DeepChem QSAR · QSPRpred</span>
            <span class="muted">Демо-стенд технологии · не коммерческий SaaS</span>
          </div>
        </header>
        <style>
        [data-testid="stPageLink"] a {
          color: var(--muted) !important;
          text-decoration: none !important;
          padding: 0.45rem 0.65rem;
          border-radius: var(--radius);
          font-size: 0.78rem;
          display: block;
          text-align: center;
        }
        [data-testid="stPageLink"] a:hover { background: var(--border); color: var(--text) !important; }
        .nav-active [data-testid="stPageLink"] a {
          background: var(--border);
          color: var(--text) !important;
          font-weight: 600;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    cols = st.columns(len(NAV_ITEMS))
    for col, (path, label, key) in zip(cols, NAV_ITEMS):
        with col:
            if key == active:
                st.markdown('<div class="nav-active">', unsafe_allow_html=True)
            st.page_link(path, label=label)
            if key == active:
                st.markdown("</div>", unsafe_allow_html=True)


def chartjs_init(init_call: str, body_html: str, height: int = 900) -> None:
    """Встроить Chart.js + charts.js и вызвать init*()."""
    payload_safe = init_call.replace("</", "<\\/")
    html = f"""
    <!DOCTYPE html>
    <html><head>
    <meta charset="utf-8">
    <style>{_embed_css()}</style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    </head><body style="background:#0f1419;margin:0;padding:0.5rem;">
    {body_html}
    <script>{_charts_js()}</script>
    <script>
    (function() {{
      function run() {{ {payload_safe} }}
      if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run);
      else run();
    }})();
    </script>
    </body></html>
    """
    components.html(html, height=height, scrolling=False)


def screening_charts_widget(charts: dict[str, Any], height: int = 1180) -> None:
    if not charts:
        return
    json_payload = json.dumps(charts, ensure_ascii=False)
    body = """
    <div class="chart-grid">
      <div class="card chart-box wide"><canvas id="chart-tech"></canvas></div>
      <div class="card chart-box wide"><canvas id="chart-funnel"></canvas></div>
      <div class="card chart-box wide"><canvas id="chart-top5"></canvas></div>
      <div class="card chart-box"><canvas id="chart-selectivity"></canvas></div>
      <div class="card chart-box"><canvas id="chart-qsprpred"></canvas></div>
      <div class="card chart-box"><canvas id="chart-qsprpred-mape"></canvas></div>
      <div class="card chart-box wide"><canvas id="chart-stages"></canvas></div>
    </div>
    """
    chartjs_init(f"initScreeningCharts({json_payload});", body, height=height)


def home_charts_widget(charts: dict[str, Any], has_pipeline: bool, height: int = 720) -> None:
    if not charts:
        return
    json_payload = json.dumps(charts, ensure_ascii=False)
    if has_pipeline:
        body = """
        <div class="chart-grid">
          <div class="card chart-box"><canvas id="chart-home-funnel"></canvas></div>
          <div class="card chart-box"><canvas id="chart-home-top5"></canvas></div>
          <div class="card chart-box wide"><canvas id="chart-home-tech"></canvas></div>
          <div class="card chart-box wide"><canvas id="chart-home-stages"></canvas></div>
        </div>
        """
    else:
        body = """
        <div class="chart-grid">
          <div class="card chart-box wide"><canvas id="chart-home-tech"></canvas></div>
        </div>
        """
    chartjs_init(f"initHomeCharts({json_payload});", body, height=height)


def pitch_charts_widget(charts: dict[str, Any], height: int = 980) -> None:
    if not charts:
        return
    json_payload = json.dumps(charts, ensure_ascii=False)
    body = """
    <div class="chart-grid">
      <div class="card chart-box wide"><canvas id="chart-pitch-tech"></canvas></div>
      <div class="card chart-box wide"><canvas id="chart-pitch-tech-eco"></canvas></div>
      <div class="card chart-box"><canvas id="chart-pitch-funnel"></canvas></div>
      <div class="card chart-box"><canvas id="chart-pitch-top5"></canvas></div>
      <div class="card chart-box wide"><canvas id="chart-pitch-stages"></canvas></div>
    </div>
    """
    chartjs_init(f"initPitchCharts({json_payload});", body, height=height)


def twin_charts_widget(twin_charts: dict[str, Any], twins_meta: list[dict], height: int = 520) -> None:
    if not twin_charts:
        return
    json_payload = json.dumps(twin_charts, ensure_ascii=False)
    toggles = []
    for i, t in enumerate(twins_meta, start=1):
        checked = "checked" if i == 1 else ""
        toggles.append(
            f'<label class="radar-toggle"><input type="checkbox" data-radar-candidate="{i}" {checked} '
            f'onchange="window._twinRadarCtrl && window._twinRadarCtrl.render()"> '
            f"#{i} {t['mol_id']}</label>"
        )
    body = f"""
    <script type="application/json" id="selecgel-twin-charts">{json_payload}</script>
    <section class="card chart-panel">
      <div class="radar-toolbar">
        <div class="radar-toggles"><span class="muted">Кандидаты:</span>{''.join(toggles)}</div>
        <div class="radar-actions">
          <label class="radar-toggle">
            <input type="checkbox" id="radar-lab-toggle" checked
              onchange="window._twinRadarCtrl && window._twinRadarCtrl.render()"> Lab overlay
          </label>
        </div>
      </div>
      <div class="chart-grid">
        <div class="card chart-box chart-box-tall"><canvas id="chart-twin-radar"></canvas></div>
        <div class="card chart-box"><canvas id="chart-twin-eco"></canvas></div>
      </div>
      <div id="radar-gate-summary" class="radar-summary"></div>
    </section>
    """
    chartjs_init("bootTwinPage();", body, height=height)


def risk_cards_html(risk: dict[str, Any]) -> str:
    cards = []
    for c in risk.get("cards", []):
        level = c.get("level", "medium")
        cards.append(
            f'<div class="risk-card level-{level}">'
            f'<span class="risk-title">{c["title"]}</span>'
            f'<strong class="risk-score">{int(c["score"])}</strong>'
            f'<span class="muted">{c.get("detail", "")}</span></div>'
        )
    return (
        f'<section class="card highlight"><h2>Оценка проекта · {risk.get("overall_score", 0):.0f}/100</h2>'
        f'<p class="muted">Risk level: {risk.get("overall_level", "—")}</p>'
        f'<div class="risk-grid">{"".join(cards)}</div></section>'
    )


def render_risk_dashboard(risk: dict[str, Any] | None) -> None:
    if risk:
        st.markdown(risk_cards_html(risk), unsafe_allow_html=True)


def charts_from_payload(payload: dict | None, recs: list[Any]) -> dict[str, Any]:
    """Собрать charts_json как в FastAPI app.py."""
    sys.path.insert(0, str(ROOT / "app"))
    from vodopritok.web.viz import (
        funnel_from_stages,
        qsprpred_chart,
        qsprpred_mape_chart,
        stages_chart,
        tech_scores_chart,
        top5_chart,
    )

    charts: dict[str, Any] = {"tech": tech_scores_chart(recs)}
    if not payload:
        return charts

    stages = payload.get("stages", [])
    top5 = payload.get("top5", [])

    class _Stage:
        def __init__(self, d: dict):
            self.output_count = d.get("output_count", 0)

    stage_objs = [_Stage(s) for s in stages]
    total = stages[0].get("input_count", 500) if stages else 500
    charts["funnel"] = funnel_from_stages(total, stage_objs, len(top5))
    if top5:
        charts["top5"] = top5_chart(top5)
    charts["stages"] = stages_chart(stages)

    validation = payload.get("validation")
    if validation:
        q = qsprpred_chart(validation)
        if q:
            charts["qsprpred"] = q
    comparison = payload.get("comparison")
    mape = qsprpred_mape_chart(comparison)
    if mape:
        charts["qsprpred_mape"] = mape
    return charts


def home_charts_from_session(session: dict | None, recs: list[Any]) -> dict[str, Any]:
    sys.path.insert(0, str(ROOT / "app"))
    from vodopritok.web.viz import build_home_charts

    return build_home_charts(session, recs) or {"tech": charts_from_payload(None, recs)["tech"]}


def pitch_charts_from_session(session: dict | None, recs: list[Any], reservoir) -> dict[str, Any]:
    sys.path.insert(0, str(ROOT / "app"))
    from vodopritok.web.viz import build_pitch_charts

    return build_pitch_charts(session, recs, reservoir) or {}


def feasibility_chart_html(assessments: list[dict]) -> str:
    """Самодостаточный HTML для iframe (не зависит от CSS страницы)."""
    if not assessments:
        return ""
    items = sorted(assessments, key=lambda a: float(a.get("feasibility_score", 0)), reverse=True)
    cols = []
    for a in items:
        score = float(a.get("feasibility_score", 0))
        h = max(14, int(score / 100 * 170))
        ok = score >= 78
        clr = "#22c55e" if ok else "#8b5cf6"
        rid = a.get("recipe_id", a.get("mol_id", "?"))
        cols.append(
            f'<div class="feas-col">'
            f'<div class="feas-score" style="color:{clr}">{score:.0f}</div>'
            f'<div class="feas-bar" style="height:{h}px;background:{clr}"></div>'
            f'<div class="feas-id">{rid}</div>'
            f"</div>"
        )
    bars = "".join(cols)
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
body {{ margin:0; padding:12px 8px 4px; background:#1a2332; font-family:system-ui,sans-serif; color:#e2e8f0; }}
h2 {{ font-size:14px; font-weight:600; margin:0 0 10px; color:#f1f5f9; }}
.feas-chart {{ display:flex; align-items:flex-end; gap:6px; height:230px; border-bottom:1px solid #334155; }}
.feas-col {{ flex:1; display:flex; flex-direction:column; align-items:center; justify-content:flex-end; min-width:0; }}
.feas-bar {{ width:72%; min-height:12px; border-radius:4px 4px 0 0; }}
.feas-id {{ font-size:10px; color:#94a3b8; margin-top:6px; text-align:center; line-height:1.15; word-break:break-word; }}
.feas-score {{ font-size:13px; font-weight:700; margin-bottom:4px; }}
</style></head><body>
<h2>Feasibility top-5 для синтеза</h2>
<div class="feas-chart">{bars}</div>
</body></html>"""


def render_feasibility_chart(assessments: list[dict]) -> None:
    """Bar chart через iframe — стабильно на Streamlit Cloud."""
    html = feasibility_chart_html(assessments)
    if html:
        components.html(html, height=340, scrolling=False)


def render_economics_sliders(defaults: dict[str, float]) -> None:
    """OPEX-слайдеры как на /screening (логика через Python)."""
    sys.path.insert(0, str(ROOT / "app"))
    from vodopritok.economics import OpexScenario, analyze_opex

    st.markdown("### Экономика OPEX (интерактивно)")
    wc_before = st.slider("WC до, %", 50, 98, int(defaults.get("wc_before", 82)))
    wc_after = st.slider("WC после, %", 40, 90, int(defaults.get("wc_after", 64)))
    oil_rate = st.slider("Qn, t/d", 3.0, 40.0, float(defaults.get("oil_rate", 14.5)), 0.5)
    treatment = st.slider("Стоимость обработки, ₽", 300_000, 2_000_000, 900_000, 50_000)
    eco = analyze_opex(
        OpexScenario(
            name="case",
            water_cut_before_pct=wc_before,
            water_cut_after_pct=wc_after,
            oil_rate_tpd=oil_rate,
            treatment_cost_rub=treatment,
        )
    )
    measures = sorted(eco.measures, key=lambda m: m.get("estimated_annual_rub", 0), reverse=True)[:3]
    measures_html = ""
    if measures:
        items = "".join(
            f"<li>{m['measure']} — {m['estimated_annual_rub']:,.0f} ₽/год</li>".replace(",", " ")
            for m in measures
        )
        measures_html = f'<p class="muted" style="margin:0.75rem 0 0.35rem">Топ мероприятий по эффекту:</p><ul style="margin:0;padding-left:1.2rem;font-size:0.85rem">{items}</ul>'
    st.markdown(
        f"""
        <div class="eco-grid">
          <div class="eco-kpi"><span class="muted">OPEX воды до</span><strong>{eco.baseline_water_opex_rub:,.0f} ₽</strong></div>
          <div class="eco-kpi"><span class="muted">Экономия/год</span><strong>{eco.annual_savings_rub:,.0f} ₽</strong></div>
          <div class="eco-kpi"><span class="muted">Payback</span><strong>{eco.payback_months:.1f} мес</strong></div>
          <div class="eco-kpi"><span class="muted">NPV 3 года</span><strong>{eco.npv_3yr_rub:,.0f} ₽</strong></div>
          <div class="eco-kpi"><span class="muted">Сокращение воды</span><strong>{eco.water_reduction_m3_year:,.0f} m³/год</strong></div>
          <div class="eco-kpi"><span class="muted">OPEX воды после</span><strong>{eco.water_opex_after_rub:,.0f} ₽</strong></div>
        </div>{measures_html}
        """.replace(",", " "),
        unsafe_allow_html=True,
    )
    render_environmental_effect(
        eco,
        tech_id=str(defaults.get("tech_id", "hrpm")),
        wc_before=wc_before,
        wc_after=wc_after,
    )


def environmental_impact_html(impact: dict[str, Any]) -> str:
    notes = "".join(f"<li>{n}</li>" for n in impact.get("hse_notes", []))
    return f"""
    <section class="card env-panel highlight">
      <div class="env-header">
        <h2>Экологический эффект</h2>
        <span class="env-score">Eco-score {impact['eco_score']}/100</span>
      </div>
      <p class="muted">{impact.get('methodology_note', '')}</p>
      <div class="env-grid">
        <div class="env-kpi"><span class="muted">Сокращение воды</span><strong>{impact['water_reduction_m3_year']:,.0f} m³/год</strong></div>
        <div class="env-kpi"><span class="muted">Меньше сброса/подготовки</span><strong>{impact['disposal_reduction_m3_year']:,.0f} m³/год</strong></div>
        <div class="env-kpi"><span class="muted">Энергия подъёма</span><strong>−{impact['energy_savings_mwh_year']} МВт·ч/год</strong></div>
        <div class="env-kpi"><span class="muted">CO₂-прокси</span><strong>−{impact['co2_avoided_tons_year']} т/год</strong></div>
        <div class="env-kpi"><span class="muted">Объём закачки (ОПР)</span><strong>{impact['injection_volume_m3']} m³</strong></div>
        <div class="env-kpi"><span class="muted">Δ WC</span><strong>{impact['wc_reduction_pp']} п.п.</strong></div>
      </div>
      <div class="env-hse">
        <span class="env-badge tier-{impact['hse_tier']}">HSE: {impact['hse_tier_ru']}</span>
        <span class="muted">{impact['hse_label']}</span>
      </div>
      <ul class="env-notes">{notes}</ul>
    </section>
    """.replace(",", " ")


def render_environmental_effect(
    analysis,
    *,
    tech_id: str = "hrpm",
    wc_before: float,
    wc_after: float,
) -> None:
    sys.path.insert(0, str(ROOT / "app"))
    from vodopritok.environmental_impact import build_environmental_impact

    impact = build_environmental_impact(
        analysis,
        tech_id=tech_id,
        wc_before=wc_before,
        wc_after=wc_after,
    )
    st.markdown(environmental_impact_html(impact), unsafe_allow_html=True)


def ml_pipeline_badges(stages: list[dict]) -> None:
    badges = []
    for stage in stages:
        warn = "warn" if "fallback" in stage.get("tool", "").lower() else "ok"
        badges.append(
            f'<span class="ml-badge {warn}">{stage.get("name", "—")} · {stage.get("tool", "—")}</span>'
        )
    st.markdown(
        f'<section class="card"><h2>ML pipeline status</h2><div class="badge-row">{"".join(badges)}</div></section>',
        unsafe_allow_html=True,
    )


def eco_defaults_from_form(form: dict[str, Any], recs: list[Any] | None = None) -> dict[str, float]:
    sys.path.insert(0, str(ROOT / "app"))
    from vodopritok.economics import build_opex_plan
    from vodopritok.demo.context_builder import build_deliverable_context

    tech_id = recs[0].technology_id if recs else "hrpm"
    ctx = build_deliverable_context()
    if ctx:
        plan = build_opex_plan(ctx)
        return {
            "wc_before": ctx.reservoir.water_cut_pct,
            "wc_after": plan["scenario"].water_cut_after_pct,
            "oil_rate": ctx.reservoir.oil_rate_tpd,
            "tech_id": tech_id,
        }
    return {
        "wc_before": float(form.get("water_cut_pct", 82)),
        "wc_after": 64.0,
        "oil_rate": float(form.get("oil_rate_tpd", 14.5)),
        "tech_id": tech_id,
    }


def twin_charts_json_from_payload(profile: dict[str, Any]) -> dict[str, Any]:
    sys.path.insert(0, str(ROOT / "app"))
    from vodopritok.web.viz import economics_chart

    twins = profile["twins"]
    return {
        "radar": profile["radar"],
        "economics": economics_chart(twins[0]) if twins else None,
    }
