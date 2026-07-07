"""Altair-графики для Streamlit (аналог Chart.js в FastAPI UI)."""

from __future__ import annotations

from typing import Any

import altair as alt
import pandas as pd
import streamlit as st

# Единый стиль под тёмную тему Streamlit
_CHART_THEME = {
    "background": "transparent",
    "axis": {"labelColor": "#94a3b8", "titleColor": "#e2e8f0", "gridColor": "#334155"},
    "legend": {"labelColor": "#94a3b8", "titleColor": "#e2e8f0"},
    "title": {"color": "#f1f5f9", "fontSize": 14},
}


def _apply_theme(chart: alt.Chart) -> alt.Chart:
    return chart.configure(**_CHART_THEME)


def chart_tech_scores(recommendations: list[Any]) -> alt.Chart:
    df = pd.DataFrame(
        [{"Технология": r.name_ru[:36], "Score": float(r.score)} for r in recommendations]
    )
    chart = (
        alt.Chart(df)
        .mark_bar(color="#8b5cf6", cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
        .encode(
            x=alt.X("Score:Q", title="Score"),
            y=alt.Y("Технология:N", sort="-x", title=""),
        )
        .properties(height=max(180, len(df) * 36), title="Рекомендация технологии")
    )
    return _apply_theme(chart)


def chart_funnel(stages: list[dict], top_n: int = 5, total_input: int = 500) -> alt.Chart:
    qspr_out = stages[1]["output_count"] if len(stages) > 1 else top_n * 10
    first = stages[0]["output_count"] if stages else total_input
    df = pd.DataFrame(
        {
            "Этап": ["Патентная библиотека", "После QSPR (−70%)", f"Top-{top_n} (QSAR)"],
            "Молекул": [first, qspr_out, top_n],
        }
    )
    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusEnd=6)
        .encode(
            x=alt.X("Молекул:Q", title="Кандидатов"),
            y=alt.Y("Этап:N", sort="-x", title=""),
            color=alt.Color("Этап:N", legend=None, scale=alt.Scale(range=["#3b82f6", "#8b5cf6", "#22c55e"])),
        )
        .properties(height=160, title="Воронка screening")
    )
    return _apply_theme(chart)


def chart_top5_bars(top5: list[dict]) -> alt.Chart:
    rows = []
    for mol in top5:
        mid = mol.get("mol_id", "?")
        rows.append({"mol_id": mid, "Метрика": "Frrw (вода)", "Значение": float(mol.get("predicted_frrw", 0))})
        rows.append({"mol_id": mid, "Метрика": "Frro (нефть)", "Значение": float(mol.get("predicted_frro", 0))})
    df = pd.DataFrame(rows)
    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("mol_id:N", title=""),
            y=alt.Y("Значение:Q", title=""),
            color=alt.Color(
                "Метрика:N",
                scale=alt.Scale(domain=["Frrw (вода)", "Frro (нефть)"], range=["#3b82f6", "#f59e0b"]),
            ),
            xOffset=alt.XOffset("Метрика:N"),
        )
        .properties(height=280, title="Top-5: Frrw vs Frro (gate Frrw ≥ 5)")
    )
    return _apply_theme(chart)


def chart_selectivity(top5: list[dict]) -> alt.Chart:
    df = pd.DataFrame(
        [
            {
                "Rank": int(mol.get("rank", i + 1)),
                "mol_id": mol.get("mol_id", f"M{i}"),
                "Селективность": float(mol.get("selectivity_index", 0)),
            }
            for i, mol in enumerate(top5)
        ]
    )
    chart = (
        alt.Chart(df)
        .mark_line(color="#22c55e", point=alt.OverlayMarkDef(color="#22c55e", size=70))
        .encode(
            x=alt.X("Rank:O", title="Rank"),
            y=alt.Y("Селективность:Q", title="Selectivity index"),
            tooltip=["mol_id", "Селективность"],
        )
        .properties(height=220, title="Индекс селективности")
    )
    return _apply_theme(chart)


