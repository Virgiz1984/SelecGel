from __future__ import annotations

import io
import json
import zipfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from vodopritok.api.routes import router as api_router
from vodopritok.decision_tree import recommend_technologies, rd_track_strategy
from vodopritok.demo.session import (
    PITCH_POINTS,
    TZ_MAPPING,
    get_context_from_session,
    load_session,
    save_session,
)
from vodopritok.models import OUTPUT_DIR, ProjectContext, ReservoirCard, load_json
from vodopritok.pipeline import export_qsprpred_json, run_cheminformatics_pipeline
from vodopritok.pipeline.orchestrator import pipeline_to_lab_validation
from vodopritok.reports import generate_all_deliverables, generate_lab_program_doc, generate_opr_program_doc, generate_opex_plan_doc, generate_synthesis_assessment_doc
from vodopritok.opr_program import build_opr_program
from vodopritok.synthesis_assessment import build_synthesis_assessment
from vodopritok.selecgel.config import PRODUCT_NAME, PRODUCT_TAGLINE
from vodopritok.selecgel.digital_twin import build_twins_from_pipeline
from vodopritok.demo.context_builder import build_deliverable_context, build_fto_rows
from vodopritok.demo.lab_data import UPLOADED_LAB_CSV, get_active_lab_csv, lab_overrides_for_pipeline, load_lab_measurements
from vodopritok.pipeline.patent_library import ensure_patent_library
from vodopritok.demo.risk_dashboard import build_risk_dashboard
from vodopritok.lab_program import build_lab_program
from vodopritok.economics import OpexScenario, analyze_opex, build_opex_plan
from vodopritok.export import generate_cover_letter, generate_one_pager, generate_tz_checklist
from vodopritok.web.viz import (
    build_home_charts,
    build_pitch_charts,
    build_qsprpred_comparison,
    build_reports_charts,
    build_screening_charts,
    economics_chart,
    tech_scores_chart,
    build_twin_radar_bundle,
    twin_radar,
)

WEB_DIR = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(WEB_DIR / "templates"))

app = FastAPI(title=PRODUCT_NAME, description=PRODUCT_TAGLINE, version="1.0.0")
app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")
app.include_router(api_router)


def _ctx(active: str, **extra) -> dict[str, Any]:
    from vodopritok.selecgel.config import PRESENTATION_MODE

    session = load_session()
    return {
        "active": active,
        "tagline": PRODUCT_TAGLINE,
        "session": session,
        "has_session": session is not None,
        "presentation_mode": PRESENTATION_MODE,
        **extra,
    }


def _lab_program_payload() -> dict:
    return build_lab_program(build_deliverable_context())


def _opex_plan_payload() -> dict:
    return build_opex_plan(build_deliverable_context())


def _eco_defaults() -> dict[str, float]:
    ctx = build_deliverable_context()
    plan = build_opex_plan(ctx)
    return {
        "wc_before": ctx.reservoir.water_cut_pct,
        "wc_after": plan["scenario"].water_cut_after_pct,
        "oil_rate": ctx.reservoir.oil_rate_tpd,
    }


def _synthesis_assessment_payload() -> dict:
    return build_synthesis_assessment(build_deliverable_context())


def _opr_program_payload() -> dict:
    return build_opr_program(build_deliverable_context())


def _reservoir_from_form(data: dict[str, Any]) -> ReservoirCard:
    return ReservoirCard(
        field_name=data.get("field_name", "Месторождение"),
        well_name=data.get("well_name", ""),
        temperature_c=float(data.get("temperature_c", 80)),
        pressure_mpa=float(data.get("pressure_mpa", 15)),
        salinity_g_l=float(data.get("salinity_g_l", 120)),
        ca2_mg_l=float(data.get("ca2_mg_l", 500)),
        lithology=data.get("lithology", "sandstone"),
        wettability=data.get("wettability", "water_wet"),
        permeability_md=float(data.get("permeability_md", 500)),
        porosity_pct=float(data.get("porosity_pct", 18)),
        water_mechanism=data.get("water_mechanism", "coning"),
        water_cut_pct=float(data.get("water_cut_pct", 85)),
        oil_rate_tpd=float(data.get("oil_rate_tpd", 12)),
        water_rate_m3pd=float(data.get("water_rate_m3pd", 45)),
        api_gravity=float(data.get("api_gravity", 22)),
        has_fracture=data.get("has_fracture") in (True, "true", "on", "1"),
        previous_ovp=data.get("previous_ovp", ""),
    )


