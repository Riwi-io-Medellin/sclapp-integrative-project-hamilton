import { apiClient } from './apiClient.js';

let techChartInstance = null;
let companiesChartInstance = null;
let chartJsLoaderPromise = null;

function toNumber(value, fallback = 0) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function destroyCharts() {
  if (techChartInstance) {
    techChartInstance.destroy();
    techChartInstance = null;
  }
  if (companiesChartInstance) {
    companiesChartInstance.destroy();
    companiesChartInstance = null;
  }
}

function setBlockStatus(targetId, text, color = '#64748b') {
  const el = document.getElementById(targetId);
  if (!el) return;
  el.textContent = text;
  el.style.color = color;
}

function sanitizeAiText(text) {
  const raw = String(text || '').trim();
  if (!raw) return '';
  const blocked = [
    'correo',
    'correos',
    'open rate',
    'pipeline',
    'negoci',
    'outreach',
    'engagement',
    'email',
    'apertura',
  ];
  const normalized = raw.toLowerCase();
  return blocked.some((token) => normalized.includes(token)) ? '' : raw;
}

function buildLocalAiFallback(topTech = [], topCompanies = []) {
  const mainTech = topTech[0]?.name_tech || 'las tecnologías líderes';
  const secondTech = topTech[1]?.name_tech || null;
  const topCompany = topCompanies[0]?.name || 'las empresas con mayor score';
  const secondCompany = topCompanies[1]?.name || null;

  const summary =
    secondTech
      ? `El mercado muestra concentración en ${mainTech} y ${secondTech}, con señales de demanda sostenida en stacks técnicos específicos.`
      : `El mercado muestra concentración en ${mainTech}, lo que ayuda a priorizar oportunidades con mejor afinidad tecnológica.`;

  const highlights = [
    secondTech
      ? `Tecnologías dominantes: ${mainTech} y ${secondTech}.`
      : `Tecnología dominante: ${mainTech}.`,
    secondCompany
      ? `Empresas mejor posicionadas por score: ${topCompany} y ${secondCompany}.`
      : `Empresa mejor posicionada por score: ${topCompany}.`,
    'La combinación score + tecnología permite una priorización más precisa del seguimiento.',
  ];

  return {
    summary,
    highlights,
    recommendation:
      'Enfoca el seguimiento primero en las empresas top score que comparten las tecnologías más repetidas del ranking para acelerar resultados de market intelligence.',
  };
}

function renderAiReport(report, topTech = [], topCompanies = []) {
  const box = document.getElementById('aiReportList');
  if (!box) return;

  const safeSummary = sanitizeAiText(report?.summary);
  const safeRecommendation = sanitizeAiText(report?.recommendation);
  const safeHighlights = Array.isArray(report?.highlights)
    ? report.highlights.map(sanitizeAiText).filter(Boolean)
    : [];

  const normalized = (safeSummary && safeRecommendation && safeHighlights.length >= 2)
    ? { summary: safeSummary, highlights: safeHighlights.slice(0, 4), recommendation: safeRecommendation }
    : buildLocalAiFallback(topTech, topCompanies);

  box.innerHTML = `
    <div class="reporte-item">
      <span class="reporte-item-ico">📌</span>
      <span><strong style="color:#e2e8f0;">Resumen:</strong> ${normalized.summary}</span>
    </div>
    ${normalized.highlights.map((item) => `
      <div class="reporte-item">
        <span class="reporte-item-ico">•</span>
        <span>${item}</span>
      </div>
    `).join('')}
    <div class="reporte-item">
      <span class="reporte-item-ico">🎯</span>
      <span><strong style="color:#e2e8f0;">Recomendación:</strong> ${normalized.recommendation}</span>
    </div>
  `;
}

function ensureChartJsLoaded() {
  if (window.Chart) return Promise.resolve();
  if (chartJsLoaderPromise) return chartJsLoaderPromise;

  chartJsLoaderPromise = new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js';
    script.onload = () => resolve();
    script.onerror = () => reject(new Error('Chart.js could not be loaded'));
    document.head.appendChild(script);
  });

  return chartJsLoaderPromise;
}

