/** Economics slider — live OPEX calc */

async function fetchEconomics(wcBefore, wcAfter, oilRate, treatmentCost, techId) {
  const q = new URLSearchParams({
    wc_before: wcBefore,
    wc_after: wcAfter,
    oil_rate: oilRate,
    treatment: treatmentCost,
  });
  if (techId) q.set('tech_id', techId);
  const r = await fetch(`/api/economics?${q}`);
  return r.json();
}

function formatRub(n) {
  return new Intl.NumberFormat('ru-RU').format(Math.round(n)) + ' ₽';
}

function formatNum(n) {
  return new Intl.NumberFormat('ru-RU').format(Math.round(n));
}

function renderEnvironmentalBlock(env) {
  if (!env) return '';
  const notes = (env.hse_notes || [])
    .map((n) => `<li>${n}</li>`)
    .join('');
  return `
    <section class="env-panel-inline" style="margin-top:1rem;padding-top:0.75rem;border-top:1px solid var(--border)">
      <div class="env-header">
        <h3 style="font-size:1rem;margin:0">Экологический эффект</h3>
        <span class="env-score">Eco-score ${env.eco_score}/100</span>
      </div>
      <p class="muted" style="font-size:0.8rem;margin:0.35rem 0">${env.methodology_note || ''}</p>
      <div class="env-grid">
        <div class="env-kpi"><span class="muted">Сокращение воды</span><strong>${formatNum(env.water_reduction_m3_year)} m³/год</strong></div>
        <div class="env-kpi"><span class="muted">Меньше сброса</span><strong>${formatNum(env.disposal_reduction_m3_year)} m³/год</strong></div>
        <div class="env-kpi"><span class="muted">Энергия подъёма</span><strong>−${env.energy_savings_mwh_year} МВт·ч/год</strong></div>
        <div class="env-kpi"><span class="muted">CO₂-прокси</span><strong>−${env.co2_avoided_tons_year} т/год</strong></div>
        <div class="env-kpi"><span class="muted">Объём закачки</span><strong>${env.injection_volume_m3} m³</strong></div>
        <div class="env-kpi"><span class="muted">Δ WC</span><strong>${env.wc_reduction_pp} п.п.</strong></div>
      </div>
      <div class="env-hse">
        <span class="env-badge tier-${env.hse_tier}">HSE: ${env.hse_tier_ru}</span>
        <span class="muted">${env.hse_label}</span>
      </div>
      <ul class="env-notes">${notes}</ul>
    </section>`;
}

function initEconomicsSlider(formDefaults) {
  const wcBefore = document.getElementById('eco-wc-before');
  const wcAfter = document.getElementById('eco-wc-after');
  const oilRate = document.getElementById('eco-oil-rate');
  const treatment = document.getElementById('eco-treatment');
  const out = document.getElementById('eco-output');
  const techId = (formDefaults && formDefaults.tech_id) || 'hrpm';
  if (!wcBefore || !out) return;

  const update = async () => {
    const data = await fetchEconomics(
      wcBefore.value, wcAfter.value, oilRate.value, treatment.value, techId
    );
    let measuresHtml = '';
    if (data.measures && data.measures.length) {
      measuresHtml = '<p class="muted" style="margin:0.75rem 0 0.35rem">Топ мероприятий по эффекту:</p><ul style="margin:0;padding-left:1.2rem;font-size:0.85rem">';
      data.measures.slice(0, 3).forEach((m) => {
        measuresHtml += `<li>${m.measure} — ${formatRub(m.estimated_annual_rub)}/год</li>`;
      });
      measuresHtml += '</ul>';
    }
    out.innerHTML = `
      <div class="eco-grid">
        <div class="eco-kpi"><span class="muted">OPEX воды до</span><strong>${formatRub(data.baseline_water_opex_rub)}</strong></div>
        <div class="eco-kpi"><span class="muted">Экономия/год</span><strong>${formatRub(data.annual_savings_rub)}</strong></div>
        <div class="eco-kpi"><span class="muted">Payback</span><strong>${data.payback_months.toFixed(1)} мес</strong></div>
        <div class="eco-kpi"><span class="muted">NPV 3 года</span><strong>${formatRub(data.npv_3yr_rub)}</strong></div>
        <div class="eco-kpi"><span class="muted">Сокращение воды</span><strong>${Math.round(data.water_reduction_m3_year).toLocaleString('ru')} m³/год</strong></div>
        <div class="eco-kpi"><span class="muted">OPEX воды после</span><strong>${formatRub(data.water_opex_after_rub)}</strong></div>
      </div>${measuresHtml}${renderEnvironmentalBlock(data.environmental)}`;
  };

  [wcBefore, wcAfter, oilRate, treatment].forEach(el => el && el.addEventListener('input', update));
  update();
}
