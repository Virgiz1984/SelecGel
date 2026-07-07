"""Сохранение последней демо-сессии (screening → отчёты)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from vodopritok.models import OUTPUT_DIR, ProjectContext, ReservoirCard

SESSION_FILE = OUTPUT_DIR / "demo_session.json"
UPLOADED_LAB_CSV = OUTPUT_DIR / "uploaded_lab.csv"


def save_session(
    form: dict[str, Any],
    expert: str = "Эксперт по ОВП",
    company: str = "Заказчик",
    pipeline_summary: dict[str, Any] | None = None,
    lab_csv_path: str | None = None,
    qsprpred_comparison: dict | None = None,
) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    existing = load_session() or {}
    payload = {
        "updated_at": datetime.now().isoformat(),
        "expert": expert,
        "company": company,
        "reservoir": form,
        "pipeline": pipeline_summary,
        "lab_csv_path": lab_csv_path or existing.get("lab_csv_path"),
        "qsprpred_comparison": qsprpred_comparison or existing.get("qsprpred_comparison"),
    }
    with SESSION_FILE.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return SESSION_FILE


def load_session() -> dict[str, Any] | None:
    if not SESSION_FILE.exists():
        return None
    with SESSION_FILE.open(encoding="utf-8") as f:
        return json.load(f)


def get_context_from_session() -> ProjectContext | None:
    data = load_session()
    if not data:
        return None
    return ProjectContext(
        expert_name=data.get("expert", "Эксперт по ОВП"),
        company_name=data.get("company", "Заказчик"),
        reservoir=ReservoirCard(**data["reservoir"]),
    )


TZ_MAPPING = [
    {
        "tz": "1. Аналитический отчёт по технологиям ОВП",
        "deliverable": "01-analyticheskiy-otchet-ovp.docx",
        "demo": "scouting + /cheminformatics (feasibility синтеза top-5) + FTO",
    },
    {
        "tz": "2. Программа лабораторных исследований",
        "deliverable": "02-programma-laboratornyh-issledovaniy.docx",
        "demo": "Track 1 top-5 + Track 2 backup + gate KPI + DoE + /lab-program",
    },
    {
        "tz": "3. Отчёт по результатам лаборатории",
        "deliverable": "03-otchet-laboratoriya.docx",
        "demo": "Core flood Frrw/Frro + QSPRpred validation",
    },
    {
        "tz": "4. Программа опытно-промышленных работ",
        "deliverable": "04-programma-opr.docx",
        "demo": "Скоринг скважины + injection design + KPI + /opr-program",
    },
    {
        "tz": "5. Отчёт по результатам ОПР",
        "deliverable": "05-otchet-opr.docx",
        "demo": "Мониторинг WC, Qn, эффект",
    },
    {
        "tz": "6. План снижения OPEX",
        "deliverable": "06-plan-snizheniya-opex.docx",
        "demo": "Методология 5 шагов + сравнение технологий + 10 мероприятий + /opex-plan",
    },
]

PITCH_POINTS = [
    "Диагностика механизма обводнения — до выбора реагента",
    "In silico screening Track 1: 500 → top-5 + оценка feasibility синтеза (/cheminformatics)",
    "Двухтрековая R&D: трек 1 — RPM (primary) + трек 2 — термотропный gel (backup); трек 3 — при каналах/трещинах",
    "Lab gate: Frrw≥5, Frro≤2 — не выходим в ОПР без доказательства",
    "Экономика внедрения: baseline OPEX → NPV/payback → 10 мероприятий с ₽/год (/opex-plan)",
    "6 документов .docx — полное покрытие ТЗ проекта за 4 месяца",
]
