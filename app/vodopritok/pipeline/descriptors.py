from __future__ import annotations

from typing import Any

from .models import DescriptorResult, MoleculeRecord

RDKIT_DESCRIPTORS = [
    "MolWt", "MolLogP", "TPSA", "NumHDonors", "NumHAcceptors",
    "NumRotatableBonds", "NumAromaticRings", "FractionCSP3",
    "HeavyAtomCount", "RingCount",
]


def _check_rdkit():
    try:
        from rdkit import Chem
        from rdkit.Chem import Descriptors, rdMolDescriptors
        return Chem, Descriptors, rdMolDescriptors
    except ImportError as e:
        raise ImportError(
            "RDKit не установлен. Установите: pip install rdkit"
        ) from e


def _check_molfeat():
    try:
        from molfeat.calc import RDKit2D
        return RDKit2D()
    except ImportError:
        return None


def compute_rdkit_descriptors(smiles: str) -> dict[str, float]:
    Chem, Descriptors, rdMolDescriptors = _check_rdkit()
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {k: 0.0 for k in RDKIT_DESCRIPTORS}

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

    Chem, _, _ = _check_rdkit()
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