def _form_defaults() -> dict[str, Any]:
    session = load_session()
    if session and session.get("reservoir"):
        return session["reservoir"]
    example = Path(__file__).resolve().parent.parent.parent / "examples" / "reservoir_example.json"
    if example.exists():
        with example.open(encoding="utf-8") as f:
            return json.load(f)
    return ReservoirCard().to_dict()


def _form_from_post(
    field_name: str = "Месторождение",
    well_name: str = "",
    expert: str = "Эксперт по ОВП",
    company: str = "Заказчик",
    temperature_c: float = 85,
    salinity_g_l: float = 130,
    permeability_md: float = 450,
    water_cut_pct: float = 82,
    oil_rate_tpd: float = 14.5,
    api_gravity: float = 22,
    lithology: str = "sandstone",
    water_mechanism: str = "coning",
    has_fracture: str = "",
    **_: Any,
) -> tuple[dict[str, Any], str, str]:
    form = {
        "field_name": field_name,
        "well_name": well_name,
        "temperature_c": temperature_c,
        "salinity_g_l": salinity_g_l,
        "permeability_md": permeability_md,
        "water_cut_pct": water_cut_pct,
        "oil_rate_tpd": oil_rate_tpd,
        "api_gravity": api_gravity,
        "lithology": lithology,
        "water_mechanism": water_mechanism,
        "has_fracture": has_fracture == "on",
    }
    return form, expert, company


def _library_stats(n: int = 500) -> dict:
    lib = ensure_patent_library(n=n)
    with lib.open(encoding="utf-8") as f:
        data = json.load(f)
    molecules = data.get("molecules", [])
    classes: dict[str, int] = {}
    patents: set[str] = set()
    for m in molecules:
        classes[m.get("class", "other")] = classes.get(m.get("class", "other"), 0) + 1
        if m.get("patent_ref"):
            patents.add(m["patent_ref"])
    sample = molecules[:8]
    return {
        "count": len(molecules),
        "classes": classes,
        "unique_patents": len(patents),
        "description": data.get("description", ""),
        "path": str(lib),
        "sample": sample,
    }


def _pipeline_summary(result) -> dict[str, Any]:
    stats = _library_stats(result.total_input)
    return {
        "stages": [asdict(s) for s in result.stages],
        "top5": [asdict(c) for c in result.top5],
        "qspr_candidates": [asdict(q) for q in result.qspr_candidates[:20]],
        "total_input": result.total_input,
        "library_path": result.library_path,
        "library_stats": stats,
    }


def _mechanisms() -> list[dict]:
    return load_json("technologies.json")["water_mechanisms"]


def _validation_with_lab(result, top5_dicts, lab_rows=None):
    validation_before = pipeline_to_lab_validation(result, [])
    overrides = lab_overrides_for_pipeline(top5_dicts, lab_rows or load_lab_measurements())
    validation_after = pipeline_to_lab_validation(result, overrides)
    comparison = build_qsprpred_comparison(validation_before["report"], validation_after["report"])
    return validation_after, comparison


def _recompute_validation_from_session(session: dict) -> tuple[dict | None, dict | None]:
    from vodopritok.demo.context_builder import _pipeline_from_session
    pipeline = _pipeline_from_session(session)
    if not pipeline:
        return None, None
    top5_dicts = session["pipeline"]["top5"]
    return _validation_with_lab(pipeline, top5_dicts, load_lab_measurements())