def chart_stages(stages: list[dict]) -> alt.Chart | None:
    if not stages:
        return None
    df = pd.DataFrame(
        {
            "Этап": [s.get("name", "Stage")[:24] for s in stages],
            "Выход": [int(s.get("output_count", 0)) for s in stages],
        }
    )
    chart = (
        alt.Chart(df)
        .mark_bar(color="#6366f1", cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("Этап:N", title="", sort=None),
            y=alt.Y("Выход:Q", title="Молекул после этапа"),
        )
        .properties(height=240, title="ML pipeline — выход по этапам")
    )
    return _apply_theme(chart)


def chart_qsprpred_mape(comparison: dict | None) -> alt.Chart | None:
    if not comparison or not comparison.get("before") or not comparison.get("after"):
        return None
    df = pd.DataFrame(
        {
            "Этап": ["До lab CSV", "После lab CSV"],
            "MAPE %": [
                float(comparison["before"].get("mape", 0)),
                float(comparison["after"].get("mape", 0)),
            ],
        }
    )
    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("Этап:N", title=""),
            y=alt.Y("MAPE %:Q", title="MAPE, %"),
            color=alt.Color("Этап:N", legend=None, scale=alt.Scale(range=["#64748b", "#22c55e"])),
        )
        .properties(height=220, title="QSPRpred: калибровка lab CSV")
    )
    return _apply_theme(chart)


def chart_qsprpred_scatter(validation: dict | None) -> alt.Chart | None:
    if not validation:
        return None
    report = validation.get("report")
    if not report or not getattr(report, "rows", None):
        return None
    rows = [r for r in report.rows if r.property_name == "frrw"]
    if not rows:
        return None
    df = pd.DataFrame(
        {
            "Predicted": [r.predicted for r in rows],
            "Observed": [r.observed for r in rows],
            "mol_id": [r.mol_id for r in rows],
        }
    )
    ideal = pd.DataFrame({"Predicted": [0, 10], "Observed": [0, 10]})
    scatter = alt.Chart(df).mark_circle(size=100, color="#3b82f6").encode(
        x=alt.X("Predicted:Q", scale=alt.Scale(domain=[0, 10])),
        y=alt.Y("Observed:Q", scale=alt.Scale(domain=[0, 10])),
        tooltip=["mol_id", "Predicted", "Observed"],
    )
    line = alt.Chart(ideal).mark_line(color="#22c55e", strokeDash=[6, 4]).encode(
        x="Predicted:Q",
        y="Observed:Q",
    )
    chart = (scatter + line).properties(height=260, title="QSPRpred: прогноз vs лаборатория (Frrw)")
    return _apply_theme(chart)


def chart_risk_cards(risk: dict | None) -> alt.Chart | None:
    if not risk or not risk.get("cards"):
        return None
    rows = []
    for c in risk["cards"]:
        score = float(c["score"])
        if score >= 75:
            color = "#22c55e"
        elif score >= 50:
            color = "#f59e0b"
        else:
            color = "#ef4444"
        rows.append({"Критерий": c["title"], "Score": score, "color": color})
    df = pd.DataFrame(rows)
    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("Критерий:N", title="", sort="-y"),
            y=alt.Y("Score:Q", title="Score / 100"),
            color=alt.Color("color:N", scale=None, legend=None),
        )
        .properties(height=280, title=f"Risk dashboard · {risk.get('overall_score', 0):.0f}/100")
    )
    return _apply_theme(chart)


