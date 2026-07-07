"""Pitch для заказчика."""

from __future__ import annotations

import streamlit as st

from sl_helpers import PITCH_POINTS, TZ_MAPPING, analyze_opex, build_opex_plan, deliverable_context, OpexScenario

st.header("Для заказчика")

st.markdown("### Что вы получаете от эксперта с технологией SelecGel")
st.markdown(
    "Не подписку на софт — **ведение проекта** с инструментом, "
    "который сокращает перебор рецептур и повышает вероятность успеха ОВП."
)

st.subheader("5 отличий от «купить реагент у сервиса»")
for i, point in enumerate(PITCH_POINTS, 1):
    st.markdown(f"{i}. {point}")

st.subheader("Покрытие ТЗ")
rows = [{"Требование ТЗ": r["tz"], "Deliverable": r["deliverable"], "Как показываю": r["demo"]} for r in TZ_MAPPING]
st.dataframe(__import__("pandas").DataFrame(rows), use_container_width=True, hide_index=True)

ctx = deliverable_context()
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
    st.subheader("Экономика внедрения (preview)")
    c1, c2, c3 = st.columns(3)
    c1.metric("Экономия воды/год", f"{eco.annual_savings_rub:,.0f} ₽".replace(",", " "))
    c2.metric("Payback", f"{eco.payback_months:.0f} мес")
    c3.metric("NPV 3 года", f"{eco.npv_3yr_rub:,.0f} ₽".replace(",", " "))
else:
    st.info("Запустите скрининг — появится экономический preview по вашему кейсу.")
