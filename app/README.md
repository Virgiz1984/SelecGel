# Vodopritok Platform

Программный комплекс для проекта **«Разработка селективной технологии ограничения водопритока»** — покрывает все 6 deliverables ТЗ и инструменты экспертной работы.

## Возможности

| Модуль | Назначение |
|--------|------------|
| **Scouting** | База 9 технологий ОВП, сравнительная матрица, аналитический отчёт (.docx) |
| **Decision Tree** | Выбор технологии по механизму обводнения, T, salinity, проницаемости |
| **Cheminformatics** | In silico screening рецептур RPM, descriptors, DoE-матрица, ML-калибровка |
| **Lab Program** | Программа лабораторных исследований, gate KPI, отчёт по core flood |
| **OPR Program** | Скоринг скважин-кандидатов, программа и отчёт ОПР |
| **Economics** | NPV, payback, план снижения OPEX (7 мероприятий) |
| **Reports** | Генерация всех 6 документов в формате .docx |

## Установка

```bash
cd app
pip install -r requirements.txt
pip install -e .
```

## Быстрый старт

```bash
# Пример карточки пласта
vodopritok init

# Рекомендация технологий
vodopritok recommend -c examples/reservoir_example.json

# Хемоинформатика: Top-15 рецептур
vodopritok screen -c examples/reservoir_example.json

# Сводный dashboard
vodopritok dashboard -c examples/reservoir_example.json

# Все 6 deliverables (.docx)
vodopritok report all -c examples/reservoir_example.json --expert "Иванов И.И." --company "Нефтегаз"
```

## Deliverables (соответствие ТЗ)

| № | Документ | Команда |
|---|----------|---------|
| 1 | Аналитический отчёт | `vodopritok report 1` |
| 2 | Программа лабораторных исследований | `vodopritok report 2` |
| 3 | Отчёт по лаборатории | `vodopritok report 3` |
| 4 | Программа ОПР | `vodopritok report 4` |
| 5 | Отчёт по ОПР | `vodopritok report 5` |
| 6 | План снижения OPEX | `vodopritok report 6` |

Документы сохраняются в `app/output/`.

## Карточка пласта (JSON)

```json
{
  "field_name": "Месторождение",
  "well_name": "Well-101",
  "temperature_c": 85,
  "salinity_g_l": 130,
  "lithology": "sandstone",
  "water_mechanism": "coning",
  "water_cut_pct": 82,
  "oil_rate_tpd": 14.5,
  "permeability_md": 450
}
```

Механизмы обводнения: `coning`, `matrix_flow`, `channeling`, `fracture`, `wormhole`, `cross_flow`, `high_perm_streak`, `bottom_water`, `behind_casing`.

## Cheminformatics pipeline

```
500 patent molecules
    → RDKit + molfeat (descriptors)
    → scikit-learn QSPR (viscosity, thermal stability) — keep 30%
    → DeepChem QSAR (selectivity Frrw/Frro) — top-5
    → QSPRpred (lab observed vs predicted)
```

```bash
# Минимум: RDKit + scikit-learn
pip install rdkit scikit-learn numpy

# Полный стек
pip install -r requirements-cheminformatics.txt

vodopritok pipeline -c examples/reservoir_example.json
```

Веб: [http://127.0.0.1:8080/pipeline](http://127.0.0.1:8080/pipeline)

## Архитектура

```
app/
├── cli.py                    # CLI (Typer)
├── vodopritok/
│   ├── data/                 # Базы технологий и мономеров
│   ├── decision_tree.py      # Выбор технологии
│   ├── cheminformatics.py    # Screening + DoE + ML
│   ├── scouting.py           # Аналитика
│   ├── lab_program.py        # Лаборатория
│   ├── opr_program.py        # ОПР
│   ├── economics.py          # OPEX
│   └── reports.py            # Генерация .docx
└── output/                   # Сгенерированные документы
```

## Связь со скаутингом

ПО использует данные из `../scouting/` (обзор технологий, хемоинформатика, рекомендации) — встроено в JSON-базы и логику scoring.

## Лицензия

Внутреннее использование в рамках проекта ОВП.