def chart_measures(measures: list[dict], top_n: int = 10) -> alt.Chart:
    rows = sorted(measures, key=lambda m: m.get("estimated_annual_rub", 0), reverse=True)[:top_n]
    df = pd.DataFrame(
        [
            {
                "Мероприятие": m.get("measure", "")[:40],
                "₽/год": float(m.get("estimated_annual_rub", 0)) / 1_000_000,
            }
            for m in rows
        ]
    )
    chart = (
        alt.Chart(df)
        .mark_bar(color="#3b82f6", cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
        .encode(
            x=alt.X("₽/год:Q", title="Млн ₽/год"),
            y=alt.Y("Мероприятие:N", sort="-x", title=""),
        )
        .properties(height=max(260, len(df) * 28), title="Топ мероприятий по экономии")
    )
    return _apply_theme(chart)


def chart_feasibility(assessments: list[dict]) -> alt.Chart:
    df = pd.DataFrame(
        [
            {
                "ID": a.get("recipe_id", a.get("mol_id", "?")),
                "Feasibility": float(a.get("feasibility_score", 0)),
            }
            for a in assessments
        ]
    )
    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("ID:N", title=""),
            y=alt.Y("Feasibility:Q", title="Score / 100"),
            color=alt.condition(alt.datum.Feasibility >= 78, alt.value("#22c55e"), alt.value("#8b5cf6")),
        )
        .properties(height=260, title="Feasibility top-5 для синтеза")
    )
    return _apply_theme(chart)


def chart_tech_economics(comparison: list[dict]) -> alt.Chart | None:
    if not comparison:
        return None
    rows = []
    for t in comparison:
        rows.append({"Технология": t["technology"][:20], "Тип": "CAPEX", "Млн ₽": t["capex_rub"] / 1_000_000})
        rows.append(
            {"Технология": t["technology"][:20], "Тип": "OPEX/год", "Млн ₽": t["annual_reagent_rub"] / 1_000_000}
        )
    df = pd.DataFrame(rows)
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("Технология:N", title=""),
            y=alt.Y("Млн ₽:Q", title="Млн ₽"),
            color=alt.Color("Тип:N", scale=alt.Scale(range=["#f59e0b", "#3b82f6"])),
            xOffset=alt.XOffset("Тип:N"),
        )
        .properties(height=280, title="Сравнение технологий (CAPEX vs OPEX/год)")
    )
    return _apply_theme(chart)


_RADAR_PALETTE = ["#3b82f6", "#8b5cf6", "#f59e0b", "#ec4899", "#06b6d4"]


def _hex_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def chart_twin_economics(twin: Any) -> alt.Chart:
    eco = twin.economics if hasattr(twin, "economics") else twin["economics"]
    df = pd.DataFrame(
        {
            "Показатель": ["Экономия/год", "NPV 3 года", "Payback"],
            "Значение": [
                float(eco.get("annual_savings_rub", 0)) / 1_000_000,
                float(eco.get("npv_3yr_rub", 0)) / 1_000_000,
                float(eco.get("payback_months", 0)),
            ],
            "Подпись": [
                f"{eco.get('annual_savings_rub', 0)/1e6:.1f} млн ₽",
                f"{eco.get('npv_3yr_rub', 0)/1e6:.1f} млн ₽",
                f"{eco.get('payback_months', 0):.0f} мес",
            ],
        }
    )
    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("Показатель:N", title=""),
            y=alt.Y("Значение:Q", title=""),
            color=alt.Color("Показатель:N", legend=None, scale=alt.Scale(range=["#22c55e", "#3b82f6", "#f59e0b"])),
            tooltip=["Показатель", "Подпись"],
        )
        .properties(height=280, title="Экономика lead candidate")
    )
    return _apply_theme(chart)


