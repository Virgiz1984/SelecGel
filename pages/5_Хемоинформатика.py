"""Оценка синтеза с хемоинформатикой."""

from __future__ import annotations

import streamlit as st

from sl_helpers import build_synthesis_assessment, deliverable_context, generate_synthesis_assessment_doc, file_download_bytes
from vodopritok.models import OUTPUT_DIR

st.header("Хемоинформатика — оценка синтеза")

ctx = deliverable_context()
if not ctx:
    st.warning("Сначала запустите скрининг.")
    st.stop()

assessment = build_synthesis_assessment(ctx)

c1, c2, c3 = st.columns(3)
c1.metric("Feasibility (avg top-5)", f"{assessment['summary']['avg_feasibility']:.0f}/100")
c2.metric("FTO low-risk", assessment["summary"]["fto_low_risk_count"])
c3.metric("Monomer supply OK", assessment["summary"]["monomer_supply_ok"])

st.subheader("Top-5 feasibility")
rows = []
for item in assessment["candidates"]:
    rows.append(
        {
            "ID": item["mol_id"],
            "Feasibility": item["feasibility_score"],
            "FTO": item["fto_risk"],
            "Monomers": item["monomer_supply"],
            "Lead time, нед": item["synthesis_lead_weeks"],
        }
    )
st.dataframe(__import__("pandas").DataFrame(rows), use_container_width=True, hide_index=True)

st.subheader("Pipeline stats")
st.json(assessment["pipeline_stats"])

if st.button("Сгенерировать .docx"):
    path = generate_synthesis_assessment_doc(ctx)
    st.success(f"Сохранено: {path.name}")

doc_path = OUTPUT_DIR / "01b-ocenka-sintez-khemoinformatika.docx"
data = file_download_bytes(doc_path)
if data:
    st.download_button("Скачать 01b-ocenka-sintez-khemoinformatika.docx", data, doc_path.name)