function renderTechChart(data) {
  const canvas = document.getElementById('chartTopTech');
  if (!canvas || !window.Chart) return;

  if (techChartInstance) {
    techChartInstance.destroy();
    techChartInstance = null;
  }

  // Normaliza solo formato y conserva orden de entrada.
  const chartData = Array.isArray(data)
    ? data
      .map((t) => ({
        name_tech: t?.name_tech ?? '—',
        companies_using: toNumber(t?.companies_using, 0),
      }))
      .filter((t) => t.name_tech && t.name_tech !== '—')
    : [];

  // LOG TEMPORAL: data enviada a la gráfica (orden final).
  console.log('[Dashboard][TopTech][ChartInput]', chartData);

  techChartInstance = new window.Chart(canvas, {
    type: 'bar',
    data: {
      labels: chartData.map((t) => t.name_tech),
      datasets: [
        {
          label: 'Empresas',
          data: chartData.map((t) => t.companies_using),
          // Paleta mockup (teal principal)
          backgroundColor: 'rgba(6, 214, 160, 0.35)',
          borderColor: '#06d6a0',
          borderWidth: 1.5,
          borderRadius: 8,
          borderSkipped: false,
          barThickness: 14,
          hoverBackgroundColor: 'rgba(6, 214, 160, 0.55)',
        },
      ],
    },
    options: {
      indexAxis: 'y', // ranking horizontal más legible
      responsive: true,
      maintainAspectRatio: false,
      layout: { padding: { top: 4, right: 8, bottom: 4, left: 4 } },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#073b4c',
          borderColor: '#1a2535',
          borderWidth: 1,
          titleColor: '#e2e8f0',
          bodyColor: '#94a3b8',
          displayColors: false,
        },
      },
      scales: {
        x: {
          beginAtZero: true,
          grid: { color: '#1a2535', lineWidth: 1 },
          border: { color: '#1a2535' },
          ticks: {
            color: '#94a3b8',
            font: { size: 11, weight: '600' },
            precision: 0,
          },
        },
        y: {
          grid: { display: false },
          border: { color: '#1a2535' },
          ticks: {
            color: '#e2e8f0',
            font: { size: 11, weight: '600' },
            // Evita que Chart.js oculte etiquetas intermedias (ej. kubernetes).
            autoSkip: false,
          },
        },
      },
    },
  });
}

function renderCompaniesChart(scoreDistribution) {
  const canvas = document.getElementById('chartCompaniesDonut');
  if (!canvas || !window.Chart) return;

  if (companiesChartInstance) {
    companiesChartInstance.destroy();
    companiesChartInstance = null;
  }

  const labels = ['Alto', 'Medio', 'Bajo'];
  let values = [0, 0, 0];
  let total = 0;

  // Nuevo endpoint: { high, medium, low, total_scored }
  if (scoreDistribution && typeof scoreDistribution === 'object' && !Array.isArray(scoreDistribution)) {
    values = [
      toNumber(scoreDistribution.high, 0),
      toNumber(scoreDistribution.medium, 0),
      toNumber(scoreDistribution.low, 0),
    ];
    total = toNumber(scoreDistribution.total_scored, values.reduce((a, b) => a + b, 0));
  } else {
    // Compatibilidad: si accidentalmente llega el array de /companies/top
    const counts = { Alto: 0, Medio: 0, Bajo: 0 };
    for (const c of scoreDistribution || []) {
      const score = c?.score;
      if (score === 3) counts.Alto += 1;
      else if (score === 2) counts.Medio += 1;
      else if (score === 1) counts.Bajo += 1;
    }
    values = [counts.Alto, counts.Medio, counts.Bajo];
    total = values.reduce((a, b) => a + b, 0);
  }
  const legendEl = document.getElementById('companyScoreLegend');
  if (legendEl) {
    legendEl.innerHTML = labels
      .map((label, idx) => {
        const dotColor =
          label === 'Alto' ? '#06d6a0' : label === 'Medio' ? '#ffd166' : '#ef476f';
        const val = values[idx] ?? 0;
        return `
          <div style="display:flex;align-items:center;gap:8px;color:#e2e8f0;font-size:12px;">
            <div style="width:9px;height:9px;border-radius:50%;background:${dotColor};box-shadow:0 0 0 3px rgba(26,37,53,0.35);"></div>
            <span style="color:#94a3b8;">${label}:</span>
            <span style="color:#e2e8f0;font-weight:800;">${val}</span>
          </div>
        `;
      })
      .join('');
  }

  if (!total) {
    // Vacío de score: dejamos estado visual sin romper el dashboard.
    if (legendEl) legendEl.style.opacity = '0.7';
    return;
  }

  companiesChartInstance = new window.Chart(canvas, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [
        {
          label: 'Distribución por score',
          data: values.map((v) => toNumber(v, 0)),
          backgroundColor: ['#06d6a0', '#ffd166', '#ef476f'],
          hoverBackgroundColor: ['#06d6a0', '#ffd166', '#ef476f'],
          borderColor: '#1a2535',
          borderWidth: 2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      layout: { padding: { top: 2, right: 8, bottom: 2, left: 8 } },
      plugins: {
        legend: { display: false },
        title: { display: false },
        tooltip: {
          backgroundColor: '#073b4c',
          borderColor: '#1a2535',
          borderWidth: 1,
          titleColor: '#e2e8f0',
          bodyColor: '#94a3b8',
          displayColors: false,
        },
      },
      cutout: '62%',
    },
  });
}

