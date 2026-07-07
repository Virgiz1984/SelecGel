"""Tests for SelecGel demo platform."""

from vodopritok.decision_tree import recommend_technologies
from vodopritok.demo.context_builder import build_fto_rows, top5_to_recipe_candidates
from vodopritok.demo.lab_data import lab_overrides_for_pipeline, load_lab_measurements
from vodopritok.models import ReservoirCard


def test_recommend_technologies_returns_ranked():
    recs = recommend_technologies(ReservoirCard(water_mechanism="coning"), top_n=3)
    assert len(recs) == 3
    assert recs[0].rank == 1
    assert recs[0].score >= recs[1].score


def test_lab_csv_loads_five_rows():
    rows = load_lab_measurements()
    assert len(rows) == 5
    assert rows[0]["rank"] == 1


def test_lab_overrides_match_top5_by_rank():
    top5 = [
        {"mol_id": "PAT-A", "rank": 1, "predicted_frrw": 5, "predicted_frro": 2},
        {"mol_id": "PAT-B", "rank": 2, "predicted_frrw": 4, "predicted_frro": 2},
    ]
    overrides = lab_overrides_for_pipeline(top5)
    assert len(overrides) == 2
    assert overrides[0]["mol_id"] == "PAT-A"
    assert overrides[0]["frrw"] == 6.2


def test_top5_to_recipe_candidates():
    top5 = [{"mol_id": "PAT-AMPS", "predicted_frrw": 5.5, "predicted_frro": 1.8, "rank": 1}]
    cands = top5_to_recipe_candidates(top5)
    assert cands[0].recipe_id == "PAT-AMPS"


def test_fto_rows_for_top5():
    top5 = [{"mol_id": "PAT-AMPS", "rank": 1}]
    rows = build_fto_rows(top5)
    assert rows[0]["mol_id"] == "PAT-AMPS"
    assert "patent_ref" in rows[0]


def test_qsar_top5_predictions_are_not_flat():
    from vodopritok.pipeline.orchestrator import run_cheminformatics_pipeline

    result = run_cheminformatics_pipeline(
        reservoir=ReservoirCard(temperature_c=85, salinity_g_l=130),
        n_molecules=500,
        top_n=5,
        use_molfeat=False,
    )
    frrw = [m.predicted_frrw for m in result.top5]
    frro = [m.predicted_frro for m in result.top5]
    assert len(set(frrw)) >= 3
    assert len(set(frro)) >= 4
    assert max(frrw) - min(frrw) >= 0.25
    assert max(frro) - min(frro) >= 0.35


def test_build_lab_program_has_tracks_phases_and_backup():
    from vodopritok.demo.context_builder import build_deliverable_context
    from vodopritok.lab_program import build_lab_program

    program = build_lab_program(build_deliverable_context())
    assert len(program["phases"]) == 2
    assert program["brine_spec"]["temperature_c"] > 0
    assert len(program["gate_criteria"]) >= 5
    assert len(program["timeline"]) == 8
    assert len(program["synthesis_queue"]) >= 5
    assert program["track2_backup"]
    assert len(program["doe_runs"]) >= 9


def test_generate_lab_program_doc_creates_file(tmp_path):
    from vodopritok.demo.context_builder import build_deliverable_context
    from vodopritok.lab_program import build_lab_program
    from vodopritok.reports import generate_lab_program_doc

    ctx = build_deliverable_context()
    program = build_lab_program(ctx)
    out = tmp_path / "02-programma-laboratornyh-issledovaniy.docx"
    path = generate_lab_program_doc(ctx, program, path=out)
    assert path.exists()
    assert path.stat().st_size > 5000


def test_build_opex_plan_has_measures_and_breakdown():
    from vodopritok.demo.context_builder import build_deliverable_context
    from vodopritok.economics import build_opex_plan

    plan = build_opex_plan(build_deliverable_context())
    assert len(plan["measures"]) >= 10
    assert plan["analysis"].baseline_water_opex_rub > 0
    assert plan["cost_breakdown"]
    assert plan["incremental_savings_rub"] > 0
    assert plan["total_potential_rub"] > plan["analysis"].annual_savings_rub
    assert len(plan["monitoring_kpi"]) >= 5
    assert plan["measures_by_category"]
    assert len(plan["methodology"]) == 5
    assert len(plan["technology_comparison"]) >= 4
    assert plan["implementation_lifecycle"]
    assert plan["competency_evidence"]
    assert plan["expert_competency"]


def test_generate_opex_plan_doc_creates_file(tmp_path):
    from vodopritok.demo.context_builder import build_deliverable_context
    from vodopritok.economics import build_opex_plan
    from vodopritok.reports import generate_opex_plan_doc

    ctx = build_deliverable_context()
    plan = build_opex_plan(ctx)
    out = tmp_path / "06-plan-snizheniya-opex.docx"
    path = generate_opex_plan_doc(ctx, plan, path=out)
    assert path.exists()
    assert path.stat().st_size > 5000


