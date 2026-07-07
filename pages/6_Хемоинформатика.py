"""Оценка синтеза с хемоинформатикой."""

from __future__ import annotations

import streamlit as st

from sl_helpers import build_synthesis_assessment, deliverable_context, generate_synthesis_assessment_doc, file_download_bytes
from sl_webui import setup_page
from st_charts import chart_feasibility, show_chart
from vodopritok.models import OUTPUT_DIR

setup_page("chem", "Хемоинформатика")

st.markdown("### Хемоинформатика — оценка синтеза")

ctx = deliverable_context()
if not ctx:
    st.warning("Сначала запустите скрининг.")
    st.stop()

assessment = build_synthesis_assessment(ctx)
items = assessment["assessments"]
pipeline = assessment["pipeline"]
monomers = assessment["monomer_supply"]

c1, c2, c3, c4 = st.columns(4)
avg_score = sum(a["feasibility_score"] for a in items) / max(len(items), 1)
c1.metric("Feasibility (avg)", f"{avg_score:.0f}/100")
c2.metric("Рекомендовано к синтезу", assessment["recommended_count"])
c3.metric("FTO low-risk", sum(1 for a in items if a["fto_risk"] == "low"))
c4.metric("Мономеров OK", sum(1 for m in monomers if m.get("fit_note") == "OK"))

show_chart(chart_feasibility(items))

st.subheader("Top-5 feasibility")
rows = [
    {
        "Rank": a["rank"],
        "ID": a["recipe_id"],
        "Feasibility": a["feasibility_score"],
        "FTO": a["fto_risk"],
        "Priority": a["lab_priority"],
        "Verdict": a["verdict"],
    }
    for a in items
]
st.dataframe(__import__("pandas").DataFrame(rows), width="stretch", hide_index=True)

st.subheader("Pipeline")
st.json(pipeline)

if st.button("Сгенерировать .docx"):
    path = generate_synthesis_assessment_doc(ctx)
    st.success(f"Сохранено: {path.name}")

doc_path = OUTPUT_DIR / "01b-ocenka-sintez-khemoinformatika.docx"
data = file_download_bytes(doc_path)
if data:
    st.download_button("Скачать 01b-ocenka-sintez-khemoinformatika.docx", data, doc_path.name)
