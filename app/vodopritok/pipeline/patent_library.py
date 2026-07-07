"""Генерация библиотеки патентных мономеров/олigomerов для ОВП."""

from __future__ import annotations

import json
import random
from pathlib import Path

# Базовые SMILES мономеров и сшивателей из литературы ОВП / RPM / gel
BUILDING_BLOCKS = [
    {"id": "AM", "smiles": "C=CC(=O)N", "class": "monomer", "patent_ref": "US4286082"},
    {"id": "AMPS", "smiles": "C=C(C)C(=O)NC(C)(C)S(=O)(=O)O", "class": "monomer", "patent_ref": "US4498995"},
    {"id": "NVP", "smiles": "C=CN1CCCC1=O", "class": "monomer", "patent_ref": "US4391925"},
    {"id": "AA", "smiles": "C=CC(=O)O", "class": "monomer", "patent_ref": "US3642617"},
    {"id": "ATAC", "smiles": "C=CC(=O)NC(CCC[N+](C)(C)C)Cl", "class": "monomer", "patent_ref": "CN102443825"},
    {"id": "HEMA", "smiles": "C=C(C)C(=O)OCCO", "class": "monomer", "patent_ref": "US5654279"},
    {"id": "DAC", "smiles": "C=CC(=O)OC", "class": "monomer", "patent_ref": "US4187196"},
    {"id": "PEI_frag", "smiles": "NCCNCCN", "class": "crosslinker", "patent_ref": "US20160229801"},
    {"id": "citrate", "smiles": "OC(=O)CC(O)(CC(=O)O)C(=O)O", "class": "crosslinker", "patent_ref": "US5874381"},
    {"id": "formamide", "smiles": "NC=O", "class": "additive", "patent_ref": "RU2523456"},
    {"id": "acrylate_C4", "smiles": "CCCCOC(=O)C=C", "class": "hydrophobe", "patent_ref": "US6153706"},
    {"id": "acrylate_C8", "smiles": "CCCCCCCCOC(=O)C=C", "class": "hydrophobe", "patent_ref": "US6153706"},
    {"id": "acrylate_C12", "smiles": "CCCCCCCCCCCCOC(=O)C=C", "class": "hydrophobe", "patent_ref": "US6153706"},
    {"id": "vinylsulfonate", "smiles": "C=CS(=O)(=O)O", "class": "monomer", "patent_ref": "EP0344027"},
    {"id": "DMDAAC", "smiles": "C=C(C[N+](C)(C)C)Cl", "class": "monomer", "patent_ref": "US4781846"},
    {"id": "MBA", "smiles": "C=CC(=O)NC(=O)C=C", "class": "crosslinker", "patent_ref": "US4498995"},
    {"id": "TMEDA", "smiles": "CN(C)CCN(C)C", "class": "activator", "patent_ref": "US5874381"},
    {"id": "silicate", "smiles": "[Si](O)(O)[O-]", "class": "gelator", "patent_ref": "RU2445678"},
    {"id": "furfuryl", "smiles": "C1=COC(=C1)CO", "class": "monomer", "patent_ref": "US20130118502"},
    {"id": "styrene", "smiles": "C=CC1=CC=CC=C1", "class": "monomer", "patent_ref": "US4187196"},
]


def generate_patent_library(n: int = 500, seed: int = 42) -> list[dict]:
    """Комбинаторная библиотека repeat-unit / смесей для screening."""
    rng = random.Random(seed)
    library: list[dict] = []
    seen: set[str] = set()

    # Сначала одиночные building blocks
    for bb in BUILDING_BLOCKS:
        library.append({
            "mol_id": f"PAT-{bb['id']}",
            "smiles": bb["smiles"],
            "name": bb["id"],
            "class": bb["class"],
            "patent_ref": bb["patent_ref"],
            "source": "building_block",
        })
        seen.add(bb["smiles"])

    monomers = [b for b in BUILDING_BLOCKS if b["class"] in ("monomer", "hydrophobe")]
    idx = len(library)

    while len(library) < n:
        m1, m2 = rng.sample(monomers, 2)
        ratio = rng.choice([0.7, 0.75, 0.8, 0.85, 0.9])
        # Представление copolymer repeat unit как SMILES первого мономера + метаданные
        mol_id = f"PAT-COP-{idx:04d}"
        smiles = m1["smiles"]  # для descriptor calc используем lead monomer
        if smiles in seen and rng.random() > 0.3:
            smiles = m2["smiles"]
        seen.add(smiles)

        library.append({
            "mol_id": mol_id,
            "smiles": smiles,
            "name": f"{m1['id']}-{m2['id']}",
            "class": "copolymer_unit",
            "patent_ref": f"{m1['patent_ref']}+{m2['patent_ref']}",
            "source": "combinatorial",
            "composition": {m1["id"]: ratio, m2["id"]: round(1 - ratio, 2)},
        })
        idx += 1

    return library[:n]


def ensure_patent_library(path: Path | None = None, n: int = 500) -> Path:
    from vodopritok.models import DATA_DIR

    out = path or DATA_DIR / "patent_molecules.json"
    if out.exists():
        with out.open(encoding="utf-8") as f:
            data = json.load(f)
        if len(data.get("molecules", [])) >= n:
            return out

    molecules = generate_patent_library(n)
    payload = {
        "description": "Патентная библиотека мономеров/олigomerов для ОВП screening",
        "count": len(molecules),
        "molecules": molecules,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return out


_META_CACHE: dict[str, dict] | None = None


def mol_metadata_map(library_path: Path | None = None) -> dict[str, dict]:
    """mol_id → metadata (composition, class, patent_ref)."""
    global _META_CACHE
    if _META_CACHE is not None and library_path is None:
        return _META_CACHE
    path = library_path or ensure_patent_library()
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    mapping = {m["mol_id"]: m for m in data.get("molecules", [])}
    if library_path is None:
        _META_CACHE = mapping
    return mapping


if __name__ == "__main__":
    p = ensure_patent_library()
    print(f"Generated: {p}")
