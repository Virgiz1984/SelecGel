from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent / "data"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


def load_json(name: str) -> dict[str, Any]:
    path = DATA_DIR / name
    with path.open(encoding="utf-8") as f:
        return json.load(f)


@dataclass
class ReservoirCard:
    """Карточка пласта заказчика."""

    field_name: str = "Месторождение"
    well_name: str = ""
    temperature_c: float = 80.0
    pressure_mpa: float = 15.0
    salinity_g_l: float = 120.0
    ca2_mg_l: float = 500.0
    lithology: str = "sandstone"
    wettability: str = "water_wet"
    permeability_md: float = 500.0
    porosity_pct: float = 18.0
    water_mechanism: str = "coning"
    water_cut_pct: float = 85.0
    oil_rate_tpd: float = 12.0
    water_rate_m3pd: float = 45.0
    api_gravity: float = 22.0
    has_fracture: bool = False
    previous_ovp: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "field_name": self.field_name,
            "well_name": self.well_name,
            "temperature_c": self.temperature_c,
            "pressure_mpa": self.pressure_mpa,
            "salinity_g_l": self.salinity_g_l,
            "ca2_mg_l": self.ca2_mg_l,
            "lithology": self.lithology,
            "wettability": self.wettability,
            "permeability_md": self.permeability_md,
            "porosity_pct": self.porosity_pct,
            "water_mechanism": self.water_mechanism,
            "water_cut_pct": self.water_cut_pct,
            "oil_rate_tpd": self.oil_rate_tpd,
            "water_rate_m3pd": self.water_rate_m3pd,
            "api_gravity": self.api_gravity,
            "has_fracture": self.has_fracture,
            "previous_ovp": self.previous_ovp,
        }


@dataclass
class LabResult:
    """Результат лабораторного core flood."""

    recipe_id: str
    recipe_name: str
    frrw: float
    frro: float
    oil_regain_pct: float
    water_regain_pct: float
    aging_days: int = 30
    aging_frrw_delta_pct: float = 0.0
    injectivity_reduction_pct: float = 15.0
    passed_gate: bool = False
    notes: str = ""


@dataclass
class OprResult:
    """Результат опытно-промышленных работ."""

    well_name: str
    technology: str
    treatment_date: str
    water_cut_before_pct: float
    water_cut_after_pct: float
    oil_rate_before_tpd: float
    oil_rate_after_tpd: float
    effect_duration_months: int = 0
    treatment_cost_rub: float = 0.0
    notes: str = ""


@dataclass
class ProjectContext:
    """Контекст проекта для генерации документов."""

    expert_name: str = "Эксперт по ОВП"
    company_name: str = "Заказчик"
    project_start: str = "2026-07-01"
    project_end: str = "2026-10-28"
    budget_rub: float = 1_500_000.0
    reservoir: ReservoirCard = field(default_factory=ReservoirCard)
    lab_results: list[LabResult] = field(default_factory=list)
    opr_results: list[OprResult] = field(default_factory=list)
    session_data: dict | None = None

    def ensure_output_dir(self) -> Path:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        return OUTPUT_DIR