@app.get("/api/economics")
async def api_economics(
    wc_before: float = 82,
    wc_after: float = 64,
    oil_rate: float = 14.5,
    treatment: float = 900_000,
) -> JSONResponse:
    a = analyze_opex(OpexScenario(
        name="case",
        water_cut_before_pct=wc_before,
        water_cut_after_pct=wc_after,
        oil_rate_tpd=oil_rate,
        treatment_cost_rub=treatment,
    ))
    top_measures = sorted(a.measures, key=lambda m: m.get("estimated_annual_rub", 0), reverse=True)[:5]
    return JSONResponse({
        "annual_savings_rub": a.annual_savings_rub,
        "payback_months": a.payback_months,
        "npv_3yr_rub": a.npv_3yr_rub,
        "water_reduction_m3_year": a.water_reduction_m3_year,
        "net_annual_benefit_rub": a.net_annual_benefit_rub,
        "baseline_water_opex_rub": a.baseline_water_opex_rub,
        "water_opex_after_rub": a.water_opex_after_rub,
        "measures": top_measures,
    })


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    form = _form_defaults()
    session = load_session()
    lead_twin = None
    pipeline_stages = None

    if session and session.get("pipeline"):
        pipeline_stages = session["pipeline"].get("stages")
        top5 = session["pipeline"].get("top5", [])
        if top5:
            lead_twin = {"mol_id": top5[0]["mol_id"], "frrw": top5[0]["predicted_frrw"],
                         "frro": top5[0]["predicted_frro"]}
    else:
        recs = recommend_technologies(_reservoir_from_form(form), top_n=1)
        if recs:
            lead_twin = {"mol_id": recs[0].name_ru, "frrw": "—", "frro": "—", "hint": "Запустите screening"}

    recs = recommend_technologies(_reservoir_from_form(form), top_n=3)
    charts = build_home_charts(session, recs)

    return TEMPLATES.TemplateResponse(request, "home.html", _ctx(
        "home", form=form, session=session, lead_twin=lead_twin,
        pipeline_stages=pipeline_stages, tz_mapping=TZ_MAPPING,
        charts_json=json.dumps(charts) if charts else "null",
    ))


@app.get("/screening", response_class=HTMLResponse)
async def screening_page(request: Request) -> HTMLResponse:
    form = _form_defaults()
    session = load_session()
    expert = session.get("expert", "Эксперт по ОВП") if session else "Эксперт по ОВП"
    company = session.get("company", "Заказчик") if session else "Заказчик"
    recs = recommend_technologies(_reservoir_from_form(form), top_n=3)
    lib = _library_stats(500)
    reservoir = _reservoir_from_form(form)
    return TEMPLATES.TemplateResponse(request, "screening.html", _ctx(
        "screening", form=form, expert=expert, company=company,
        mechanisms=_mechanisms(), recommendations=recs,
        rd_tracks=rd_track_strategy(reservoir),
        result=None, validation=None, error="",
        library_stats=lib, lab_count=len(load_lab_measurements()),
        charts_json=json.dumps({"tech": tech_scores_chart(recs)}),
    ))


@app.post("/screening/run", response_class=HTMLResponse)
async def screening_run(
    request: Request,
    field_name: str = Form("Месторождение Западная Сибирь"),
    well_name: str = Form("Well-101"),
    expert: str = Form("Эксперт по ОВП"),
    company: str = Form("Заказчик"),
    temperature_c: float = Form(85),
    salinity_g_l: float = Form(130),
    permeability_md: float = Form(450),
    water_cut_pct: float = Form(82),
    oil_rate_tpd: float = Form(14.5),
    api_gravity: float = Form(21),
    lithology: str = Form("sandstone"),
    water_mechanism: str = Form("coning"),
    has_fracture: str = Form(""),
) -> HTMLResponse:
    form, expert, company = _form_from_post(
        field_name=field_name, well_name=well_name, expert=expert, company=company,
        temperature_c=temperature_c, salinity_g_l=salinity_g_l, permeability_md=permeability_md,
        water_cut_pct=water_cut_pct, oil_rate_tpd=oil_rate_tpd, api_gravity=api_gravity,
        lithology=lithology, water_mechanism=water_mechanism, has_fracture=has_fracture,
    )
    reservoir = _reservoir_from_form(form)
    recs = recommend_technologies(reservoir, top_n=3)
    try:
        result = run_cheminformatics_pipeline(reservoir=reservoir, n_molecules=500, top_n=5)
        top5_dicts = [asdict(c) for c in result.top5]
        validation, comparison = _validation_with_lab(result, top5_dicts)
        summary = _pipeline_summary(result)
        save_session(
            form, expert, company, summary,
            lab_csv_path=str(get_active_lab_csv()),
            qsprpred_comparison=comparison,
        )
        export_qsprpred_json(validation["report"], OUTPUT_DIR / "qsprpred_validation.json")
        generate_one_pager(reservoir, recs, top5_dicts, expert=expert, company=company)
        twins = build_twins_from_pipeline(result, reservoir)
        if twins:
            summary["lead_twin"] = asdict(twins[0])
            save_session(form, expert, company, summary, lab_csv_path=str(get_active_lab_csv()), qsprpred_comparison=comparison)
        fto = build_fto_rows(top5_dicts)
        risk = build_risk_dashboard(
            reservoir, top5_dicts, recs,
            stages=[asdict(s) for s in result.stages],
            validation_metrics=comparison.get("after"),
            fto_rows=fto,
        )
        wc_after_default = max(reservoir.water_cut_pct - 18, 55)
        return TEMPLATES.TemplateResponse(request, "screening.html", _ctx(
            "screening", form=form, expert=expert, company=company,
            mechanisms=_mechanisms(), recommendations=recs,
            rd_tracks=rd_track_strategy(reservoir),
            result=result, validation=validation, error="", saved=True,
            library_stats=summary.get("library_stats"),
            fto_rows=fto, lab_count=len(load_lab_measurements()),
            risk_dashboard=risk, qsprpred_comparison=comparison,
            eco_defaults={"wc_before": reservoir.water_cut_pct, "wc_after": wc_after_default,
                          "oil_rate": reservoir.oil_rate_tpd},
            charts_json=json.dumps(build_screening_charts(result, recs, validation, comparison)),
            lab_program=_lab_program_payload(),
            opex_plan=_opex_plan_payload(),
            synthesis_assessment=_synthesis_assessment_payload(),
            opr_program=_opr_program_payload(),
        ))
    except Exception as e:
        return TEMPLATES.TemplateResponse(request, "screening.html", _ctx(
            "screening", form=form, expert=expert, company=company,
            mechanisms=_mechanisms(), recommendations=recs,
            rd_tracks=rd_track_strategy(reservoir),
            result=None, error=str(e),
            charts_json=json.dumps({"tech": tech_scores_chart(recs)}),
        ))


