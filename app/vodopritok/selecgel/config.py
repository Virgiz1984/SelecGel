"""SelecGel — product configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum

PRODUCT_NAME = "SelecGel"
PRODUCT_TAGLINE = "Хемоинформатический конвейер для селективного ОВП"
PRODUCT_VERSION = "1.0.0"
PRESENTATION_MODE = os.getenv("SELECGEL_PRESENTATION", "1") != "0"


class SubscriptionTier(str, Enum):
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


@dataclass(frozen=True)
class TierFeatures:
    tier: SubscriptionTier
    name_ru: str
    price_rub_month: int
    screening: bool
    digital_twin: bool
    supply_chain: bool
    feedback_loop: bool
    api_access: bool
    reports_docx: bool
    max_screenings_month: int


TIERS: dict[SubscriptionTier, TierFeatures] = {
    SubscriptionTier.BASIC: TierFeatures(
        tier=SubscriptionTier.BASIC,
        name_ru="Базовый",
        price_rub_month=49_000,
        screening=True,
        digital_twin=False,
        supply_chain=False,
        feedback_loop=False,
        api_access=False,
        reports_docx=False,
        max_screenings_month=10,
    ),
    SubscriptionTier.PROFESSIONAL: TierFeatures(
        tier=SubscriptionTier.PROFESSIONAL,
        name_ru="Профессиональный",
        price_rub_month=149_000,
        screening=True,
        digital_twin=True,
        supply_chain=True,
        feedback_loop=True,
        api_access=True,
        reports_docx=True,
        max_screenings_month=100,
    ),
    SubscriptionTier.ENTERPRISE: TierFeatures(
        tier=SubscriptionTier.ENTERPRISE,
        name_ru="Enterprise",
        price_rub_month=0,  # custom
        screening=True,
        digital_twin=True,
        supply_chain=True,
        feedback_loop=True,
        api_access=True,
        reports_docx=True,
        max_screenings_month=9999,
    ),
}

BUSINESS_MODELS = [
    {
        "id": "saas",
        "name": "Подписка (SaaS)",
        "description": "Ежемесячная/годовая плата. Базовый — скрининг; Профессиональный — полный цикл + API.",
    },
    {
        "id": "outcome",
        "name": "Результат как услуга",
        "description": "Оплата % от сэкономленного OPEX или прироста добычи. Риск и успех разделяются с клиентом.",
    },
    {
        "id": "licensing",
        "name": "Лицензирование рецептур",
        "description": "Продажа права на использование подтверждённых платформой lead formulations.",
    },
    {
        "id": "api",
        "name": "API-доступ",
        "description": "Интеграция QSAR/QSPR-моделей в корпоративные системы заказчика.",
    },
]

MARKET_STATS = {
    "market_2024_usd_b": 2.48,
    "market_2035_usd_b": 5.0,
    "cagr_note": "Быстрорастущий рынок химического ПО для нефтегаза",
}


def get_tier(tier_id: str = "professional") -> TierFeatures:
    try:
        return TIERS[SubscriptionTier(tier_id)]
    except ValueError:
        return TIERS[SubscriptionTier.PROFESSIONAL]
