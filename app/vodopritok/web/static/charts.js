/* SelecGel chart helpers — Chart.js */

const chartDefaults = {
  color: '#8b9cb3',
  borderColor: '#2d3a4f',
};

Chart.defaults.color = chartDefaults.color;
Chart.defaults.borderColor = chartDefaults.borderColor;

function destroyChart(id) {
  const canvas = document.getElementById(id);
  if (!canvas || !canvas._chart) return;
  canvas._chart.destroy();
  canvas._chart = null;
}

function mountChart(id, config) {
  destroyChart(id);
  const canvas = document.getElementById(id);
  if (!canvas) return null;
  canvas._chart = new Chart(canvas, config);
  return canvas._chart;
}

function updateRadarChart(canvasId, labels, datasets) {
  destroyChart(canvasId);
  mountChart(canvasId, radarChartConfig(labels, datasets));
}

function renderFunnel(id, data) {
  mountChart(id, {
    type: 'bar',
    data: {
      labels: data.labels,
      datasets: [{
        label: 'Кандидатов',
        data: data.values,
        backgroundColor: data.colors || ['#3b82f6', '#8b5cf6', '#22c55e'],
        borderRadius: 6,
      }],
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      plugins: {
        legend: { display: false },
        title: { display: true, text: 'Воронка screening', color: '#e8edf4' },
      },
      scales: {
        x: { grid: { color: '#2d3a4f' } },
        y: { grid: { display: false } },
      },
    },
  });
}

function renderTop5(id, data) {
  mountChart(id, {
    type: 'bar',
    data: {
      labels: data.labels,
      datasets: [
        { label: 'Frrw (вода)', data: data.frrw, backgroundColor: '#3b82f6' },
        { label: 'Frro (нефть)', data: data.frro, backgroundColor: '#f59e0b' },
        { label: 'Gate Frrw=5', data: data.labels.map(() => 5), type: 'line', borderColor: '#22c55e', borderDash: [6, 4], pointRadius: 0, borderWidth: 2, fill: false },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        title: { display: true, text: 'Top-5: селективность (Frrw vs Frro)', color: '#e8edf4' },
      },
      scales: { y: { beginAtZero: true, grid: { color: '#2d3a4f' } } },
    },
  });
}

function renderSelectivity(id, data) {
  mountChart(id, {
    type: 'line',
    data: {
      labels: data.labels,
      datasets: [{
        label: 'Selectivity index',
        data: data.selectivity,
        borderColor: '#22c55e',
        backgroundColor: 'rgba(34,197,94,0.15)',
        fill: true,
        tension: 0.3,
        pointRadius: 5,
      }],
    },
    options: {
      responsive: true,
      plugins: { title: { display: true, text: 'Индекс селективности', color: '#e8edf4' } },
      scales: { y: { beginAtZero: true } },
    },
  });
}

function renderTechScores(id, data) {
  mountChart(id, {
    type: 'bar',
    data: {
      labels: data.labels,
      datasets: [{ label: 'Score', data: data.scores, backgroundColor: '#8b5cf6', borderRadius: 4 }],
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      plugins: {
        legend: { display: false },
        title: { display: true, text: 'Рекомендация технологии', color: '#e8edf4' },
      },
    },
  });
}

function renderQsprpred(id, data) {
  mountChart(id, {
    type: 'scatter',
    data: {
      datasets: [{
        label: 'Predicted vs Observed (Frrw)',
        data: data.predicted.map((p, i) => ({ x: p, y: data.observed[i] })),
        backgroundColor: '#3b82f6',
        pointRadius: 7,
      }, {
        label: 'Ideal y=x',
        data: [{ x: 0, y: 0 }, { x: 10, y: 10 }],
        type: 'line',
        borderColor: '#22c55e',
        borderDash: [4, 4],
        pointRadius: 0,
      }],
    },
    options: {
      responsive: true,
      plugins: { title: { display: true, text: 'QSPRpred: прогноз vs лаборатория', color: '#e8edf4' } },
      scales: {
        x: { title: { display: true, text: 'Predicted' } },
        y: { title: { display: true, text: 'Observed' } },
      },
    },
  });
}

