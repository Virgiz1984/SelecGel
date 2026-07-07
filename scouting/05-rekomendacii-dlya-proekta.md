# Рекомендации для проекта разработки селективного ОВП

## 1. Executive summary

На основании скаутинга рекомендуется **двухтрековая стратегия** с единым финальным gate на лабораторию и ОПР:

| Track | Технология | Обоснование |
|-------|------------|-------------|
| **Track 1 (primary)** | Селективный RPM на базе hydrophobically modified copolymer | Максимальная «селективность» в классическом смысле; bullhead; обширная field-метodology; реализуем за 4 мес. при наличии lab |
| **Track 2 (backup)** | Термотропная полимер-неорганическая композиция (тип МЕГА) | Дифференциация; адаптация к российским пластам; потенциал IP; выше риск по срокам |

**Track 3 (conditional):** RPPG — только если диагностика покажет **fracture/conduit-dominated** water production.

---

## 2. Decision tree для выбора технологии

```
Старт: механизм обводнения известен?
│
├─ НЕТ → диагностика (PLT, temperature log, tracer, production history)
│
└─ ДА
    │
    ├─ Coning / matrix flow, perm < 1 D, sandstone
    │       → Track 1: RPM (+ хемоинформатика monomer ratio)
    │
    ├─ Fracture / channel / wormhole, perm > 1 D
    │       → Track 3: RPPG или bulk gel + механика
    │
    ├─ HTHS gas + bottom water
    │       → Nano-reinforced PEI gel (benchmark 2026 paper)
    │
    └─ Carbonate, oil-wet
            → AMPS copolymer RPM / PPG film + wettability modifier
```

---

## 3. План работ на 4 месяца (50% загрузки)

### Месяц 1: Аналитика + in silico

- [ ] Финализация настоящего scouting report → .docx для заказчика  
- [ ] Сбор данных по целевым пластам заказчика  
- [ ] FTO-скрининг по Track 1 и Track 2  
- [ ] Хемоинформатика: библиотека + Top-15 RPM candidates  
- [ ] **Deliverable 1:** Аналитический отчёт  
- [ ] **Deliverable 2:** Программа лабораторных исследований  

### Месяц 2: Лаборатория Phase 1

- [ ] Синтез 5–8 полимеров (Track 1) + 2–3 термотропных (Track 2)  
- [ ] Rheology, TGA, aging in formation brine  
- [ ] Static adsorption + contact angle  
- [ ] Core flood screening (минимум 12 точек)  
- [ ] Gate: Frrw/Frrо ≥ 3 (RPM) или selective block ≥ 70% water / <30% oil  

### Месяц 3: Лаборатория Phase 2 + ОПР design

- [ ] DoE optimization → 1–2 lead recipes  
- [ ] Long-term aging 30 days (accelerated)  
- [ ] **Deliverable 3:** Отчёт по лаборатории  
- [ ] Candidate well selection (3–5 скважин)  
- [ ] **Deliverable 4:** Программа ОПР  

### Месяц 4: ОПР support + economics

- [ ] Сопровождение 1–2 pilot treatments  
- [ ] Monitoring plan: water cut, oil rate, pressure  
- [ ] **Deliverable 5:** Отчёт по ОПР (preliminary if pilots ongoing)  
- [ ] **Deliverable 6:** План снижения OPEX  

---

## 4. KPI для gate-решений

### Лабораторный gate (переход к ОПР)

| Параметр | RPM target | Gel target |
|----------|------------|------------|
| Frrw (residual) | ≥ 5 | — |
| Frro (residual) | ≤ 2 | — |
| Oil regain permeability | ≥ 70% baseline | ≥ 50% |
| Water regain | ≤ 30% baseline | water block ≥ 80% |
| Aging 30d at T_plast | ΔFrrw < 20% | syneresis < 10% |
| Injectivity | ≤ 30% reduction | pumpable |

### ОПР gate (масштабирование)

| Параметр | Target |
|----------|--------|
| Δ water cut | ≥ −15 abs. % |
| Δ oil rate | ≥ −5% (не хуже) |
| Effect duration | ≥ 6 months |
| Cost per ton reduced water | < benchmark ПГС/ВУС |

---

## 5. Мероприятия по снижению OPEX (preview для Deliverable 6)

1. **Локализация synthesis** — monomers и crosslinkers российского происхождения  
2. **Concentrate delivery** — сухой полимер vs emulsion → logistics  
3. **Bullhead vs CT** — минимизация intervention cost  
4. **Candidate scoring tool** — снижение неуспешных treatments  
5. **Repeat treatment scheduling** — RPM refresh vs full re-gel  
6. **Water handling savings model** — NPV calculator per well  
7. **Chemical compatibility with demulsifiers** — avoid over-treatment  

---

## 6. Команда и ресурсы

| Роль | Загрузка | Функция |
|------|----------|---------|
| External expert (Senior ОВП) | 50% | Lead, programs, interpretation |
| Lab chemist | Outsource | Synthesis, QC |
| Core flood engineer | Outsource | Filtration tests |
| Field coordinator | Internal | OPR wells, pumping |
| Data / cheminformatics | 20% | ML ranking, DoE |
| Project lead (company) | Internal | Access, decisions |

**Минимальная lab infrastructure:** core flood setup, oven, rheometer, TGA, brine preparation, contact angle goniometer.

---

## 7. Риски проекта и митигация

| # | Риск | P | Impact | Митигация |
|---|------|---|--------|-----------|
| 1 | Неверный механизм обводнения | Средня | Высокий | Diagnostics before lab |
| 2 | RPM не работает на карбонате | Средня | Высокий | Track 2 / PPG film |
| 3 | 4 мес. недостаточно для ОПР | Высокая | Средний | Parallel lab + OPR prep; preliminary OPR report |
| 4 | IP infringement | Низкая | Высокий | FTO month 1 |
| 5 | Lab–field gap | Средня | Высокий | Use actual core + live brine |
| 6 | Regulatory HSE | Низкая | Средний | Avoid Cr, limit residual AM |

---

## 8. Итоговая рекомендация

**Разрабатывать:** proprietary **селективный RPM** с элементами хемоинформатики (Track 1), параллельно держать **термотропный gel** как backup для HTHS и сложной минералогии (Track 2).

**Не приоритизировать как primary:** классические ВУС/жидкое стекло (неселективны), импорт HRPM «as-is» (нет IP, санкции).

**Следующий шаг:** получить от заказчика **карточку пласта** (T, salinity, lithology, mechanism) → уточнить Track 1 vs 2 за 1 неделю.

---

*Источники: [06-istochniki-i-literatura.md](06-istochniki-i-literatura.md)*
