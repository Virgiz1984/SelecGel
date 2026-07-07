from __future__ import annotations

from pathlib import Path

from .decision_tree import recommend_technologies
from .models import ProjectContext, load_json

SCOUTING_DIR = Path(__file__).resolve().parent.parent.parent.parent / "scouting"
SCOUTING_FILES = [
    ("01-obzor-selktivnyh-tehnologiy-ovp.md", "Обзор селективных технологий"),
    ("02-sravnitelnaya-matrica.md", "Сравнительная матрица"),
    ("04-hemoinformatika-sintez-receptur.md", "Хемоинформатика"),
    ("05-rekomendacii-dlya-proekta.md", "Рекомендации для проекта"),
]


def load_scouting_excerpts(max_chars: int = 1200) -> list[dict]:
    excerpts = []
    for filename, title in SCOUTING_FILES:
        path = SCOUTING_DIR / filename
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.startswith("#")]
        body = " ".join(lines)[:max_chars]
        if len(body) >= max_chars:
            body = body[: max_chars - 3] + "..."
        excerpts.append({"title": title, "source": filename, "text": body})
    return excerpts


def build_scouting_summary(ctx: ProjectContext) -> dict:
    """Структурированные данные для аналитического отчёта."""
    tech_data = load_json("technologies.json")
    recs = recommend_technologies(ctx.reservoir, top_n=5)
    selective = [t for t in tech_data["technologies"] if t["class"] == "selective"]

    return {
        "title": "Аналитический отчёт: обзор селективных технологий ограничения водопритока",
        "technologies_count": len(tech_data["technologies"]),
        "selective_count": len(selective),
        "recommendations": recs,
        "reservoir": ctx.reservoir.to_dict(),
        "key_conclusion": (
            "Рекомендуется двухтрековая стратегия: Track 1 — селективный RPM с хемоинформатикой; "
            "Track 2 — термотропный гель как backup. Track 3 (RPPG) — при fracture-dominated механизме."
        ),
        "cheminformatics_summary": (
            "Хемоинформатика позволяет сократить перебор рецептур с 100+ до 10–15 кандидатов "
            "через descriptor-based ranking и DoE-оптимизацию."
        ),
        "sections": [
            "1. Введение и постановка задачи",
            "2. Классификация технологий ОВП",
            "3. Relative Permeability Modifiers (RPM)",
            "4. Полимерные гели (in-situ, термотропные, HTHS)",
            "5. PPG / RPPG",
            "6. Сравнительная матрица и SWOT",
            "7. Коммерческие решения и российский рынок",
            "8. Хемоинформатика для синтеза рецептур",
            "9. Рекомендации для проекта",
            "10. Источники",
        ],
    }


def technology_table_rows() -> list[list[str]]:
    tech_data = load_json("technologies.json")
    rows = []
    for t in tech_data["technologies"]:
        rows.append([
            t["name_ru"],
            t["selectivity_type"],
            t["mechanism"],
            f"{t['temp_min_c']}–{t['temp_max_c']}",
            t["salinity"],
            str(t["trl"]),
            t["class"],
        ])
    return rows


def mechanism_technology_matrix() -> list[list[str]]:
    return [
        ["Coning / matrix", "RPM, weak gel", "In-depth CDG", "Bulk gel без изоляции"],
        ["Fracture / channel", "RPPG, PPG", "Bulk gel", "RPM alone"],
        ["Cross-flow", "In-depth gel/PPG", "RPM + profile", "Surface-active only"],
        ["Bottom water gas", "HTHS selective gel", "Foam", "Standard RPM"],
        ["Carbonate oil-wet", "AMPS RPM / PPG film", "Wettability modifier", "Cationic RPM alone"],
    ]
