"""SelecGel — демо на Streamlit Cloud."""

from __future__ import annotations

import streamlit as st

from sl_helpers import PITCH_POINTS, PRODUCT_NAME, PRODUCT_TAGLINE, TZ_MAPPING, form_defaults, load_session, rdkit_available

st.set_page_config(
    page_title=PRODUCT_NAME,
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title(f"{PRODUCT_NAME}")
st.caption(PRODUCT_TAGLINE)

session = load_session()
if session and session.get("pipeline"):
    st.success("Есть сохранённая сессия скрининга — откройте **Скрининг** для результатов.")
else:
    st.info("Начните с **Скрининга**: in silico 500 → top-5 и сохранение сессии для отчётов.")

if not rdkit_available():
    st.warning("RDKit недоступен в этом окружении — скрининг работает в demo-режиме (псевдо-дескрипторы).")

col1, col2, col3 = st.columns(3)
form = form_defaults()
col1.metric("Месторождение", form.get("field_name", "—")[:24])
col2.metric("Обводнённость", f"{form.get('water_cut_pct', 0):.0f} %")
col3.metric("T пласта", f"{form.get('temperature_c', 0):.0f} °C")

st.divider()

st.subheader("Маршрут демо")
st.markdown(
    """
1. **Скрининг** — карточка пласта, конвейер 500→top-5, FTO, риски
2. **Лаборатория / OPEX / ОПР / Хемоинформатика** — deliverables по ТЗ
3. **Отчёты** — генерация 6 .docx + ZIP
4. **Для заказчика** — позиционирование эксперта
"""
)

st.subheader("5 отличий от «купить реагент у сервиса»")
for point in PITCH_POINTS:
    st.markdown(f"- {point}")

st.subheader("Покрытие ТЗ")
rows = [{"Требование ТЗ": r["tz"], "Deliverable": r["deliverable"], "Демо": r["demo"]} for r in TZ_MAPPING]
st.dataframe(rows, use_container_width=True, hide_index=True)