@app.get("/digital-twin", response_class=HTMLResponse)
async def twin_page(request: Request) -> HTMLResponse:
    form = _form_defaults()
    reservoir = _reservoir_from_form(form)
    twins = []
    session = load_session()
    try:
        if session and session.get("pipeline"):
            result = run_cheminformatics_pipeline(reservoir=reservoir, top_n=5)
            twins = build_twins_from_pipeline(result, reservoir)
        else:
            result = run_cheminformatics_pipeline(reservoir=reservoir, top_n=5)
            twins = build_twins_from_pipeline(result, reservoir)
    except Exception:
        pass
    return TEMPLATES.TemplateResponse(request, "digital_twin.html", _ctx(
        "twin", twins=twins, form=form, session=session,
        lab_count=len(load_lab_measurements()),
        twin_charts_json=json.dumps({
            "radar": build_twin_radar_bundle(
                twins,
                lab_rows=load_lab_measurements(),
                reservoir_temp_c=reservoir.temperature_c,
            ),
            "economics": economics_chart(twins[0]),
        }) if twins else "null",
    ))


@app.get("/lab-program", response_class=HTMLResponse)
async def lab_program_page(request: Request) -> HTMLResponse:
    session = load_session()
    program = _lab_program_payload()
    return TEMPLATES.TemplateResponse(request, "lab_program.html", _ctx(
        "lab",
        program=program,
        has_session=session is not None,
    ))


@app.post("/lab-program/generate")
async def lab_program_generate() -> RedirectResponse:
    ctx = build_deliverable_context()
    generate_lab_program_doc(ctx, build_lab_program(ctx))
    return RedirectResponse(url="/lab-program?generated=1", status_code=303)


@app.get("/export/lab-program")
async def export_lab_program_doc() -> StreamingResponse:
    ctx = build_deliverable_context()
    path = generate_lab_program_doc(ctx, build_lab_program(ctx))
    return StreamingResponse(
        path.open("rb"),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{path.name}"'},
    )


@app.get("/opex-plan", response_class=HTMLResponse)
async def opex_plan_page(request: Request) -> HTMLResponse:
    plan = _opex_plan_payload()
    return TEMPLATES.TemplateResponse(request, "opex_plan.html", _ctx(
        "opex",
        plan=plan,
        eco_defaults=_eco_defaults(),
    ))


@app.post("/opex-plan/generate")
async def opex_plan_generate() -> RedirectResponse:
    ctx = build_deliverable_context()
    generate_opex_plan_doc(ctx, build_opex_plan(ctx))
    return RedirectResponse(url="/opex-plan?generated=1", status_code=303)


@app.get("/export/opex-plan")
async def export_opex_plan_doc() -> StreamingResponse:
    ctx = build_deliverable_context()
    path = generate_opex_plan_doc(ctx, build_opex_plan(ctx))
    return StreamingResponse(
        path.open("rb"),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{path.name}"'},
    )


