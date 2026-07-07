# SelecGel — демо-стенд технологии ОВП

Демо-стенд хемоинформатического конвейера для селективного ОВП.

## Streamlit Cloud (рекомендуется)

Репозиторий: [github.com/Virgiz1984/SelecGel](https://github.com/Virgiz1984/SelecGel)

1. [share.streamlit.io](https://share.streamlit.io) → **New app**
2. Repository: `Virgiz1984/SelecGel`, branch `main`
3. Main file: `streamlit_app.py`
4. **Advanced settings → Python version: 3.11 или 3.12** (важно для RDKit)
5. Deploy

Локально:

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## FastAPI (локальный стенд)

```bash
cd app
pip install -r requirements.txt
pip install rdkit
python -m cli serve --port 8080
```

| Страница | Назначение |
|----------|------------|
| `/` | Обзор |
| `/screening` | Live demo 500→top-5 |
| `/pitch` | Таблица ТЗ → deliverables |
| `/reports` | 6 .docx + ZIP |

Сценарий презентации: [`DEMO.md`](DEMO.md)

## Структура

- `streamlit_app.py` + `pages/` — Streamlit UI для Cloud
- `app/` — ядро SelecGel (pipeline, отчёты, FastAPI)
- `scouting/` — аналитика для отчёта #1
- `linkedin/` — статья и инфографика