function renderRadar(id, data) {
  if (data.candidates) {
    initInteractiveTwinRadar(id, data);
    return;
  }
  const datasets = [{
    label: 'Lead candidate',
    data: data.values,
    borderColor: '#3b82f6',
    backgroundColor: 'rgba(59,130,246,0.22)',
    pointRadius: 4,
    pointBackgroundColor: '#3b82f6',
  }];
  if (data.gate) {
    datasets.push({
      label: 'Gate (цель)',
      data: data.gate,
      borderColor: '#22c55e',
      backgroundColor: 'rgba(34,197,94,0.06)',
      borderDash: [6, 4],
      pointRadius: 3,
      pointBackgroundColor: '#22c55e',
    });
  }
  mountChart(id, radarChartConfig(data.labels, datasets));
}

const RADAR_PALETTE = ['#3b82f6', '#8b5cf6', '#f59e0b', '#ec4899', '#06b6d4'];

function radarTooltipLabel(context, labels) {
  const idx = context.dataIndex;
  const score = context.parsed.r;
  const profile = context.dataset.rawProfile;
  if (profile && profile.raw) {
    const r = profile.raw;
    const names = ['Frrw', 'Frro', 'Sel.', 'Inj.', 'T°C'];
    const rawVal = [r.frrw, r.frro, r.selectivity_index, r.injectivity_index, r.thermal_stability_c][idx];
    return `${labels[idx]}: ${score}/10 · ${names[idx]}=${rawVal}`;
  }
  return `${labels[idx]}: ${score}/10`;
}

function radarChartConfig(labels, datasets) {
  return {
    type: 'radar',
    data: { labels, datasets },
    options: {
      responsive: true,
      plugins: {
        title: { display: true, text: 'Профиль реагента (норм. 0–10)', color: '#e8edf4' },
        legend: { labels: { color: '#94a3b8' }, position: 'bottom' },
        tooltip: {
          callbacks: {
            label(ctx) {
              return radarTooltipLabel(ctx, labels);
            },
          },
        },
      },
      scales: {
        r: {
          beginAtZero: true,
          min: 0,
          max: 10,
          ticks: { stepSize: 2, color: '#64748b', backdropColor: 'transparent' },
          grid: { color: '#2d3a4f' },
          angleLines: { color: '#334155' },
          pointLabels: { color: '#cbd5e1', font: { size: 11 } },
        },
      },
    },
  };
}

function initInteractiveTwinRadar(canvasId, payload) {
  const state = {
    focusRank: payload.candidates[0]?.rank || 1,
    showLab: payload.has_lab,
  };

  function readVisibleRanks() {
    const ranks = new Set();
    document.querySelectorAll('input[data-radar-candidate]').forEach((el) => {
      if (el.checked) {
        const rank = parseInt(el.getAttribute('data-radar-candidate'), 10);
        if (!Number.isNaN(rank)) ranks.add(rank);
      }
    });
    if (ranks.size === 0 && payload.candidates[0]) {
      ranks.add(payload.candidates[0].rank);
    }
    return ranks;
  }

  function buildDatasets(visibleRanks) {
    const datasets = payload.candidates
      .filter((c) => visibleRanks.has(c.rank))
      .map((c) => {
        const color = RADAR_PALETTE[(c.rank - 1) % RADAR_PALETTE.length];
        const isFocus = c.rank === state.focusRank;
        return {
          label: `#${c.rank} ${c.mol_id}`,
          data: c.values.slice(),
          borderColor: color,
          backgroundColor: color + (isFocus ? '33' : '18'),
          borderWidth: isFocus ? 2.5 : 1.5,
          pointRadius: isFocus ? 5 : 3,
          pointBackgroundColor: color,
          rawProfile: c,
        };
      });

    const labToggle = document.getElementById('radar-lab-toggle');
    const showLab = labToggle ? labToggle.checked : state.showLab;

    if (showLab && payload.lab) {
      payload.lab
        .filter((l) => visibleRanks.has(l.rank))
        .forEach((l) => {
          datasets.push({
            label: `Lab #${l.rank}`,
            data: l.values.slice(),
            borderColor: '#22c55e',
            backgroundColor: 'rgba(34,197,94,0.08)',
            borderDash: [4, 3],
            borderWidth: 2,
            pointRadius: 4,
            pointBackgroundColor: '#22c55e',
            rawProfile: l,
          });
        });
    }

    if (payload.gate) {
      datasets.push({
        label: 'Gate (цель)',
        data: payload.gate.slice(),
        borderColor: '#94a3b8',
        backgroundColor: 'rgba(148,163,184,0.05)',
        borderDash: [6, 4],
        borderWidth: 1.5,
        pointRadius: 2,
        pointBackgroundColor: '#94a3b8',
      });
    }
    return datasets;
  }

  function render() {
    const visibleRanks = readVisibleRanks();
    if (visibleRanks.has(state.focusRank) === false) {
      state.focusRank = Math.min(...visibleRanks);
    }
    updateRadarChart(canvasId, payload.labels, buildDatasets(visibleRanks));
    updateRadarSummary(payload, { focusRank: state.focusRank, showLab: document.getElementById('radar-lab-toggle')?.checked });
  }

  window._twinRadarCtrl = {
    canvasId,
    payload,
    state,
    render,
    setFocus(rank) {
      state.focusRank = rank;
      const cb = document.querySelector(`input[data-radar-candidate="${rank}"]`);
      if (cb) cb.checked = true;
      render();
    },
  };

  render();
  window._twinRadarExport = () => exportChartPng(canvasId, 'selecgel-radar-profile.png');
}

