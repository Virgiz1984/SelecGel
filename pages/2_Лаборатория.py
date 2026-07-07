"""Программа лабораторных исследований."""

from __future__ import annotations

import streamlit as st

from sl_helpers import build_lab_program, deliverable_context, generate_lab_program_doc, file_download_bytes
from vodopritok.models import OUTPUT_DIR

st.header("Программа лабораторных исследований")

ctx = deliverable_context()
if not ctx:
    st.warning("Сначала запустите скрининг на странице **Скрининг**.")
    st.stop()

plan = build_lab_program(ctx)

c1, c2, c3 = st.columns(3)
c1.metric("Track 1 (primary)", plan["track1"]["name"])
c2.metric("Track 2 (backup)", plan["track2"]["name"])
c3.metric("Lab gate Frrw", f"≥ {plan['gate_kpi']['frrw_min']}")

st.subheader("Очередь синтеза")
st.dataframe(__import__("pandas").DataFrame(plan["synthesis_queue"]), use_container_width=True, hide_index=True)

st.subheader("Timeline")
st.dataframe(__import__("pandas").DataFrame(plan["timeline"]), use_container_width=True, hide_index=True)

st.subheader("DoE matrix")
st.dataframe(__import__("pandas").DataFrame(plan["doe_matrix"]), use_container_width=True, hide_index=True)

if st.button("Сгенерировать .docx"):
    path = generate_lab_program_doc(ctx)
    st.success(f"Сохранено: {path.name}")

doc_path = OUTPUT_DIR / "02-programma-laboratornyh-issledovaniy.docx"
data = file_download_bytes(doc_path)
if data:
    st.download_button("Скачать 02-programma-laboratornyh-issledovaniy.docx", data, doc_path.name)
