/** Economics slider — live OPEX calc */

async function fetchEconomics(wcBefore, wcAfter, oilRate, treatmentCost) {
  const q = new URLSearchParams({
    wc_before: wcBefore,
    wc_after: wcAfter,
    oil_rate: oilRate,
    treatment: treatmentCost,
  });
  const r = await fetch(`/api/economics?${q}`);
  return r.json();
}

function formatRub(n) {
  return new Intl.NumberFormat('ru-RU').format(Math.round(n)) + ' ₽';
}

function initEconomicsSlider(formDefaults) {
  const wcBefore = document.getElementById('eco-wc-before');
  const wcAfter = document.getElementById('eco-wc-after');
  const oilRate = document.getElementById('eco-oil-rate');
  const treatment = document.getElementById('eco-treatment');
  const out = document.getElementById('eco-output');
  if (!wcBefore || !out) return;

  const update = async () => {
    const data = await fetchEconomics(
      wcBefore.value, wcAfter.value, oilRate.value, treatment.value
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
      </div>${measuresHtml}`;
  };

  [wcBefore, wcAfter, oilRate, treatment].forEach(el => el && el.addEventListener('input', update));
  update();
}
