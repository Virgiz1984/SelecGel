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
inj = plan["injection"]

st.subheader("Скоринг скважины")
c1, c2, c3 = st.columns(3)
c1.metric("Скважина", plan.get("candidate_well", "—"))
c2.metric("Score", f"{plan.get('well_score', 0):.0f}/100")
c3.metric("Технология", plan.get("technology", "—")[:32])

st.subheader("Injection design")
st.json(inj)

st.subheader("Timeline ОПР")
st.dataframe(__import__("pandas").DataFrame(plan["timeline"]), width="stretch", hide_index=True)

st.subheader("KPI gate")
st.dataframe(__import__("pandas").DataFrame([plan["opr_gate"]]), width="stretch", hide_index=True)

if st.button("Сгенерировать .docx"):
    path = generate_opr_program_doc(ctx)
    st.success(f"Сохранено: {path.name}")

doc_path = OUTPUT_DIR / "04-programma-opr.docx"
data = file_download_bytes(doc_path)
if data:
    st.download_button("Скачать 04-programma-opr.docx", data, doc_path.name)