function initTwinRadarControls() {
  const toolbar = document.getElementById('radar-toolbar');
  if (!toolbar || !window._twinRadarCtrl || toolbar.dataset.radarBound === '1') return;
  toolbar.dataset.radarBound = '1';

  toolbar.addEventListener('change', (event) => {
    const target = event.target;
    if (!(target instanceof HTMLInputElement)) return;
    if (target.matches('[data-radar-candidate]') || target.id === 'radar-lab-toggle') {
      window._twinRadarCtrl.render();
    }
  });

  if (!document.body.dataset.radarFocusBound) {
    document.body.dataset.radarFocusBound = '1';
    document.body.addEventListener('click', (event) => {
      const btn = event.target.closest('[data-radar-focus]');
      if (!btn || !window._twinRadarCtrl) return;
      const rank = parseInt(btn.getAttribute('data-radar-focus'), 10);
      if (!Number.isNaN(rank)) window._twinRadarCtrl.setFocus(rank);
    });
  }
}

function updateRadarSummary(payload, state) {
  const panel = document.getElementById('radar-gate-summary');
  if (!panel) return;
  const focusRank = state.focusRank || 1;
  const cand = payload.candidates.find((c) => c.rank === focusRank);
  if (!cand || !cand.summary) {
    panel.innerHTML = '';
    return;
  }
  const lab = payload.lab?.find((l) => l.rank === focusRank);
  let html = `<p class="muted" style="margin:0 0 0.5rem"><strong>${cand.mol_id}</strong> — in silico vs gate</p><div class="radar-gate-chips">`;
  cand.summary.forEach((s) => {
    const cls = s.pass ? 'ok' : 'warn';
    html += `<span class="tag ${cls}">${s.axis}: ${s.score} / ${s.gate}</span>`;
  });
  html += '</div>';
  if (lab && state.showLab) {
    html += `<p class="muted" style="margin:0.75rem 0 0.35rem">Lab #${lab.rank}${lab.notes ? ' — ' + lab.notes : ''}</p><div class="radar-gate-chips">`;
    lab.summary.forEach((s) => {
      const cls = s.pass ? 'ok' : 'warn';
      html += `<span class="tag ${cls}">${s.axis}: ${s.score} / ${s.gate}</span>`;
    });
    html += '</div>';
  }
  panel.innerHTML = html;
}

function renderEconomics(id, data) {
  mountChart(id, {
    type: 'bar',
    data: {
      labels: data.labels,
      datasets: [{
        label: 'Значение',
        data: data.values,
        backgroundColor: ['#22c55e', '#3b82f6', '#f59e0b'],
        borderRadius: 6,
      }],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        title: { display: true, text: 'Экономика скважины', color: '#e8edf4' },
      },
    },
  });
}

function renderStages(id, data) {
  mountChart(id, {
    type: 'bar',
    data: {
      labels: data.labels,
      datasets: [{
        label: 'Кандидатов на выходе',
        data: data.values,
        backgroundColor: ['#3b82f6', '#8b5cf6', '#22c55e', '#f59e0b'].slice(0, data.values.length),
        borderRadius: 6,
      }],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        title: { display: true, text: 'Этапы конвейера', color: '#e8edf4' },
      },
      scales: { y: { beginAtZero: true, grid: { color: '#2d3a4f' } } },
    },
  });
}

function renderDeliverables(id, data) {
  mountChart(id, {
    type: 'doughnut',
    data: {
      labels: data.labels,
      datasets: [{
        data: data.values,
        backgroundColor: data.colors || ['#22c55e', '#374151'],
        borderWidth: 0,
      }],
    },
    options: {
      responsive: true,
      plugins: {
        title: { display: true, text: 'Deliverables по ТЗ (6 docx)', color: '#e8edf4' },
      },
    },
  });
}

