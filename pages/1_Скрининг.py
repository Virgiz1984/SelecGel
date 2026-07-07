"""Live demo: 500 → top-5."""

from __future__ import annotations

import streamlit as st

from sl_helpers import (
    form_defaults,
    funnel_dataframe,
    library_stats,
    load_session,
    mechanisms,
    recommend_technologies,
    reservoir_from_form,
    run_screening,
    top5_dataframe,
)

st.header("Скрининг 500 → top-5")

defaults = form_defaults()
session = load_session()
expert_default = session.get("expert", "Эксперт по ОВП") if session else "Эксперт по ОВП"
company_default = session.get("company", "Заказчик") if session else "Заказчик"

with st.form("reservoir_form"):
    c1, c2 = st.columns(2)
    with c1:
        expert = st.text_input("Эксперт", expert_default)
        field_name = st.text_input("Месторождение", defaults.get("field_name", ""))
        well_name = st.text_input("Скважина", defaults.get("well_name", ""))
        temperature_c = st.number_input("T, °C", value=float(defaults.get("temperature_c", 85)))
        salinity_g_l = st.number_input("Минeralization, g/L", value=float(defaults.get("salinity_g_l", 130)))
        permeability_md = st.number_input("Проницаемость, mD", value=float(defaults.get("permeability_md", 450)))
    with c2:
        company = st.text_input("Заказчик", company_default)
        water_cut_pct = st.number_input("Обводнённость, %", value=float(defaults.get("water_cut_pct", 82)))
        oil_rate_tpd = st.number_input("Дебит нефти, т/сут", value=float(defaults.get("oil_rate_tpd", 14.5)))
        api_gravity = st.number_input("API", value=float(defaults.get("api_gravity", 21)))
        lithology = st.selectbox(
            "Литология",
            ["sandstone", "carbonate", "shale"],
            index=["sandstone", "carbonate", "shale"].index(defaults.get("lithology", "sandstone")),
        )
        mech_ids = [m["id"] for m in mechanisms()]
        mech_default = defaults.get("water_mechanism", "coning")
        water_mechanism = st.selectbox(
            "Механизм обводнения",
            mech_ids,
            index=mech_ids.index(mech_default) if mech_default in mech_ids else 0,
            format_func=lambda x: next(m["name_ru"] for m in mechanisms() if m["id"] == x),
        )
        has_fracture = st.checkbox("Есть трещины / каналы", value=bool(defaults.get("has_fracture")))

    run = st.form_submit_button("Запустить конвейер", type="primary")

form = {
    "field_name": field_name,
    "well_name": well_name,
    "temperature_c": temperature_c,
    "salinity_g_l": salinity_g_l,
    "permeability_md": permeability_md,
    "water_cut_pct": water_cut_pct,
    "oil_rate_tpd": oil_rate_tpd,
    "api_gravity": api_gravity,
    "lithology": lithology,
    "water_mechanism": water_mechanism,
    "has_fracture": has_fracture,
}

reservoir = reservoir_from_form(form)
recs = recommend_technologies(reservoir, top_n=3)
lib = library_stats(500)

st.subheader("Патентная библиотека")
lc1, lc2, lc3 = st.columns(3)
lc1.metric("Молекул", lib["count"])
lc2.metric("Классов", len(lib["classes"]))
lc3.metric("Патентов", lib["unique_patents"])

if run:
    with st.spinner("QSPR → QSAR → top-5…"):
        try:
            payload = run_screening(form, expert, company)
            st.session_state["screening_payload"] = payload
            st.success("Конвейер завершён, сессия сохранена.")
        except Exception as exc:
            st.error(str(exc))

payload = st.session_state.get("screening_payload")
if not payload and session and session.get("pipeline"):
    st.info("Показаны данные из последней сохранённой сессии. Нажмите «Запустить» для пересчёта.")
    from dataclasses import asdict

    from vodopritok.demo.context_builder import build_fto_rows
    from vodopritok.demo.risk_dashboard import build_risk_dashboard
    from vodopritok.pipeline.models import PipelineResult, PipelineStage, QSARScore, QSPRScore

    pipe = session["pipeline"]
    stages = [PipelineStage(**s) for s in pipe.get("stages", [])]
    top5 = [QSARScore(**t) for t in pipe.get("top5", [])]
    result = PipelineResult(
        stages=stages,
        top5=top5,
        qspr_candidates=[],
        total_input=pipe.get("total_input", 500),
        library_path=pipe.get("library_path", ""),
    )
    top5_dicts = pipe.get("top5", [])
    payload = {
        "result": result,
        "top5": top5_dicts,
        "recommendations": recs,
        "fto_rows": build_fto_rows(top5_dicts),
        "risk_dashboard": build_risk_dashboard(
            reservoir, top5_dicts, recs, stages=pipe.get("stages", [])
        ),
        "library_stats": pipe.get("library_stats") or lib,
    }

st.subheader("Рекомендация технологий")
tech_df = __import__("pandas").DataFrame(
    [{"Технология": r.name_ru, "Score": round(r.score, 1), "Track": r.rd_track} for r in recs]
)
st.bar_chart(tech_df.set_index("Технология")["Score"])

if payload:
    result = payload["result"]
    st.subheader("Воронка конвейера")
    stages = [s if isinstance(s, dict) else __import__("dataclasses").asdict(s) for s in result.stages]
    funnel = funnel_dataframe(stages, top_n=len(payload["top5"]))
    st.bar_chart(funnel.set_index("Этап")["Молекул"])

    st.subheader("Top-5")
    st.dataframe(top5_dataframe(payload["top5"]), use_container_width=True, hide_index=True)

    if payload.get("fto_rows"):
        st.subheader("FTO / патенты")
        st.dataframe(__import__("pandas").DataFrame(payload["fto_rows"]), use_container_width=True, hide_index=True)

    risk = payload.get("risk_dashboard")
    if risk:
        st.subheader("Risk dashboard")
        rc1, rc2, rc3 = st.columns(3)
        rc1.metric("Общий риск", risk.get("overall_label", "—"))
        rc2.metric("Lab gate", "PASS" if risk.get("lab_gate_pass") else "FAIL")
        rc3.metric("FTO", risk.get("fto_summary", "—"))
