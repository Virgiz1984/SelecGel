"""Цифровой профиль реагента — radar Top-5 + economics."""

from __future__ import annotations

import streamlit as st

from sl_helpers import build_profile_payload
from sl_webui import setup_page, twin_charts_json_from_payload, twin_charts_widget

setup_page("twin", "Профиль")

payload = build_profile_payload()
if not payload:
    st.markdown(
        '<section class="card"><p class="muted">Сначала запустите screening.</p></section>',
        unsafe_allow_html=True,
    )
    st.page_link("pages/1_Скрининг.py", label="Перейти к screening")
    st.stop()

twins = payload["twins"]
st.markdown(
    f"""
    <section class="card">
      <h2>Цифровой профиль реагента</h2>
      <p class="muted">Сравнение Top-{len(twins)} in silico, lab overlay ({payload['lab_count']} строк CSV) и gate по 5 осям.</p>
    </section>
    """,
    unsafe_allow_html=True,
)

twin_charts = twin_charts_json_from_payload(payload)
twins_meta = [{"mol_id": t.mol_id} for t in twins]
twin_charts_widget(twin_charts, twins_meta, height=560)

st.caption(
    "Наведите на точку — норм. балл и сырое значение (Frrw, Frro, T°C). "
    "Пунктир Lab — данные из CSV по rank."
)

for i, twin in enumerate(twins, start=1):
    st.markdown(
        f"""
        <section class="card">
          <div class="twin-header">
            <h3>#{i} · {twin.mol_id}</h3>
            <span class="confidence">Confidence {twin.confidence_score}%</span>
          </div>
          <p>{twin.recommendation}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Свойства (прогноз)**")
        for key, val in twin.predicted_properties.items():
            st.text(f"{key}: {val}")
    with c2:
        st.markdown("**Lab gate**")
        for key, val in twin.lab_gate.items():
            st.text(f"{key}: {val}")
    st.markdown("**Окно применения**")
    st.json(twin.application_window)
