from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MoleculeRecord:
    mol_id: str
    smiles: str
    name: str
    patent_ref: str = ""
    mol_class: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DescriptorResult:
    mol_id: str
    smiles: str
    rdkit_features: dict[str, float]
    molfeat_features: dict[str, float] = field(default_factory=dict)
    feature_vector: list[float] = field(default_factory=list)
    feature_names: list[str] = field(default_factory=list)


@dataclass
class QSPRScore:
    mol_id: str
    predicted_viscosity_cp: float
    predicted_thermal_stability_c: float
    qspr_score: float
    passed: bool = True


@dataclass
class QSARScore:
    mol_id: str
    predicted_frrw: float
    predicted_frro: float
    selectivity_index: float
    qsar_score: float
    rank: int = 0


@dataclass
class PipelineStage:
    name: str
    tool: str
    input_count: int
    output_count: int
    filter_pct: float
    details: str = ""


@dataclass
class PipelineResult:
    stages: list[PipelineStage]
    descriptors: list[DescriptorResult]
    qspr_candidates: list[QSPRScore]
    top5: list[QSARScore]
    total_input: int
    library_path: str = ""


@dataclass
class QSPRpredValidationRow:
    mol_id: str
    property_name: str
    predicted: float
    observed: float
    residual: float
    abs_error: float
    pct_error: float


@dataclass
class QSPRpredReport:
    rows: list[QSPRpredValidationRow]
    metrics: dict[str, dict[str, float]]  # property -> {rmse, mae, r2, mape}
    summary: str
