"""Программа лабораторных исследований."""

from __future__ import annotations

import streamlit as st

from sl_helpers import build_lab_program, deliverable_context, generate_lab_program_doc, file_download_bytes
from sl_webui import setup_page
from vodopritok.models import OUTPUT_DIR

setup_page("lab", "Лаборатория")

st.markdown("### Программа лабораторных исследований")

ctx = deliverable_context()
if not ctx:
    st.warning("Сначала запустите скрининг на странице **Скрининг**.")
    st.stop()

plan = build_lab_program(ctx)
tracks = plan["tracks"]
t1 = tracks.get("track1")
t2 = tracks.get("track2")

c1, c2, c3 = st.columns(3)
c1.metric("Track 1 (primary)", t1.name_ru if t1 else "RPM")
c2.metric("Track 2 (backup)", t2.name_ru if t2 else "Thermotropic gel")
c3.metric("Рецептур Track 1", len(plan["track1_candidates"]))

st.caption("Lab gate Phase 2: Frrw ≥ 5, Frro ≤ 2 (см. gate criteria ниже)")

st.subheader("Очередь синтеза")
st.dataframe(__import__("pandas").DataFrame(plan["synthesis_queue"]), width="stretch", hide_index=True)

st.subheader("Timeline")
st.dataframe(__import__("pandas").DataFrame(plan["timeline"]), width="stretch", hide_index=True)

st.subheader("Gate criteria")
st.dataframe(__import__("pandas").DataFrame(plan["gate_criteria"]), width="stretch", hide_index=True)

st.subheader("DoE matrix")
st.dataframe(__import__("pandas").DataFrame(plan["doe_runs"]), width="stretch", hide_index=True)

if st.button("Сгенерировать .docx"):
    path = generate_lab_program_doc(ctx)
    st.success(f"Сохранено: {path.name}")

doc_path = OUTPUT_DIR / "02-programma-laboratornyh-issledovaniy.docx"
data = file_download_bytes(doc_path)
if data:
    st.download_button("Скачать 02-programma-laboratornyh-issledovaniy.docx", data, doc_path.name)
