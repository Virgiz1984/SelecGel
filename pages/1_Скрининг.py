"""Live demo: 500 → top-5."""

from __future__ import annotations

import streamlit as st

from sl_helpers import (
    form_defaults,
    library_stats,
    load_session,
    mechanisms,
    payload_from_session,
    rd_track_strategy,
    recommend_technologies,
    reservoir_from_form,
    run_screening,
    top5_dataframe,
)
from st_charts import render_screening_charts

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
        salinity_g_l = st.number_input("Мineralization, g/L", value=float(defaults.get("salinity_g_l", 130)))
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
rd_tracks = rd_track_strategy(reservoir)

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
    payload = payload_from_session(session, reservoir, recs, lib)

render_screening_charts(payload, recs)

if payload:
    st.subheader("Двухтрековая стратегия R&D")
    st.caption(rd_tracks.get("screening_note", ""))
    tc1, tc2 = st.columns(2)
    t1 = rd_tracks.get("track1")
    t2 = rd_tracks.get("track2")
    with tc1:
        st.markdown(f"**Track 1 — primary**  \n{t1.name_ru if t1 else '—'}  \n{t1.track if t1 else ''}")
    with tc2:
        st.markdown(f"**Track 2 — backup**  \n{t2.name_ru if t2 else '—'}  \n{t2.track if t2 else ''}")

    st.subheader("Top-5 для лаборатории")
    st.dataframe(top5_dataframe(payload["top5"]), width="stretch", hide_index=True)

    if payload.get("fto_rows"):
        st.subheader("FTO / патенты")
        st.dataframe(__import__("pandas").DataFrame(payload["fto_rows"]), width="stretch", hide_index=True)