function initScreeningCharts(payload) {
  if (!payload) return;
  if (payload.funnel) renderFunnel('chart-funnel', payload.funnel);
  if (payload.top5) {
    renderTop5('chart-top5', payload.top5);
    renderSelectivity('chart-selectivity', payload.top5);
  }
  if (payload.tech) renderTechScores('chart-tech', payload.tech);
  if (payload.qsprpred) renderQsprpred('chart-qsprpred', payload.qsprpred);
  if (payload.qsprpred_mape) renderQsprpredMape('chart-qsprpred-mape', payload.qsprpred_mape);
  if (payload.stages) renderStages('chart-stages', payload.stages);
}

function renderQsprpredMape(id, data) {
  mountChart(id, {
    type: 'bar',
    data: {
      labels: data.labels,
      datasets: [{
        label: 'MAPE Frrw, %',
        data: data.values,
        backgroundColor: ['#f59e0b', '#22c55e'],
        borderRadius: 6,
      }],
    },
    options: {
      responsive: true,
      plugins: {
        title: { display: true, text: 'QSPRpred: до / после lab CSV', color: '#e8edf4' },
      },
      scales: { y: { beginAtZero: true } },
    },
  });
}

function initHomeCharts(payload) {
  if (!payload) return;
  if (payload.funnel) renderFunnel('chart-home-funnel', payload.funnel);
  if (payload.top5) renderTop5('chart-home-top5', payload.top5);
  if (payload.tech) renderTechScores('chart-home-tech', payload.tech);
  if (payload.stages) renderStages('chart-home-stages', payload.stages);
}

function initTwinCharts(radar, economics) {
  if (radar) renderRadar('chart-twin-radar', radar);
  if (economics) renderEconomics('chart-twin-eco', economics);
  initTwinRadarControls();
}

function renderTechEconomics(id, data) {
  mountChart(id, {
    type: 'bar',
    data: {
      labels: data.labels,
      datasets: [
        { label: 'CAPEX, млн ₽', data: data.capex, backgroundColor: '#3b82f6' },
        { label: 'OPEX реагента/год, млн ₽', data: data.annual_opex, backgroundColor: '#f59e0b' },
      ],
    },
    options: {
      responsive: true,
      plugins: { title: { display: true, text: 'Экономика технологий ОВП', color: '#e8edf4' }, legend: { labels: { color: '#94a3b8' } } },
      scales: { x: { ticks: { color: '#94a3b8' } }, y: { ticks: { color: '#94a3b8' } } },
    },
  });
}

function initPitchCharts(payload) {
  if (!payload) return;
  if (payload.tech) renderTechScores('chart-pitch-tech', payload.tech);
  if (payload.tech_economics) renderTechEconomics('chart-pitch-tech-eco', payload.tech_economics);
  if (payload.funnel) renderFunnel('chart-pitch-funnel', payload.funnel);
  if (payload.top5) renderTop5('chart-pitch-top5', payload.top5);
  if (payload.stages) renderStages('chart-pitch-stages', payload.stages);
}

function initReportsCharts(payload) {
  if (!payload) return;
  if (payload.deliverables) renderDeliverables('chart-reports-deliverables', payload.deliverables);
  if (payload.funnel) renderFunnel('chart-reports-funnel', payload.funnel);
  if (payload.top5) renderTop5('chart-reports-top5', payload.top5);
  if (payload.stages) renderStages('chart-reports-stages', payload.stages);
}

function exportChartPng(canvasId, filename) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const link = document.createElement('a');
  link.download = filename || `${canvasId}.png`;
  link.href = canvas.toDataURL('image/png');
  link.click();
}

function exportAllCharts(ids) {
  ids.forEach((id, i) => {
    const canvas = document.getElementById(id);
    if (canvas) exportChartPng(id, `selecgel-${id}.png`);
  });
}

function bootTwinPage() {
  const dataEl = document.getElementById('selecgel-twin-charts');
  if (!dataEl) return;
  try {
    const d = JSON.parse(dataEl.textContent);
    if (d && d.radar && d.radar.candidates) {
      initTwinCharts(d.radar, d.economics);
    } else if (d && d.radar) {
      console.warn('SelecGel: radar без candidates — перезапустите сервер (python -m cli serve --reload)');
      initTwinCharts(d.radar, d.economics);
    }
  } catch (err) {
    console.error('SelecGel twin charts init failed', err);
  }
}

document.addEventListener('DOMContentLoaded', bootTwinPage);
