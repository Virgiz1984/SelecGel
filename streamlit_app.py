"""SelecGel — демо на Streamlit Cloud (UI как FastAPI :8080)."""

from __future__ import annotations

import streamlit as st

from sl_helpers import (
    PITCH_POINTS,
    TZ_MAPPING,
    form_defaults,
    load_session,
    rdkit_available,
    recommend_technologies,
    reservoir_from_form,
)
from sl_webui import home_charts_from_session, home_charts_widget, setup_page

setup_page("home", "Обзор")

session = load_session()
form = form_defaults()
reservoir = reservoir_from_form(form)
recs = recommend_technologies(reservoir, top_n=3)

st.markdown(
    """
    <section class="card">
      <p class="eyebrow">Технология эксперта · селективное ОВП</p>
      <h2>In silico screening реагентов под ваш пласт</h2>
      <p class="hero-text">
        Хемоинформатический конвейер: <strong>500 → 150 → top-5</strong> кандидатов до лаборатории.
        Сначала механизм обводнения — потом класс технологии — потом химия.
      </p>
    </section>
    """,
    unsafe_allow_html=True,
)

hc1, hc2, hc3 = st.columns(3)
with hc1:
    st.page_link("pages/1_Скрининг.py", label="Запустить screening", icon="▶️")
with hc2:
    st.page_link("pages/9_Экология.py", label="Экология", icon="🌿")
with hc3:
    st.page_link("pages/8_Для_заказчика.py", label="Для заказчика", icon="📄")

if session and session.get("pipeline"):
    updated = session.get("updated_at", "")[:16]
    field = session.get("reservoir", {}).get("field_name", "—")
    temp = session.get("reservoir", {}).get("temperature_c", "—")
    st.markdown(
        f"""
        <section class="card success-bar">
          <strong>Последний screening сохранён</strong>
          <span class="muted">{updated} · {field} · T={temp}°C</span>
        </section>
        """,
        unsafe_allow_html=True,
    )
    st.page_link("pages/7_Отчёты.py", label="Сгенерировать отчёты")
else:
    st.markdown(
        '<section class="card"><p class="muted">Демо-кейс: Западная Сибирь, Well-101, T=85°C, WC=82%. Начните со screening.</p></section>',
        unsafe_allow_html=True,
    )

if not rdkit_available():
    st.warning("RDKit недоступен — скрининг в demo-режиме (псевдо-дескрипторы).")

st.markdown(
    """
    <section class="card">
      <h2>Конвейер</h2>
      <div class="pipeline-flow">
        <span class="flow-step">Карточка пласта</span><span class="flow-arrow">→</span>
        <span class="flow-step">RDKit · 500 SMILES</span><span class="flow-arrow">→</span>
        <span class="flow-step">QSPR −70%</span><span class="flow-arrow">→</span>
        <span class="flow-step">QSAR top-5</span><span class="flow-arrow">→</span>
        <span class="flow-step">Lab gate → ОПР</span>
      </div>
    </section>
    """,
    unsafe_allow_html=True,
)

has_pipeline = bool(session and session.get("pipeline"))
charts = home_charts_from_session(session, recs)
home_charts_widget(charts, has_pipeline)

st.markdown('<section class="modules grid-4">', unsafe_allow_html=True)
mcols = st.columns(4)
links = [
    ("pages/1_Скрининг.py", "1", "Screening", "500 → top-5 · live demo"),
    ("pages/5_Профиль.py", "2", "Профиль реагента", "Frrw, η, economics"),
    ("pages/7_Отчёты.py", "3", "6 отчётов .docx", "Покрытие ТЗ проекта"),
    ("pages/8_Для_заказчика.py", "4", "Для заказчика", "ТЗ → deliverables"),
]
for col, (path, num, title, desc) in zip(mcols, links):
    with col:
        st.page_link(path, label=f"{num}. {title}")
        st.caption(desc)

lead = (session or {}).get("pipeline", {}).get("lead_twin")
if lead:
    st.markdown(
        f"""
        <section class="card">
          <h2>Lead candidate</h2>
          <p><strong>{lead.get('mol_id', '—')}</strong></p>
        </section>
        """,
        unsafe_allow_html=True,
    )

st.markdown("### Покрытие ТЗ проекта (6 deliverables)")
rows = [{"Пункт ТЗ": r["tz"], "Файл": r["deliverable"]} for r in TZ_MAPPING]
st.dataframe(rows, width="stretch", hide_index=True)

st.markdown("### 5 отличий от «купить реагент у сервиса»")
for point in PITCH_POINTS:
    st.markdown(f"- {point}")
