"""Pitch для заказчика."""

from __future__ import annotations

import streamlit as st

from sl_helpers import PITCH_POINTS, TZ_MAPPING, analyze_opex, build_opex_plan, deliverable_context, form_defaults, load_session, OpexScenario, recommend_technologies, reservoir_from_form
from sl_webui import pitch_charts_from_session, pitch_charts_widget, setup_page

setup_page("pitch", "Для заказчика")

st.markdown(
    """
    <section class="card">
      <h2>Для заказчика</h2>
      <p class="hero-text">
        Не подписку на софт — <strong>ведение проекта</strong> с инструментом,
        который сокращает перебор рецептур и повышает вероятность успеха ОВП.
      </p>
    </section>
    """,
    unsafe_allow_html=True,
)

st.markdown("### 5 отличий от «купить реагент у сервиса»")
for i, point in enumerate(PITCH_POINTS, 1):
    st.markdown(f"{i}. {point}")

st.markdown("### Покрытие ТЗ")
rows = [{"Требование ТЗ": r["tz"], "Deliverable": r["deliverable"], "Как показываю": r["demo"]} for r in TZ_MAPPING]
st.dataframe(__import__("pandas").DataFrame(rows), width="stretch", hide_index=True)

ctx = deliverable_context()
session = load_session()
form = form_defaults()
reservoir = reservoir_from_form(form)
recs = recommend_technologies(reservoir, top_n=3)

st.markdown("### Визуализация для заказчика")
charts = pitch_charts_from_session(session, recs, reservoir)
pitch_charts_widget(charts)

if ctx:
    plan = build_opex_plan(ctx)
    scenario = plan["scenario"]
    eco = analyze_opex(
        OpexScenario(
            name="pitch",
            water_cut_before_pct=scenario.water_cut_before_pct,
            water_cut_after_pct=scenario.water_cut_after_pct,
            oil_rate_tpd=scenario.oil_rate_tpd,
            treatment_cost_rub=scenario.treatment_cost_rub,
        )
    )
    st.markdown("### Экономика внедрения (preview)")
    st.markdown(
        f"""
        <div class="eco-grid">
          <div class="eco-kpi"><span class="muted">Экономия воды/год</span><strong>{eco.annual_savings_rub:,.0f} ₽</strong></div>
          <div class="eco-kpi"><span class="muted">Payback</span><strong>{eco.payback_months:.0f} мес</strong></div>
          <div class="eco-kpi"><span class="muted">NPV 3 года</span><strong>{eco.npv_3yr_rub:,.0f} ₽</strong></div>
        </div>
        """.replace(",", " "),
        unsafe_allow_html=True,
    )
else:
    st.info("Запустите скрининг — появится экономический preview по вашему кейсу.")
