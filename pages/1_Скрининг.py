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
    top5_predictions_flat,
    top5_table_html,
    upload_lab_csv,
)
from sl_webui import (
    charts_from_payload,
    eco_defaults_from_form,
    ml_pipeline_badges,
    render_economics_sliders,
    render_risk_dashboard,
    screening_charts_widget,
    setup_page,
)

setup_page("screening", "Screening")

st.markdown(
    """
    <section class="card">
      <h2>Виртуальный screening</h2>
      <p class="muted">Параметры пласта заказчика → конвейер, top-5, экономика и one-pager для встречи.</p>
    </section>
    """,
    unsafe_allow_html=True,
)

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
        salinity_g_l = st.number_input("Mineralization, g/L", value=float(defaults.get("salinity_g_l", 130)))
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

    run = st.form_submit_button("Запустить (500 → top-5)", type="primary")

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

st.markdown("### Lab CSV (калибровка QSPRpred)")
st.caption("Колонки: rank, frrw, frro, … — rank сопоставляется с top-5.")
uploaded = st.file_uploader("Загрузить CSV", type=["csv"], key="lab_csv")
if uploaded is not None:
    if st.button("Загрузить и пересчитать"):
        upload_lab_csv(uploaded.getvalue())
        st.session_state.pop("screening_payload", None)
        st.success("Lab CSV загружен — QSPRpred пересчитан.")
        st.rerun()

st.markdown(
    f"""
    <section class="card">
      <h2>Патентная библиотека</h2>
      <p class="muted">{lib.get("description", "")}</p>
      <div class="kpi-row">
        <span class="kpi"><strong>{lib["count"]}</strong> SMILES</span>
        <span class="kpi"><strong>{lib["unique_patents"]}</strong> patent refs</span>
      </div>
    </section>
    """,
    unsafe_allow_html=True,
)

if run:
    with st.spinner("QSPR → QSAR → top-5…"):
        try:
            payload = run_screening(form, expert, company)
            st.session_state["screening_payload"] = payload
            st.success("Результат сохранён — данные подставятся в 6 .docx.")
        except Exception as exc:
            st.error(str(exc))

payload = st.session_state.get("screening_payload")
if not payload and session and session.get("pipeline"):
    st.info("Показаны данные из последней сохранённой сессии. Нажмите «Запустить» для пересчёта.")
    payload = payload_from_session(session, reservoir, recs, lib)

charts = charts_from_payload(payload, recs)
screening_charts_widget(charts)

if payload:
    if top5_predictions_flat(payload.get("top5", [])):
        st.warning(
            "Прогнозы top-5 выглядят одинаковыми (старая сессия или ML fallback). "
            "Нажмите **«Запустить (500 → top-5)»** ещё раз для пересчёта."
        )
    render_risk_dashboard(payload.get("risk_dashboard"))
    render_economics_sliders(eco_defaults_from_form(form, recs))
    ml_pipeline_badges(payload.get("stages", []))

    st.markdown(
        f"""
        <section class="card highlight">
          <h2>Двухтрековая стратегия R&D</h2>
          <p class="muted">{rd_tracks.get("screening_note", "")}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    tc1, tc2 = st.columns(2)
    t1 = rd_tracks.get("track1")
    t2 = rd_tracks.get("track2")
    with tc1:
        st.markdown(f"**Track 1 — primary**  \n{t1.name_ru if t1 else '—'}  \n{t1.track if t1 else ''}")
    with tc2:
        st.markdown(f"**Track 2 — backup**  \n{t2.name_ru if t2 else '—'}  \n{t2.track if t2 else ''}")

    comparison = payload.get("comparison")
    if comparison and comparison.get("after"):
        before_m = comparison.get("before", {}).get("mape")
        after_m = comparison.get("after", {}).get("mape")
        if before_m is not None and after_m is not None:
            st.caption(f"QSPRpred MAPE: {before_m}% → {after_m}% после lab CSV")

    st.markdown(top5_table_html(payload["top5"]), unsafe_allow_html=True)

    if payload.get("fto_rows"):
        st.markdown("### FTO / патентная оценка")
        st.dataframe(__import__("pandas").DataFrame(payload["fto_rows"]), width="stretch", hide_index=True)
else:
    st.markdown("### Рекомендация технологии (до screening)")
    rec_rows = [
        {"#": r.rank, "Технология": r.name_ru, "Track": r.track, "Score": f"{r.score:.0f}"}
        for r in recs
    ]
    st.dataframe(__import__("pandas").DataFrame(rec_rows), width="stretch", hide_index=True)