def twin_radar_figure(
    bundle: dict[str, Any],
    selected_ranks: list[int],
    show_lab: bool = True,
):
    import plotly.graph_objects as go

    labels = bundle["labels"]
    gate = bundle["gate"]
    theta = labels + [labels[0]]
    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=gate + [gate[0]],
            theta=theta,
            name="Gate (цель)",
            line=dict(color="#22c55e", dash="dash", width=2),
            fill="toself",
            fillcolor="rgba(34,197,94,0.08)",
            opacity=0.9,
        )
    )

    for cand in bundle.get("candidates", []):
        rank = int(cand.get("rank", 0))
        if rank not in selected_ranks:
            continue
        values = cand.get("values", [])
        if not values:
            continue
        color = _RADAR_PALETTE[(rank - 1) % len(_RADAR_PALETTE)]
        fig.add_trace(
            go.Scatterpolar(
                r=values + [values[0]],
                theta=theta,
                name=f"#{rank} {cand.get('mol_id', '')}",
                line=dict(color=color, width=2),
                fill="toself",
                fillcolor=_hex_rgba(color, 0.15),
                opacity=0.75,
            )
        )

    if show_lab and bundle.get("lab"):
        lab_by_rank = {int(l["rank"]): l for l in bundle["lab"]}
        for rank in selected_ranks:
            lab = lab_by_rank.get(rank)
            if not lab:
                continue
            values = lab.get("values", [])
            if not values:
                continue
            fig.add_trace(
                go.Scatterpolar(
                    r=values + [values[0]],
                    theta=theta,
                    name=f"Lab #{rank}",
                    line=dict(color="#94a3b8", dash="dot", width=2),
                    fill="none",
                    opacity=0.9,
                )
            )

    fig.update_layout(
        polar=dict(radialaxis=dict(range=[0, 10], showgrid=True, gridcolor="#334155")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.15),
        height=480,
        title=dict(text="Профиль реагента (норм. 0–10)", x=0.5),
        margin=dict(t=60, b=80),
    )
    return fig


def show_plotly(fig) -> None:
    if fig is not None:
        st.plotly_chart(fig, width="stretch")


def radar_gate_summary_table(bundle: dict, selected_ranks: list[int]) -> pd.DataFrame:
    rows = []
    for cand in bundle.get("candidates", []):
        if int(cand.get("rank", 0)) not in selected_ranks:
            continue
        for item in cand.get("summary", []):
            rows.append(
                {
                    "Кандидат": cand.get("mol_id"),
                    "Ось": item.get("axis"),
                    "Score": item.get("score"),
                    "Gate": item.get("gate"),
                    "Pass": "✓" if item.get("pass") else "✗",
                }
            )
    return pd.DataFrame(rows)


def show_chart(chart: alt.Chart | None) -> None:
    if chart is not None:
        st.altair_chart(chart, width="stretch")


def render_home_charts(session: dict | None, recommendations: list[Any]) -> None:
    st.subheader("Обзор конвейера")
    c1, c2 = st.columns(2)
    with c1:
        show_chart(chart_tech_scores(recommendations))
    if session and session.get("pipeline"):
        pipe = session["pipeline"]
        stages = pipe.get("stages", [])
        top5 = pipe.get("top5", [])
        with c2:
            show_chart(chart_funnel(stages, top_n=len(top5), total_input=pipe.get("total_input", 500)))
        c3, c4 = st.columns(2)
        with c3:
            if top5:
                show_chart(chart_top5_bars(top5))
        with c4:
            show_chart(chart_stages(stages))


def render_screening_charts(payload: dict | None, recommendations: list[Any]) -> None:
    st.subheader("Рекомендация технологий")
    show_chart(chart_tech_scores(recommendations))

    if not payload:
        return

    stages = payload.get("stages", [])
    top5 = payload.get("top5", [])
    total = len(top5)

    st.subheader("Воронка и pipeline")
    c1, c2 = st.columns(2)
    with c1:
        show_chart(chart_funnel(stages, top_n=total, total_input=stages[0]["input_count"] if stages else 500))
    with c2:
        show_chart(chart_stages(stages))

    st.subheader("Top-5 — селективность")
    c3, c4 = st.columns(2)
    with c3:
        show_chart(chart_top5_bars(top5))
    with c4:
        show_chart(chart_selectivity(top5))

    comparison = payload.get("comparison")
    validation = payload.get("validation")
    if comparison or validation:
        st.subheader("QSPRpred validation")
        c5, c6 = st.columns(2)
        with c5:
            show_chart(chart_qsprpred_scatter(validation))
        with c6:
            show_chart(chart_qsprpred_mape(comparison))
            if comparison and comparison.get("before") and comparison.get("after"):
                st.caption(
                    f"MAPE: {comparison['before'].get('mape', 0):.1f}% → "
                    f"{comparison['after'].get('mape', 0):.1f}% после lab CSV"
                )

    risk = payload.get("risk_dashboard")
    if risk:
        st.subheader("Risk dashboard")
        show_chart(chart_risk_cards(risk))
