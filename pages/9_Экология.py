"""Экологический эффект технологии ОВП."""

from __future__ import annotations

import streamlit as st

from sl_helpers import deliverable_context, form_defaults, load_session, recommend_technologies, reservoir_from_form
from sl_webui import eco_defaults_from_form, render_environmental_effect, setup_page
from vodopritok.economics import OpexScenario, analyze_opex, build_opex_plan

setup_page("environment", "Экология")

st.markdown(
    """
    <section class="card">
      <h2>Экологический эффект</h2>
      <p class="muted">
        Демо-оценка: сокращение добычи/сброса воды → энергия подъёма и CO₂-прокси;
        HSE-профиль — по классу технологии (Track 1/2). Не заменяет LCA/ОВОС.
      </p>
    </section>
    """,
    unsafe_allow_html=True,
)

session = load_session()
form = form_defaults()
recs = recommend_technologies(reservoir_from_form(form), top_n=3)

if not session or not session.get("pipeline"):
    st.warning("Сначала запустите **Скрининг** — расчёт привязан к вашему кейсу и top-5.")
    st.page_link("pages/1_Скрининг.py", label="Запустить screening")
    st.stop()

ctx = deliverable_context()
plan = build_opex_plan(ctx) if ctx else None
defaults = eco_defaults_from_form(form, recs)

if plan:
    scenario = plan["scenario"]
    wc_before = st.slider("WC до, %", 50, 98, int(scenario.water_cut_before_pct))
    wc_after = st.slider("WC после, %", 40, 90, int(scenario.water_cut_after_pct))
    oil_rate = st.slider("Qn, t/d", 3.0, 40.0, float(scenario.oil_rate_tpd), 0.5)
    treatment = st.slider("Стоимость обработки, ₽", 300_000, 2_000_000, int(scenario.treatment_cost_rub), 50_000)
    tech_id = recs[0].technology_id if recs else str(defaults.get("tech_id", "hrpm"))
else:
    wc_before = st.slider("WC до, %", 50, 98, int(defaults.get("wc_before", 82)))
    wc_after = st.slider("WC после, %", 40, 90, int(defaults.get("wc_after", 64)))
    oil_rate = st.slider("Qn, t/d", 3.0, 40.0, float(defaults.get("oil_rate", 14.5)), 0.5)
    treatment = st.slider("Стоимость обработки, ₽", 300_000, 2_000_000, 900_000, 50_000)
    tech_id = str(defaults.get("tech_id", "hrpm"))

eco = analyze_opex(
    OpexScenario(
        name="environment",
        water_cut_before_pct=wc_before,
        water_cut_after_pct=wc_after,
        oil_rate_tpd=oil_rate,
        treatment_cost_rub=treatment,
    )
)

render_environmental_effect(
    eco,
    tech_id=tech_id,
    wc_before=wc_before,
    wc_after=wc_after,
)

st.caption("Тот же блок доступен на **Скрининг** (после конвейера) и **OPEX**.")
