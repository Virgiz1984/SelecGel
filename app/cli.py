"""CLI для Vodopritok Platform."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from vodopritok import __version__
from vodopritok.cheminformatics import generate_doe_matrix, generate_recipe_grid
from vodopritok.decision_tree import decision_tree_text, recommend_technologies
from vodopritok.economics import OpexScenario, analyze_opex, build_opex_plan
from vodopritok.lab_program import build_lab_program, build_lab_report
from vodopritok.models import OUTPUT_DIR, ProjectContext, ReservoirCard
from vodopritok.opr_program import build_opr_program, build_opr_report, score_well_candidate
from vodopritok.reports import (
    generate_all_deliverables,
    generate_lab_program_doc,
    generate_lab_report_doc,
    generate_opr_program_doc,
    generate_opr_report_doc,
    generate_opex_plan_doc,
    generate_scouting_report,
)

app = typer.Typer(
    name="vodopritok",
    help="Платформа для проекта селективного ограничения водопритока (ОВП)",
)
console = Console(force_terminal=True, legacy_windows=False)
OK = "[green]OK[/green]"


def _load_reservoir(config: Optional[Path]) -> ReservoirCard:
    if config and config.exists():
        with config.open(encoding="utf-8") as f:
            data = json.load(f)
        return ReservoirCard(**data)
    return ReservoirCard()


def _load_context(config: Optional[Path], expert: str, company: str) -> ProjectContext:
    reservoir = _load_reservoir(config)
    return ProjectContext(
        expert_name=expert,
        company_name=company,
        reservoir=reservoir,
    )


@app.command()
def version() -> None:
    """Версия ПО."""
    console.print(f"Vodopritok Platform v{__version__}")


@app.command()
def init(
    output: Path = typer.Option(
        Path("examples/reservoir_example.json"),
        help="Путь для сохранения примера карточки пласта",
    ),
) -> None:
    """Создать пример конфигурации пласта."""
    example = ReservoirCard(
        field_name="Месторождение Западная Сибирь",
        well_name="Well-101",
        temperature_c=85.0,
        salinity_g_l=130.0,
        ca2_mg_l=600.0,
        lithology="sandstone",
        wettability="water_wet",
        permeability_md=450.0,
        porosity_pct=19.5,
        water_mechanism="coning",
        water_cut_pct=82.0,
        oil_rate_tpd=14.5,
        water_rate_m3pd=52.0,
        api_gravity=21.0,
        has_fracture=False,
        previous_ovp="",
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as f:
        json.dump(example.to_dict(), f, ensure_ascii=False, indent=2)
    console.print(f"{OK} Пример сохранён: {output}")


@app.command("recommend")
def recommend_cmd(
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="JSON карточка пласта"),
) -> None:
    """Рекомендация технологий ОВП по карточке пласта."""
    reservoir = _load_reservoir(config)
    recs = recommend_technologies(reservoir)

    table = Table(title="Рекомендации технологий ОВП")
    table.add_column("Rank", style="cyan")
    table.add_column("Технология")
    table.add_column("Track")
    table.add_column("Score", justify="right")
    table.add_column("Предупреждения")

    for rec in recs:
        warnings = "; ".join(rec.warnings[:2]) or "—"
        table.add_row(str(rec.rank), rec.name_ru, rec.track, f"{rec.score:.0f}", warnings)

    console.print(table)
    console.print()
    console.print(decision_tree_text(reservoir))


@app.command("screen")
def screen_cmd(
    config: Optional[Path] = typer.Option(None, "--config", "-c"),
    top: int = typer.Option(15, help="Число кандидатов"),
) -> None:
    """In silico screening рецептур (хемоинформатика)."""
    reservoir = _load_reservoir(config)
    candidates = generate_recipe_grid(reservoir, n_candidates=top)

    table = Table(title=f"Top-{top} рецептур RPM (in silico)")
    table.add_column("Rank")
    table.add_column("ID")
    table.add_column("Frrw", justify="right")
    table.add_column("Frro", justify="right")
    table.add_column("Score", justify="right")
    table.add_column("Track")

    for c in candidates:
        table.add_row(
            str(c.rank), c.recipe_id, f"{c.predicted_frrw:.1f}",
            f"{c.predicted_frro:.1f}", f"{c.predicted_score:.1f}", c.track,
        )
    console.print(table)


@app.command("doe")
def doe_cmd() -> None:
    """Генерация DoE-матрицы для лаборатории."""
    runs = generate_doe_matrix()
    table = Table(title=f"DoE matrix ({len(runs)} runs)")
    if runs:
        for key in runs[0]:
            table.add_column(key)
        for run in runs[:10]:
            table.add_row(*[str(run[k]) for k in runs[0]])
    console.print(table)
    if len(runs) > 10:
        console.print(f"... и ещё {len(runs) - 10} прогонов")


@app.command("score-well")
def score_well_cmd(
    config: Optional[Path] = typer.Option(None, "--config", "-c"),
) -> None:
    """Скоринг скважины-кандидата для ОПР."""
    reservoir = _load_reservoir(config)
    score, notes = score_well_candidate(reservoir)
    console.print(f"[bold]Candidate score:[/bold] {score:.0f}/100")
    for n in notes:
        console.print(f"  • {n}")


@app.command("economics")
def economics_cmd(
    config: Optional[Path] = typer.Option(None, "--config", "-c"),
    wc_after: float = typer.Option(64.0, help="Обводнённость после, %"),
) -> None:
    """Расчёт экономики OPEX."""
    reservoir = _load_reservoir(config)
    scenario = OpexScenario(
        name=reservoir.field_name,
        water_cut_before_pct=reservoir.water_cut_pct,
        water_cut_after_pct=wc_after,
        oil_rate_tpd=reservoir.oil_rate_tpd,
    )
    a = analyze_opex(scenario)
    console.print(f"Сокращение воды: {a.water_reduction_m3_year:,.0f} м³/год")
    console.print(f"Годовая экономия: {a.annual_savings_rub:,.0f} ₽")
    console.print(f"Payback: {a.payback_months:.1f} мес.")
    console.print(f"NPV (3 года): {a.npv_3yr_rub:,.0f} ₽")


@app.command("report")
def report_cmd(
    deliverable: str = typer.Argument(..., help="1-6 или 'all'"),
    config: Optional[Path] = typer.Option(None, "--config", "-c"),
    expert: str = typer.Option("Эксперт по ОВП", "--expert"),
    company: str = typer.Option("Заказчик", "--company"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
) -> None:
    """Генерация deliverable .docx (1–6 или all)."""
    ctx = _load_context(config, expert, company)

    if deliverable.lower() == "all":
        from vodopritok.demo.context_builder import build_deliverable_context
        ctx = build_deliverable_context() if not config else _load_context(config, expert, company)
        if config:
            from vodopritok.demo.session import load_session, save_session
            session = load_session()
            save_session(ctx.reservoir.to_dict(), expert, company, session.get("pipeline") if session else None)
            ctx = build_deliverable_context()
        paths = generate_all_deliverables(ctx)
        for p in paths:
            console.print(f"{OK} {p}")
        return

    mapping = {
        "1": ("Аналитический отчёт", lambda: generate_scouting_report(ctx, output)),
        "2": ("Программа лаборатории", lambda: generate_lab_program_doc(ctx, build_lab_program(ctx), output)),
        "3": ("Отчёт лаборатории", lambda: generate_lab_report_doc(ctx, build_lab_report(ctx), output)),
        "4": ("Программа ОПР", lambda: generate_opr_program_doc(ctx, build_opr_program(ctx), output)),
        "5": ("Отчёт ОПР", lambda: generate_opr_report_doc(ctx, build_opr_report(ctx), output)),
        "6": ("План OPEX", lambda: generate_opex_plan_doc(ctx, build_opex_plan(ctx), output)),
    }

    if deliverable not in mapping:
        console.print("[red]Укажите deliverable: 1, 2, 3, 4, 5, 6 или all[/red]")
        raise typer.Exit(1)

    name, fn = mapping[deliverable]
    path = fn()
    console.print(f"{OK} {name}: {path}")


@app.command("dashboard")
def dashboard_cmd(
    config: Optional[Path] = typer.Option(None, "--config", "-c"),
) -> None:
    """Сводный dashboard проекта."""
    ctx = _load_context(config, "Эксперт", "Заказчик")
    r = ctx.reservoir

    console.print("[bold]=== Vodopritok Project Dashboard ===[/bold]")
    console.print(f"Месторождение: {r.field_name} | T={r.temperature_c}°C | WC={r.water_cut_pct}%")
    console.print()

    recs = recommend_technologies(r, top_n=3)
    console.print("[bold]Top technologies:[/bold]")
    for rec in recs:
        console.print(f"  {rec.rank}. {rec.name_ru} (score={rec.score:.0f})")

    score, _ = score_well_candidate(r)
    console.print(f"\n[bold]Well candidate score:[/bold] {score:.0f}/100")

    candidates = generate_recipe_grid(r, n_candidates=3)
    console.print("\n[bold]Top recipes (in silico):[/bold]")
    for c in candidates:
        console.print(f"  {c.recipe_id}: Frrw={c.predicted_frrw:.1f}, Frro={c.predicted_frro:.1f}")

    plan = build_opex_plan(ctx)
    a = plan["analysis"]
    console.print(f"\n[bold]OPEX potential:[/bold] {a.annual_savings_rub:,.0f} ₽/год, payback {a.payback_months:.1f} мес.")


@app.command("pipeline")
def pipeline_cmd(
    config: Optional[Path] = typer.Option(None, "--config", "-c"),
    n_molecules: int = typer.Option(500, help="Размер патентной библиотеки"),
    top: int = typer.Option(5, help="Top-N после QSAR"),
    no_molfeat: bool = typer.Option(False, help="Только RDKit, без molfeat"),
    export_qsprpred: bool = typer.Option(True, help="Экспорт QSPRpred JSON"),
) -> None:
    """Полный конвейер: RDKit+molfeat → QSPR → DeepChem → QSPRpred."""
    from vodopritok.models import OUTPUT_DIR
    from vodopritok.pipeline import export_qsprpred_json, run_cheminformatics_pipeline
    from vodopritok.pipeline.orchestrator import pipeline_to_lab_validation

    reservoir = _load_reservoir(config)
    console.print("[bold]Cheminformatics pipeline[/bold]")
    console.print("1. RDKit + molfeat → descriptors")
    console.print("2. scikit-learn QSPR → viscosity + thermal (keep 30%)")
    console.print("3. DeepChem QSAR → selectivity (top-5)")
    console.print("4. QSPRpred → lab validation report")
    console.print()

    try:
        result = run_cheminformatics_pipeline(
            reservoir=reservoir,
            n_molecules=n_molecules,
            top_n=top,
            use_molfeat=not no_molfeat,
        )
    except ImportError as e:
        console.print(f"[red]Ошибка:[/red] {e}")
        raise typer.Exit(1) from e

    for stage in result.stages:
        console.print(
            f"  [{stage.tool}] {stage.name}: "
            f"{stage.input_count} → {stage.output_count} "
            f"(отсеяно {stage.filter_pct}%)"
        )

    table = Table(title=f"Top-{top} molecules (QSAR selectivity)")
    table.add_column("Rank")
    table.add_column("mol_id")
    table.add_column("Frrw", justify="right")
    table.add_column("Frro", justify="right")
    table.add_column("Selectivity", justify="right")
    for mol in result.top5:
        table.add_row(
            str(mol.rank), mol.mol_id,
            f"{mol.predicted_frrw:.2f}", f"{mol.predicted_frro:.2f}",
            f"{mol.selectivity_index:.2f}",
        )
    console.print(table)

    validation = pipeline_to_lab_validation(result)
    report = validation["report"]
    console.print(f"\n[bold]QSPRpred:[/bold] {report.summary}")

    if export_qsprpred:
        out = OUTPUT_DIR / "qsprpred_validation.json"
        export_qsprpred_json(report, out)
        console.print(f"{OK} QSPRpred report: {out}")


@app.command("golden-demo")
def golden_demo_cmd(
    config: Optional[Path] = typer.Option(None, "--config", "-c"),
    expert: str = typer.Option("Эксперт по ОВП", "--expert"),
    company: str = typer.Option("Демо-заказчик (Западная Сибирь)", "--company"),
) -> None:
    """Golden demo: screening → session → 6 docx → ZIP."""
    from vodopritok.demo.golden import run_golden_demo

    result = run_golden_demo(reservoir_path=config, expert=expert, company=company)
    console.print(f"{OK} Golden demo ZIP: {result['zip']}")
    for p in result["docx"]:
        console.print(f"  {p.name}")


@app.command("serve")
def serve_cmd(
    host: str = typer.Option("127.0.0.1", help="Хост"),
    port: int = typer.Option(8080, help="Порт"),
    reload: bool = typer.Option(True, help="Auto-reload при изменении кода"),
) -> None:
    """Запустить веб-интерфейс."""
    import uvicorn

    console.print(f"SelecGel: http://{host}:{port}")
    uvicorn.run("vodopritok.web.app:app", host=host, port=port, reload=reload)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
