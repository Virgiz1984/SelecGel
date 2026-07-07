"""План снижения OPEX."""

from __future__ import annotations

import streamlit as st

from sl_helpers import OpexScenario, analyze_opex, build_opex_plan, deliverable_context, generate_opex_plan_doc, file_download_bytes
from vodopritok.models import OUTPUT_DIR

st.header("План снижения OPEX")

ctx = deliverable_context()
if not ctx:
    st.warning("Сначала запустите скрининг.")
    st.stop()

plan = build_opex_plan(ctx)
scenario = plan["scenario"]
analysis = plan["analysis"]

st.subheader("Сценарий")
c1, c2, c3, c4 = st.columns(4)
c1.metric("WC до", f"{scenario.water_cut_before_pct:.0f} %")
c2.metric("WC после", f"{scenario.water_cut_after_pct:.0f} %")
c3.metric("Экономия/год", f"{analysis.annual_savings_rub:,.0f} ₽".replace(",", " "))
c4.metric("Payback", f"{analysis.payback_months:.0f} мес")

wc_before = st.slider("WC до, %", 50.0, 95.0, float(scenario.water_cut_before_pct))
wc_after = st.slider("WC после, %", 40.0, 90.0, float(scenario.water_cut_after_pct))
oil_rate = st.number_input("Дебит нефти, т/сут", value=float(scenario.oil_rate_tpd))

live = analyze_opex(
    OpexScenario(
        name="live",
        water_cut_before_pct=wc_before,
        water_cut_after_pct=wc_after,
        oil_rate_tpd=oil_rate,
        treatment_cost_rub=scenario.treatment_cost_rub,
    )
)
lc1, lc2, lc3 = st.columns(3)
lc1.metric("NPV 3 года", f"{live.npv_3yr_rub:,.0f} ₽".replace(",", " "))
lc2.metric("Снижение воды", f"{live.water_reduction_m3_year:,.0f} m³/год".replace(",", " "))
lc3.metric("Чистая выгода/год", f"{live.net_annual_benefit_rub:,.0f} ₽".replace(",", " "))

st.subheader("10 мероприятий")
measures = sorted(plan["measures"], key=lambda m: m.get("estimated_annual_rub", 0), reverse=True)
st.dataframe(__import__("pandas").DataFrame(measures), width="stretch", hide_index=True)

if st.button("Сгенерировать .docx"):
    path = generate_opex_plan_doc(ctx)
    st.success(f"Сохранено: {path.name}")

doc_path = OUTPUT_DIR / "06-plan-snizheniya-opex.docx"
data = file_download_bytes(doc_path)
if data:
    st.download_button("Скачать 06-plan-snizheniya-opex.docx", data, doc_path.name)
