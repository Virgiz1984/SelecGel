"""Генерация deliverables .docx."""

from __future__ import annotations

import streamlit as st

from sl_helpers import deliverable_context, generate_reports_zip, file_download_bytes
from vodopritok.models import OUTPUT_DIR
from vodopritok.reports import generate_all_deliverables

st.header("Отчёты и deliverables")

ctx = deliverable_context()
if not ctx:
    st.warning("Сначала запустите скрининг — контекст проекта берётся из сессии.")
    st.stop()

st.write(f"**{ctx.company_name}** · {ctx.reservoir.field_name} · {ctx.reservoir.well_name}")

if st.button("Сгенерировать все 6 документов", type="primary"):
    with st.spinner("Генерация .docx…"):
        paths = generate_all_deliverables(ctx)
    st.success(f"Готово: {len(paths)} файлов в `{OUTPUT_DIR}`")
    for path in paths:
        data = file_download_bytes(path)
        if data:
            st.download_button(f"Скачать {path.name}", data, path.name, key=path.name)

st.divider()
if st.button("Скачать ZIP (все deliverables)"):
    with st.spinner("Упаковка ZIP…"):
        zip_bytes = generate_reports_zip()
    st.download_button(
        "Скачать selecgel-deliverables.zip",
        zip_bytes,
        "selecgel-deliverables.zip",
        mime="application/zip",
    )

st.subheader("Файлы в output/")
if OUTPUT_DIR.exists():
    docs = sorted(OUTPUT_DIR.glob("*.docx"))
    if docs:
        for path in docs:
            st.text(f"• {path.name} ({path.stat().st_size // 1024} KB)")
    else:
        st.caption("Пока нет .docx — нажмите «Сгенерировать».")
else:
    st.caption("Папка output ещё не создана.")
