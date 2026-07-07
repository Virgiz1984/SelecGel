"""Цифровой профиль реагента — radar Top-5 + economics."""

from __future__ import annotations

import streamlit as st

from sl_helpers import build_profile_payload
from st_charts import (
    chart_twin_economics,
    radar_gate_summary_table,
    show_chart,
    show_plotly,
    twin_radar_figure,
)

st.header("Профиль реагента")

payload = build_profile_payload()
if not payload:
    st.warning("Сначала запустите **Скрининг** — профиль строится по top-5 in silico.")
    st.stop()

twins = payload["twins"]
bundle = payload["radar"]
st.caption(
    f"Сравнение Top-{len(twins)} in silico · lab overlay ({payload['lab_count']} строк CSV) · "
    f"T пласта {payload['reservoir'].temperature_c:.0f}°C"
)

rank_options = list(range(1, len(twins) + 1))
default_ranks = [r for r in rank_options if any(c.get("rank") == r and c.get("default_visible") for c in bundle.get("candidates", []))]
if not default_ranks:
    default_ranks = [1]

tc1, tc2 = st.columns([2, 1])
with tc1:
    selected = st.multiselect(
        "Кандидаты на radar",
        options=rank_options,
        default=default_ranks,
        format_func=lambda r: f"#{r} {twins[r - 1].mol_id}",
    )
    show_lab = st.checkbox("Lab overlay (CSV по rank)", value=True)
with tc2:
    lead_idx = max(0, (selected[0] - 1) if selected else 0)
    show_chart(chart_twin_economics(twins[lead_idx]))

if selected:
    show_plotly(twin_radar_figure(bundle, selected, show_lab=show_lab))
    gate_df = radar_gate_summary_table(bundle, selected)
    if not gate_df.empty:
        st.subheader("Lab gate по осям")
        st.dataframe(gate_df, width="stretch", hide_index=True)
else:
    st.info("Выберите хотя бы одного кандидата для radar.")

st.subheader("Карточки кандидатов")
for i, twin in enumerate(twins, start=1):
    with st.expander(f"#{i} · {twin.mol_id} · confidence {twin.confidence_score}%", expanded=(i == 1)):
        st.write(twin.recommendation)
        st.caption(twin.technology_class)
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