def test_build_synthesis_assessment_has_feasibility_scores():
    from vodopritok.demo.context_builder import build_deliverable_context
    from vodopritok.synthesis_assessment import build_synthesis_assessment

    assessment = build_synthesis_assessment(build_deliverable_context())
    assert len(assessment["methodology"]) == 6
    assert len(assessment["assessments"]) == 5
    assert assessment["assessments"][0]["feasibility_score"] >= 0
    assert assessment["monomer_supply"]
    assert assessment["expert_competency"]
    assert assessment["recommended_count"] >= 1


def test_generate_synthesis_assessment_doc_creates_file(tmp_path):
    from vodopritok.demo.context_builder import build_deliverable_context
    from vodopritok.reports import generate_synthesis_assessment_doc
    from vodopritok.synthesis_assessment import build_synthesis_assessment

    ctx = build_deliverable_context()
    assessment = build_synthesis_assessment(ctx)
    out = tmp_path / "01b-ocenka-sintez-khemoinformatika.docx"
    path = generate_synthesis_assessment_doc(ctx, assessment, path=out)
    assert path.exists()
    assert path.stat().st_size > 5000


def test_build_opr_program_has_injection_and_gate():
    from vodopritok.demo.context_builder import build_deliverable_context
    from vodopritok.opr_program import build_opr_program

    program = build_opr_program(build_deliverable_context())
    assert program["injection"]["volume_m3"] > 0
    assert program["timeline"]
    assert program["monitoring_schedule"]
    assert program["opr_gate"]
    assert program["lab_gate"]
    assert program["economics_preview"]["payback_months"] > 0
    assert len(program["wells_shortlist"]) >= 3
    assert program["expert_competency"]


def test_generate_opr_program_doc_creates_file(tmp_path):
    from vodopritok.demo.context_builder import build_deliverable_context
    from vodopritok.opr_program import build_opr_program
    from vodopritok.reports import generate_opr_program_doc

    ctx = build_deliverable_context()
    program = build_opr_program(ctx)
    out = tmp_path / "04-programma-opr.docx"
    path = generate_opr_program_doc(ctx, program, path=out)
    assert path.exists()
    assert path.stat().st_size > 5000


def test_twin_radar_uses_normalized_asymmetric_profile():
    from vodopritok.demo.lab_data import load_lab_measurements
    from vodopritok.pipeline.orchestrator import run_cheminformatics_pipeline
    from vodopritok.selecgel.digital_twin import build_twins_from_pipeline
    from vodopritok.web.viz import build_twin_radar_bundle, twin_radar

    reservoir = ReservoirCard(temperature_c=85, salinity_g_l=130)
    result = run_cheminformatics_pipeline(reservoir=reservoir, top_n=5, use_molfeat=False)
    twins = build_twins_from_pipeline(result, reservoir)
    radar = twin_radar(twins[0], reservoir.temperature_c)
    values = radar["values"]
    assert len(values) == 5
    assert max(values) <= 10
    assert min(values) >= 0
    assert max(values) - min(values) >= 1.5
    assert radar.get("summary")
    assert radar["values"][4] > 0, "thermal axis should not be zero after calibration"

    bundle = build_twin_radar_bundle(twins, load_lab_measurements(), reservoir.temperature_c)
    assert len(bundle["candidates"]) == 5
    assert bundle["has_lab"]
    assert len(bundle["lab"]) == 5
    frro_scores = [c["values"][1] for c in bundle["candidates"]]
    assert max(frro_scores) - min(frro_scores) >= 0.3


def test_fallback_descriptors_differ_by_mol_id():
    from vodopritok.pipeline.descriptors import _fallback_descriptors

    d1 = _fallback_descriptors("PAT-A|CCO")
    d2 = _fallback_descriptors("PAT-B|CCO")
    assert d1 != d2


def test_environmental_impact_from_opex():
    from vodopritok.economics import OpexScenario, analyze_opex
    from vodopritok.environmental_impact import build_environmental_impact

    analysis = analyze_opex(
        OpexScenario(
            name="test",
            water_cut_before_pct=82,
            water_cut_after_pct=64,
            oil_rate_tpd=14.5,
        )
    )
    impact = build_environmental_impact(
        analysis, tech_id="hrpm", wc_before=82, wc_after=64,
    )
    assert impact["water_reduction_m3_year"] > 0
    assert impact["co2_avoided_tons_year"] > 0
    assert impact["eco_score"] > 0
    assert impact["hse_tier"] in ("low", "medium", "high")
    assert impact["hse_notes"]
