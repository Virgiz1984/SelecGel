from __future__ import annotations

from dataclasses import dataclass

from vodopritok.models import load_json


@dataclass
class SupplierOffer:
    supplier_id: str
    supplier_name: str
    marketplace: str
    monomer: str
    unit_price_rub_kg: float
    moq_kg: float
    lead_time_days: int
    origin: str
    score: float
    total_cost_rub: float = 0.0


@dataclass
class SupplyChainPlan:
    """Модуль 3: оптимизация цепочки поставок (Chemexsol-style)."""

    required_monomers: list[str]
    offers: list[SupplierOffer]
    best_bundle: list[SupplierOffer]
    total_cost_rub: float
    total_lead_time_days: int
    savings_vs_import_pct: float
    recommendation: str


# Mock marketplace data (Chemexsol / локальные поставщики)
_MARKETPLACE_CATALOG = [
    {"id": "CX-001", "name": "Chemexsol RF", "marketplace": "Chemexsol", "monomer": "AM", "price": 185, "moq": 500, "lead": 14, "origin": "РФ"},
    {"id": "CX-002", "name": "Chemexsol RF", "marketplace": "Chemexsol", "monomer": "AMPS", "price": 420, "moq": 200, "lead": 21, "origin": "РФ"},
    {"id": "CX-003", "name": "SNF Volgograd", "marketplace": "Direct", "monomer": "AM", "price": 172, "moq": 1000, "lead": 10, "origin": "РФ"},
    {"id": "CX-004", "name": "SIBUR Monomers", "marketplace": "Direct", "monomer": "NVP", "price": 380, "moq": 300, "lead": 18, "origin": "РФ"},
    {"id": "CX-005", "name": "Import EU (legacy)", "marketplace": "Trader", "monomer": "AMPS", "price": 650, "moq": 100, "lead": 45, "origin": "EU"},
    {"id": "CX-006", "name": "Tomsk Polychem", "marketplace": "Chemexsol", "monomer": "PEI", "price": 890, "moq": 50, "lead": 12, "origin": "РФ"},
    {"id": "CX-007", "name": "Kemira RF", "marketplace": "Chemexsol", "monomer": "ATAC", "price": 510, "moq": 150, "lead": 16, "origin": "РФ"},
    {"id": "CX-008", "name": "Local Synthesis", "marketplace": "Direct", "monomer": "C12AM", "price": 1200, "moq": 25, "lead": 30, "origin": "РФ"},
]


def _score_offer(price: float, lead: int, origin: str) -> float:
    score = 100 - price / 20 - lead * 0.5
    if origin == "РФ":
        score += 15
    return round(score, 1)


def optimize_supply_chain(
    batch_kg: float = 500,
    monomers: list[str] | None = None,
) -> SupplyChainPlan:
    mono_data = load_json("monomers.json")
    default = [m["id"] for m in mono_data["monomers"][:4]]
    required = monomers or default

    offers: list[SupplierOffer] = []
    for req in required:
        matching = [c for c in _MARKETPLACE_CATALOG if c["monomer"] == req]
        for item in matching:
            qty = max(batch_kg * 0.3, item["moq"])
            cost = qty * item["price"]
            offers.append(SupplierOffer(
                supplier_id=item["id"],
                supplier_name=item["name"],
                marketplace=item["marketplace"],
                monomer=item["monomer"],
                unit_price_rub_kg=item["price"],
                moq_kg=item["moq"],
                lead_time_days=item["lead"],
                origin=item["origin"],
                score=_score_offer(item["price"], item["lead"], item["origin"]),
                total_cost_rub=round(cost, 0),
            ))

    offers.sort(key=lambda o: (-o.score, o.total_cost_rub))

    best: list[SupplierOffer] = []
    covered: set[str] = set()
    for o in offers:
        if o.monomer not in covered:
            best.append(o)
            covered.add(o.monomer)
        if covered >= set(required):
            break

    total_cost = sum(o.total_cost_rub for o in best)
    import_cost = sum(
        o.total_cost_rub for o in best if o.origin != "РФ"
    ) or total_cost
    rf_cost = sum(o.total_cost_rub for o in best if o.origin == "РФ")
    savings = round((1 - rf_cost / max(import_cost, 1)) * 100, 1) if import_cost else 0

    return SupplyChainPlan(
        required_monomers=required,
        offers=offers,
        best_bundle=best,
        total_cost_rub=round(total_cost, 0),
        total_lead_time_days=max((o.lead_time_days for o in best), default=14),
        savings_vs_import_pct=max(0, savings),
        recommendation=(
            f"Оптимальный bundle: {len(best)} поставщиков, "
            f"{total_cost:,.0f} ₽, lead time {max((o.lead_time_days for o in best), default=14)} дн. "
            f"Приоритет — российское происхождение (Chemexsol / Direct)."
        ),
    )
