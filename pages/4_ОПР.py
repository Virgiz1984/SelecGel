"""Программа опытно-промышленных работ."""

from __future__ import annotations

import streamlit as st

from sl_helpers import build_opr_program, deliverable_context, generate_opr_program_doc, file_download_bytes
from vodopritok.models import OUTPUT_DIR

st.header("Программа ОПР")

ctx = deliverable_context()
if not ctx:
    st.warning("Сначала запустите скрининг.")
    st.stop()

plan = build_opr_program(ctx)

st.subheader("Скоринг скважины")
well = plan["well_scoring"]
c1, c2, c3 = st.columns(3)
c1.metric("Скважина", well.get("well_name", "—"))
c2.metric("Score", well.get("total_score", "—"))
c3.metric("Рекомендация", well.get("recommendation", "—"))

st.subheader("Injection design")
inj = plan["injection_design"]
st.json(inj)

st.subheader("Timeline ОПР")
st.dataframe(__import__("pandas").DataFrame(plan["timeline"]), use_container_width=True, hide_index=True)

st.subheader("KPI gate")
st.dataframe(__import__("pandas").DataFrame([plan["opr_gate"]]), use_container_width=True, hide_index=True)

if st.button("Сгенерировать .docx"):
    path = generate_opr_program_doc(ctx)
    st.success(f"Сохранено: {path.name}")

doc_path = OUTPUT_DIR / "04-programma-opr.docx"
data = file_download_bytes(doc_path)
if data:
    st.download_button("Скачать 04-programma-opr.docx", data, doc_path.name)