function normalizeStats(stats, trend = [], topCompanies = []) {
  const totalCompanies = toNumber(
    stats?.total_companies ?? stats?.companies_with_vacancies ?? stats?.companies_analyzed,
    0,
  );
  const scoredCompanies = toNumber(stats?.scored_companies ?? stats?.companies_scored, 0);

  // Si backend no trae top_score_detected, usamos score máximo del endpoint /companies/top.
  const topScoreDetected = toNumber(
    stats?.top_score_detected ?? topCompanies?.[0]?.score ?? stats?.high_score_companies,
    0,
  );

  // Si backend no trae technologies_detected, usamos cantidad de tecnologías del ranking.
  const technologiesDetected = toNumber(
    stats?.technologies_detected ?? trend?.length,
    0,
  );

  return { totalCompanies, scoredCompanies, topScoreDetected, technologiesDetected };
}

export function renderDashboardView(main) {
  destroyCharts();

  main.innerHTML = `
    <div class="view-container">
      <!-- ====== HEADER HERO (mockup) ====== -->
      <div
        class="dashboard-hero"
        style="
          position: relative;
          overflow: hidden;
          border-radius: 12px;
          border: 1px solid #1a2535;
          background-image: url('assets/img/9k.png');
          background-size: cover;
          background-position: center;
          margin-bottom: 16px;
        "
      >
        <div
          style="
            position: absolute;
            inset: 0;
            background: linear-gradient(
              to right,
              rgba(0, 0, 0, 0.65) 0%,
              rgba(0, 0, 0, 0.45) 30%,
              rgba(0, 0, 0, 0.15) 60%,
              rgba(0, 0, 0, 0.0) 100%
            );
          "
        ></div>
        <div
          style="
            position: relative;
            padding: 34px 28px;
            display: flex;
            justify-content: space-between;
            gap: 16px;
            align-items: flex-start;
          "
        >
          <div>
            <div style="font-size: 12px; font-weight: 700; color: #e2e8f0; margin-bottom: 8px; text-shadow: 0 2px 10px rgba(0,0,0,0.5);">
              Buenos días 👋
            </div>
            <p style="margin: 10px 0 0; color: #e2e8f0; font-size: 13px; max-width: 680px; line-height: 1.6; text-shadow: 0 2px 10px rgba(0,0,0,0.5);">
              Sclapp convierte datos del mercado en priorización inteligente de empresas y tecnologías.
            </p>
          </div>

          <div class="view-header-botones" style="margin-top: 4px;">
            <button class="btn-secundario" id="btnRefreshDashboard">↻ Actualizar dashboard</button>
            <button class="btn-primario" id="btnGenerateAiReport">✦ Generar Reporte IA</button>
          </div>
        </div>
      </div>

      <div class="kpis-grid">
        <div class="kpi-card">
          <div class="kpi-top">
            <div class="kpi-icono-box teal">🏢</div>
            <span class="kpi-cambio positivo">Market</span>
          </div>
          <div class="kpi-numero" id="kpiTotalCompanies">...</div>
          <div class="kpi-label">Empresas analizadas</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-top">
            <div class="kpi-icono-box purple">🛡</div>
            <span class="kpi-cambio positivo">Scoring</span>
          </div>
          <div class="kpi-numero" id="kpiScoredCompanies">...</div>
          <div class="kpi-label">Empresas con score</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-top">
            <div class="kpi-icono-box orange">🏆</div>
            <span class="kpi-cambio positivo">Top</span>
          </div>
          <div class="kpi-numero" id="kpiTopScore">...</div>
          <div class="kpi-label">Top score detectado</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-top">
            <div class="kpi-icono-box blue">⚙</div>
            <span class="kpi-cambio positivo">Stack</span>
          </div>
          <div class="kpi-numero" id="kpiTechnologies">...</div>
          <div class="kpi-label">Tecnologías detectadas</div>
        </div>
      </div>

      <div class="graficas-row-2" style="margin-bottom:16px;">
        <div class="grafica-card">
          <div class="grafica-top">
            <span class="grafica-titulo">Top tecnologías más buscadas</span>
          </div>
          <p class="grafica-subtitulo" id="topTechStatus">Cargando datos...</p>
          <div class="chart-box">
            <canvas id="chartTopTech"></canvas>
          </div>
        </div>

        <div class="grafica-card">
          <div class="grafica-top">
            <span class="grafica-titulo">Distribución de empresas por score</span>
          </div>
          <p class="grafica-subtitulo" id="topCompaniesStatus">Cargando datos...</p>
          <div class="chart-box">
            <canvas id="chartCompaniesDonut"></canvas>
          </div>
          <div style="margin-top: 12px; display: flex; gap: 14px; flex-wrap: wrap;" id="companyScoreLegend"></div>
        </div>
      </div>

      <div class="reporte-card">
        <div class="reporte-encabezado">
          <div>
            <div class="reporte-titulo">✦ AI Executive Report</div>
            <div class="reporte-subtitulo" id="aiReportStatus">Listo para generar análisis.</div>
          </div>
          <button class="btn-secundario" id="btnGenerateAiReportInline">Generar</button>
        </div>
        <div class="reporte-lista" id="aiReportList">
          <div class="reporte-item">
            <span class="reporte-item-ico">🧠</span>
            <span>Haz clic en "Generar Reporte IA" para construir un análisis ejecutivo con datos reales del mercado.</span>
          </div>
        </div>
      </div>
    </div>
  `;

  let latestTopTech = [];
  let latestTopCompanies = [];

  async function loadMainData() {
    setBlockStatus('topTechStatus', 'Cargando datos...');
    setBlockStatus('topCompaniesStatus', 'Cargando datos...');
    document.getElementById('kpiTotalCompanies').textContent = '...';
    document.getElementById('kpiScoredCompanies').textContent = '...';
    document.getElementById('kpiTopScore').textContent = '...';
    document.getElementById('kpiTechnologies').textContent = '...';

    try {
      await ensureChartJsLoaded();
    } catch (_) {
      setBlockStatus('topTechStatus', 'No se pudo cargar Chart.js.', '#f87171');
      setBlockStatus('topCompaniesStatus', 'No se pudo cargar Chart.js.', '#f87171');
      return;
    }

    const [statsRes, techRes, companiesRes, scoreDistRes] = await Promise.allSettled([
      apiClient.getDashboardStats(),
      apiClient.getTechnologiesTrending(),
      apiClient.getCompaniesTop(),
      apiClient.getDashboardScoreDistribution(),
    ]);

    const stats = statsRes.status === 'fulfilled' ? statsRes.value : {};
    const topTech = (techRes.status === 'fulfilled' && Array.isArray(techRes.value)) ? techRes.value.slice(0, 10) : [];
    const topCompanies = (companiesRes.status === 'fulfilled' && Array.isArray(companiesRes.value)) ? companiesRes.value.slice(0, 10) : [];
    const scoreDistribution = scoreDistRes.status === 'fulfilled' ? scoreDistRes.value : null;

    // LOG TEMPORAL: respuesta cruda del endpoint de tecnologías.
    console.log('[Dashboard][TopTech][API]', techRes.status === 'fulfilled' ? techRes.value : techRes.reason);

    latestTopTech = topTech;
    latestTopCompanies = topCompanies;

    const normalized = normalizeStats(stats, topTech, topCompanies);
    document.getElementById('kpiTotalCompanies').textContent = String(normalized.totalCompanies);
    document.getElementById('kpiScoredCompanies').textContent = String(normalized.scoredCompanies);
    document.getElementById('kpiTopScore').textContent = String(normalized.topScoreDetected);
    document.getElementById('kpiTechnologies').textContent = String(normalized.technologiesDetected);

    if (topTech.length === 0) {
      setBlockStatus('topTechStatus', 'Sin datos para Top tecnologías.', '#94a3b8');
      if (techChartInstance) {
        techChartInstance.destroy();
        techChartInstance = null;
      }
    } else {
      setBlockStatus('topTechStatus', `${topTech.length} tecnologías cargadas.`);
      // LOG TEMPORAL: array exacto que se manda al render.
      console.log('[Dashboard][TopTech][ToRender]', topTech);
      renderTechChart(topTech);
    }

    // Donut: usa distribución global por score (no el top)
    if (!scoreDistribution || toNumber(scoreDistribution.total_scored, 0) === 0) {
      setBlockStatus('topCompaniesStatus', 'Sin datos para Top empresas.', '#94a3b8');
      if (companiesChartInstance) {
        companiesChartInstance.destroy();
        companiesChartInstance = null;
      }
    } else {
      setBlockStatus('topCompaniesStatus', `Total scoreados: ${scoreDistribution.total_scored}.`);
      renderCompaniesChart(scoreDistribution);
    }

    if (statsRes.status === 'rejected') {
      console.warn('Dashboard stats error:', statsRes.reason);
    }
    if (techRes.status === 'rejected') {
      console.warn('Trending technologies error:', techRes.reason);
      setBlockStatus('topTechStatus', 'Error cargando tecnologías.', '#f87171');
    }
    if (scoreDistRes.status === 'rejected') {
      console.warn('Score distribution error:', scoreDistRes.reason);
      setBlockStatus('topCompaniesStatus', 'Error cargando distribución por score.', '#f87171');
    }
  }

  async function loadAiReport() {
    setBlockStatus('aiReportStatus', 'Generando reporte...');
    const reportList = document.getElementById('aiReportList');
    if (reportList) {
      reportList.innerHTML = `
        <div class="reporte-item">
          <span class="reporte-item-ico">⏳</span>
          <span>Analizando tecnologías y empresas para priorización...</span>
        </div>
      `;
    }

    try {
      const report = await apiClient.getDashboardAiReport();
      renderAiReport(report, latestTopTech, latestTopCompanies);
      setBlockStatus('aiReportStatus', 'Reporte generado con datos actuales.', '#64748b');
    } catch (error) {
      console.warn('AI report error:', error);
      renderAiReport(null, latestTopTech, latestTopCompanies);
      setBlockStatus('aiReportStatus', 'Error IA: se mostró fallback de market intelligence.', '#f59e0b');
    }
  }

  document.getElementById('btnRefreshDashboard')?.addEventListener('click', loadMainData);
  document.getElementById('btnGenerateAiReport')?.addEventListener('click', loadAiReport);
  document.getElementById('btnGenerateAiReportInline')?.addEventListener('click', loadAiReport);

  loadMainData();
}