@app.get("/cheminformatics", response_class=HTMLResponse)
async def cheminformatics_page(request: Request) -> HTMLResponse:
    assessment = _synthesis_assessment_payload()
    return TEMPLATES.TemplateResponse(request, "cheminformatics.html", _ctx(
        "chem",
        assessment=assessment,
    ))


@app.post("/cheminformatics/generate")
async def cheminformatics_generate() -> RedirectResponse:
    ctx = build_deliverable_context()
    generate_synthesis_assessment_doc(ctx, build_synthesis_assessment(ctx))
    return RedirectResponse(url="/cheminformatics?generated=1", status_code=303)


@app.get("/export/cheminformatics")
async def export_cheminformatics_doc() -> StreamingResponse:
    ctx = build_deliverable_context()
    path = generate_synthesis_assessment_doc(ctx, build_synthesis_assessment(ctx))
    return StreamingResponse(
        path.open("rb"),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{path.name}"'},
    )


@app.get("/opr-program", response_class=HTMLResponse)
async def opr_program_page(request: Request) -> HTMLResponse:
    program = _opr_program_payload()
    return TEMPLATES.TemplateResponse(request, "opr_program.html", _ctx(
        "opr",
        program=program,
    ))


@app.post("/opr-program/generate")
async def opr_program_generate() -> RedirectResponse:
    ctx = build_deliverable_context()
    generate_opr_program_doc(ctx, build_opr_program(ctx))
    return RedirectResponse(url="/opr-program?generated=1", status_code=303)


@app.get("/export/opr-program")
async def export_opr_program_doc() -> StreamingResponse:
    ctx = build_deliverable_context()
    path = generate_opr_program_doc(ctx, build_opr_program(ctx))
    return StreamingResponse(
        path.open("rb"),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{path.name}"'},
    )


@app.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request) -> HTMLResponse:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    session = load_session()
    form = _form_defaults()
    expert = session.get("expert", "Эксперт по ОВП") if session else "Эксперт по ОВП"
    company = session.get("company", "Заказчик") if session else "Заказчик"
    files = sorted(OUTPUT_DIR.glob("*.*"))
    docx = [f for f in files if f.suffix == ".docx"]
    charts = build_reports_charts(session, len(docx))
    return TEMPLATES.TemplateResponse(request, "reports.html", _ctx(
        "reports", files=files, docx_count=len(docx),
        form=form, expert=expert, company=company,
        mechanisms=_mechanisms(), tz_mapping=TZ_MAPPING,
        has_session=session is not None,
        charts_json=json.dumps(charts),
    ))


@app.post("/reports/generate")
async def generate_reports(
    field_name: str = Form("Месторождение"),
    well_name: str = Form(""),
    expert: str = Form("Эксперт по ОВП"),
    company: str = Form("Заказчик"),
    temperature_c: float = Form(85),
    salinity_g_l: float = Form(130),
    permeability_md: float = Form(450),
    water_cut_pct: float = Form(82),
    oil_rate_tpd: float = Form(14.5),
    api_gravity: float = Form(21),
    lithology: str = Form("sandstone"),
    water_mechanism: str = Form("coning"),
    has_fracture: str = Form(""),
) -> RedirectResponse:
    form, expert, company = _form_from_post(
        field_name=field_name, well_name=well_name, expert=expert, company=company,
        temperature_c=temperature_c, salinity_g_l=salinity_g_l, permeability_md=permeability_md,
        water_cut_pct=water_cut_pct, oil_rate_tpd=oil_rate_tpd, api_gravity=api_gravity,
        lithology=lithology, water_mechanism=water_mechanism, has_fracture=has_fracture,
    )
    ctx = build_deliverable_context()
    session = load_session()
    if session:
        save_session(form, expert, company, session.get("pipeline"),
                     lab_csv_path=session.get("lab_csv_path"),
                     qsprpred_comparison=session.get("qsprpred_comparison"))
    else:
        save_session(form, expert, company, None)
    generate_all_deliverables(ctx)
    return RedirectResponse(url="/reports?generated=1", status_code=303)


