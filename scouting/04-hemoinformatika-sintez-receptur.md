# Хемоинформатика для синтеза рецептур ОВП

## 1. Задача в контексте проекта

**Цель:** сократить перебор рецептур в лаборатории за счёт:

1. In silico отбора monomers / crosslinkers / surfactants  
2. Предсказания adsorption, rheology, thermal stability, salinity tolerance  
3. Design of Experiments (DoE) для финальной оптимизации 5–15 рецептур вместо 100+  

**Применимо к классам:**

- RPM (copolymer composition, hydrophobic blocks, charge density)
- In-situ gels (PAM/AMPS/NVP ratios, crosslinker selection)
- Термотропные системы (polymer + inorganic gelator synergy)
- PPG (crosslink density, particle modulus — QSPR)

---

## 2. Pipeline хемоинформатики для ОВП

```
┌─────────────────┐
│ Целевой пласт   │  T, P, salinity, Ca²⁺, mineralogy, wettability, API
└────────┬────────┘
         ▼
┌─────────────────┐
│ Библиотека      │  Monomers: AM, AMPS, NVP, ATAC, hydrophobic comonomers
│ building blocks │  Crosslinkers: PEI, citrate-Al, organic, nano-fillers
└────────┬────────┘
         ▼
┌─────────────────┐
│ Descriptor gen  │  MW, charge density, HLB, logP, Tg (polymer), H-bond donors
└────────┬────────┘
         ▼
┌─────────────────┐
│ ML / QSAR       │  Target: Frrw, gel strength, gelation time, adsorption isotherm
└────────┬────────┘
         ▼
┌─────────────────┐
│ MD / docking    │  Polymer–quartz, polymer–calcite, polymer–oil interface
└────────┬────────┘
         ▼
┌─────────────────┐
│ Top-N candidates│  N = 10–20 для синтеза
└────────┬────────┘
         ▼
┌─────────────────┐
│ DoE lab matrix  │  Response surface → оптимум
└─────────────────┘
```

---

## 3. Инструменты и методы

### 3.1. Молекулярные дескрипторы полимеров

| Дескриптор | Связь с ОВП |
|------------|-------------|
| Charge density (COO⁻, SO₃⁻) | Adsorption на кварце/карбонате |
| Hydrophobic block length | RPM associative behavior |
| Molecular weight / distribution | Injectivity vs retention |
| Crosslink density (predicted) | Gel strength, syneresis |
| HLB (для ПАВ/эмульсий) | Emulsion stability in brine |

**Инструменты:** RDKit (monomers/oligomers), BioPython, custom polymer descriptors, Polymer Genome Project databases.

### 3.2. QSAR / Machine Learning

| Target property | Model type | Training data |
|-----------------|------------|---------------|
| Gelation time | Gradient boosting / RF | Historical lab + literature |
| Swollen gel strength (PPG) | ANN | SPE datasets, university papers |
| RPM residual resistance factor | Multi-task ML | Core flood results |
| Thermal degradation T | Group contribution + ML | TGA literature |

**Подход:** transfer learning — pretrain on public polymer EOR datasets, fine-tune on **закрытых данных заказчика** после лаборатории Phase 1.

### 3.3. Молекулярная динамика (MD)

- **Polymer adsorption on SiO₂ (sandstone proxy)** — оптимизация ionic monomer ratio  
- **Calcite surface (carbonate)** — NVP/AMPS copolymers, wettability change  
- **Oil–water–rock three-phase** — qualitative ranking of RPM candidates  

**ПО:** GROMACS, LAMMPS, Materials Studio (commercial), OpenMM.

### 3.4. Generative design (перспектива)

- **Generative AI for polymer repeat units** — emerging in 2024–2025 literature for EOR polymers  
- Constraint: synthesizability, HSE, cost of comonomers in РФ  

---

## 4. Конкретные гипотезы для in silico screening

### Гипотеза A: RPM для песчаника Западной Сибири

**Optimize:** AM-co-AMPS-co-hydrophobic comonomer  
**Predict:** Langmuir adsorption constant on quartz, layer thickness vs salinity  
**Lab validate:** 5 copolymers × 3 MW → core flood Frrw/Frro  

### Гипотеза B: Термотропный dual-gel (МЕГА-type)

**Optimize:** ratio polymer : silicate / siliconorganic : nano-colloid  
**Predict:** gelation T threshold, syneresis at 90°C 30 days  
**Lab validate:** rheology vs T sweep, core plug selective flow  

### Гипотеза C: PEI-crosslinked gel for HTHS

**Optimize:** PEI branch density, polymer MW, nano-SiO₂ loading  
**Benchmark:** 2026 HTHS paper (>95% water block, <35% gas block)  
**Lab validate:** long-term stability cell 60+ days  

### Гипотеза D: RPPG re-crosslinker package

**Optimize:** hyperbranched crosslinker structure  
**Predict:** re-crosslinking kinetics vs T  
**Lab validate:** fracture model cell  

---

## 5. Design of Experiments (DoE) — связка с хемоинформатикой

После in silico Top-10:

| Factor | Levels | Response |
|--------|--------|----------|
| Polymer conc., % | 3 | Frrw |
| Crosslinker conc. | 3 | Gel strength |
| Salinity match | 2 | Stability |
| T test | 2 | Aging |
| Hydrophobe mol.% | 3 | Frro |

**Design:** Box-Behnken or D-optimal (15–25 runs)  
**Software:** Statistica, JMP, Python (pyDOE3, scikit-learn)

---

## 6. Data requirements от заказчика

Для калибровки моделей необходимо собрать на старте проекта:

1. Минералогия и granulometry керна  
2. Composition formation water (Na⁺, Ca²⁺, Mg²⁺, HCO₃⁻, TDS)  
3. T, P пласта  
4. Wettability (contact angle)  
5. Permeability, porosity, fracture description  
6. История обводнения (coning vs channeling)  
7. Архив предыдущих ОВП на месторождении (если есть)  

---

## 7. Риски хемоинформатического подхода

| Риск | Митигация |
|------|-----------|
| Мало training data | Start with literature + expert rules; active learning |
| Полимеры — не small molecules | Oligomer/repeat-unit approximation |
| MD слишком дорогой | Coarse-grained models; rank-only |
| Gap sim ↔ lab | Mandatory core flood validation gate |
| IP conflicts | FTO before synthesis |

---

## 8. Ожидаемый вклад в срок проекта (4 мес.)

| Этап | Недели | Output |
|------|--------|--------|
| Data collection + library setup | 1–2 | Monomer library, targets |
| Descriptor + ML ranking | 3–5 | Top-15 candidates |
| Expert review + FTO screen | 5–6 | Top-8 for synthesis |
| Lab DoE (parallel with exp.) | 7–12 | Calibrated model v2 |
| Final recipe recommendation | 13–16 | 1–2 lead formulations |

---

## 9. Рекомендуемый software stack (open + commercial)

| Комponent | Option |
|-----------|--------|
| Cheminformatics | RDKit, Open Babel |
| ML | scikit-learn, XGBoost, PyTorch |
| MD | GROMACS + OPLS-AA / CHARMM |
| DoE | JMP or Python pyDOE3 |
| LIMS / data | Excel → PostgreSQL or ELN (Benchling alternative) |
| Patent search | Espacenet, Rospatent |

---

*Следующий документ: [05-rekomendacii-dlya-proekta.md](05-rekomendacii-dlya-proekta.md)*
