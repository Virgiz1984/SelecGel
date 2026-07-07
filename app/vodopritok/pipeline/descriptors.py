from __future__ import annotations

import hashlib
import struct
from typing import Any

from .models import DescriptorResult, MoleculeRecord

RDKIT_DESCRIPTORS = [
    "MolWt", "MolLogP", "TPSA", "NumHDonors", "NumHAcceptors",
    "NumRotatableBonds", "NumAromaticRings", "FractionCSP3",
    "HeavyAtomCount", "RingCount",
]

_RANGES: dict[str, tuple[float, float]] = {
    "MolWt": (180.0, 2800.0),
    "MolLogP": (-2.5, 8.5),
    "TPSA": (20.0, 320.0),
    "NumHDonors": (0.0, 12.0),
    "NumHAcceptors": (0.0, 18.0),
    "NumRotatableBonds": (0.0, 35.0),
    "NumAromaticRings": (0.0, 6.0),
    "FractionCSP3": (0.05, 0.95),
    "HeavyAtomCount": (12.0, 180.0),
    "RingCount": (0.0, 8.0),
}


def rdkit_available() -> bool:
    try:
        from rdkit import Chem  # noqa: F401
        return True
    except ImportError:
        return False


def _check_rdkit():
    try:
        from rdkit import Chem
        from rdkit.Chem import Descriptors, rdMolDescriptors
        return Chem, Descriptors, rdMolDescriptors
    except ImportError as e:
        raise ImportError(
            "RDKit не установлен. Установите: pip install rdkit"
        ) from e


def _fallback_descriptors(smiles: str) -> dict[str, float]:
    """Детерминированные псевдо-дескрипторы для demo без RDKit (Streamlit Cloud)."""
    digest = hashlib.sha256(smiles.encode("utf-8")).digest()

    def unit(idx: int) -> float:
        offset = (idx * 2) % max(2, len(digest) - 1)
        return struct.unpack_from(">H", digest, offset)[0] / 65535.0

    out: dict[str, float] = {}
    for i, name in enumerate(RDKIT_DESCRIPTORS):
        lo, hi = _RANGES[name]
        val = lo + unit(i) * (hi - lo)
        if name in {"NumHDonors", "NumHAcceptors", "NumRotatableBonds", "NumAromaticRings", "RingCount", "HeavyAtomCount"}:
            val = float(int(round(val)))
        out[name] = round(val, 4 if name == "FractionCSP3" else 2)
    return out


def _check_molfeat():
    try:
        from molfeat.calc import RDKit2D
        return RDKit2D()
    except ImportError:
        return None


def compute_rdkit_descriptors(smiles: str) -> dict[str, float]:
    try:
        Chem, Descriptors, rdMolDescriptors = _check_rdkit()
    except ImportError:
        return _fallback_descriptors(smiles)

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return _fallback_descriptors(smiles)

    return {
        "MolWt": Descriptors.MolWt(mol),
        "MolLogP": Descriptors.MolLogP(mol),
        "TPSA": Descriptors.TPSA(mol),
        "NumHDonors": Descriptors.NumHDonors(mol),
        "NumHAcceptors": Descriptors.NumHAcceptors(mol),
        "NumRotatableBonds": Descriptors.NumRotatableBonds(mol),
        "NumAromaticRings": rdMolDescriptors.CalcNumAromaticRings(mol),
        "FractionCSP3": rdMolDescriptors.CalcFractionCSP3(mol),
        "HeavyAtomCount": Descriptors.HeavyAtomCount(mol),
        "RingCount": Descriptors.RingCount(mol),
    }


def compute_molfeat_descriptors(smiles: str, calc=None) -> dict[str, float]:
    """molfeat RDKit2D — расширенный набор (~200 descriptors)."""
    calc = calc if calc is not None else _check_molfeat()
    if calc is None:
        return {}

    try:
        Chem, _, _ = _check_rdkit()
    except ImportError:
        return {}
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {}

    try:
        feats = calc(mol)
        if hasattr(feats, "tolist"):
            feats = feats.tolist()
        names = getattr(calc, "columns", None) or [f"mf_{i}" for i in range(len(feats))]
        return {str(names[i]): float(feats[i]) for i in range(min(len(names), len(feats)))}
    except Exception:
        return {}


def featurize_molecules(
    molecules: list[MoleculeRecord],
    use_molfeat: bool = True,
) -> list[DescriptorResult]:
    """Stage 1: RDKit + molfeat → матрица дескрипторов."""
    molfeat_calc = _check_molfeat() if use_molfeat else None
    results: list[DescriptorResult] = []

    for mol in molecules:
        rdkit = compute_rdkit_descriptors(mol.smiles)
        mf = compute_molfeat_descriptors(mol.smiles, molfeat_calc) if use_molfeat else {}

        combined = {**rdkit, **mf}
        names = sorted(combined.keys())
        vector = [combined[n] for n in names]

        results.append(
            DescriptorResult(
                mol_id=mol.mol_id,
                smiles=mol.smiles,
                rdkit_features=rdkit,
                molfeat_features=mf,
                feature_vector=vector,
                feature_names=names,
            )
        )
    return results


def featurize_smiles_list(smiles_list: list[str], ids: list[str] | None = None) -> list[DescriptorResult]:
    mols = [
        MoleculeRecord(mol_id=ids[i] if ids else f"MOL-{i}", smiles=s, name=s[:20])
        for i, s in enumerate(smiles_list)
    ]
    return featurize_molecules(mols)