@app.get("/pitch/print", response_class=HTMLResponse)
async def pitch_print(request: Request) -> HTMLResponse:
    form = _form_defaults()
    session = load_session()
    recs = recommend_technologies(_reservoir_from_form(form), top_n=3)
    reservoir = _reservoir_from_form(form)
    charts = build_pitch_charts(session, recs, reservoir)
    return TEMPLATES.TemplateResponse(request, "pitch_print.html", _ctx(
        "pitch", form=form, session=session, tz_mapping=TZ_MAPPING,
        pitch_points=PITCH_POINTS, recommendations=recs,
        rd_tracks=rd_track_strategy(reservoir),
        opex_plan=_opex_plan_payload(),
        synthesis_assessment=_synthesis_assessment_payload(),
        opr_program=_opr_program_payload(),
        charts_json=json.dumps(charts) if charts else "null",
        print_mode=True,
    ))


@app.post("/lab/upload")
async def lab_csv_upload(file: UploadFile = File(...)) -> RedirectResponse:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    content = await file.read()
    UPLOADED_LAB_CSV.write_bytes(content)
    session = load_session()
    if session and session.get("pipeline"):
        validation, comparison = _recompute_validation_from_session(session)
        if validation:
            export_qsprpred_json(validation["report"], OUTPUT_DIR / "qsprpred_validation.json")
        save_session(
            session["reservoir"], session.get("expert", "Эксперт по ОВП"),
            session.get("company", "Заказчик"), session.get("pipeline"),
            lab_csv_path=str(UPLOADED_LAB_CSV),
            qsprpred_comparison=comparison,
        )
    return RedirectResponse(url="/screening?lab_uploaded=1", status_code=303)


@app.get("/export/one-pager")
async def download_one_pager() -> StreamingResponse:
    session = load_session()
    if not session or not session.get("pipeline"):
        return StreamingResponse(io.BytesIO(b""), status_code=404)
    form = session["reservoir"]
    reservoir = _reservoir_from_form(form)
    recs = recommend_technologies(reservoir, top_n=3)
    path = generate_one_pager(
        reservoir, recs, session["pipeline"]["top5"],
        expert=session.get("expert", "Эксперт"), company=session.get("company", "Заказчик"),
    )
    return StreamingResponse(
        path.open("rb"),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{path.name}"'},
    )


@app.post("/demo/golden")
async def golden_demo_run() -> RedirectResponse:
    from vodopritok.demo.golden import run_golden_demo
    run_golden_demo()
    return RedirectResponse(url="/reports?generated=1&golden=1", status_code=303)


@app.get("/demo/golden/download")
async def golden_demo_download() -> StreamingResponse:
    from vodopritok.demo.golden import GOLDEN_DIR
    zip_path = GOLDEN_DIR / "selecgel-golden-demo.zip"
    if not zip_path.exists():
        from vodopritok.demo.golden import run_golden_demo
        run_golden_demo()
        zip_path = GOLDEN_DIR / "selecgel-golden-demo.zip"
    return StreamingResponse(
        zip_path.open("rb"),
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="selecgel-golden-demo.zip"'},
    )


@app.get("/pitch", response_class=HTMLResponse)
async def pitch_page(request: Request) -> HTMLResponse:
    form = _form_defaults()
    session = load_session()
    recs = recommend_technologies(_reservoir_from_form(form), top_n=3)
    reservoir = _reservoir_from_form(form)
    charts = build_pitch_charts(session, recs, reservoir)
    return TEMPLATES.TemplateResponse(request, "pitch.html", _ctx(
        "pitch", form=form, session=session, tz_mapping=TZ_MAPPING,
        pitch_points=PITCH_POINTS, recommendations=recs,
        rd_tracks=rd_track_strategy(reservoir),
        opex_plan=_opex_plan_payload(),
        synthesis_assessment=_synthesis_assessment_payload(),
        opr_program=_opr_program_payload(),
        charts_json=json.dumps(charts) if charts else "null",
    ))


@app.get("/reports/download/{filename}")
async def download_file(filename: str) -> StreamingResponse:
    path = OUTPUT_DIR / filename
    if not path.exists() or ".." in filename:
        return StreamingResponse(io.BytesIO(b""), status_code=404)
    media = "application/octet-stream"
    if path.suffix == ".docx":
        media = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif path.suffix == ".json":
        media = "application/json"
    return StreamingResponse(path.open("rb"), media_type=media,
                             headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@app.get("/reports/download-all")
async def download_all() -> StreamingResponse:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(OUTPUT_DIR.glob("*.*")):
            zf.write(path, path.name)
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/zip",
                             headers={"Content-Disposition": 'attachment; filename="selecgel-demo-pack.zip"'})
