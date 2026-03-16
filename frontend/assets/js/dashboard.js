import { apiClient } from './apiClient.js';

// Dashboard view: KPIs and lists from backend.
// Calls: getDashboardStats(), getCompaniesTop(), getTechnologiesTrending().
export function renderDashboardView(main) {
  main.innerHTML = `
    <div class="view-container">

      <div class="view-header">
        <div>
          <h2 class="view-title">Dashboard</h2>
          <p class="view-subtitle">Intelligent data for real opportunities</p>
        </div>
      </div>

      <!-- ====== KPIs (filled by loadDashboardStats) ====== -->
      <div class="kpis-grid">
        <div class="kpi-card">
          <div class="kpi-top">
            <div class="kpi-icono-box teal">🏢</div>
            <span class="kpi-cambio positivo" id="kpi1Trend">—</span>
          </div>
          <div class="kpi-numero" id="kpiTotalCompanies">—</div>
          <div class="kpi-label">Companies with vacancies</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-top">
            <div class="kpi-icono-box blue">✉</div>
            <span class="kpi-cambio positivo" id="kpi2Trend">—</span>
          </div>
          <div class="kpi-numero" id="kpiEmailsSent">—</div>
          <div class="kpi-label">Emails sent</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-top">
            <div class="kpi-icono-box purple">🛡</div>
            <span class="kpi-cambio positivo" id="kpi3Trend">—</span>
          </div>
          <div class="kpi-numero" id="kpiScored">—</div>
          <div class="kpi-label">Scored (AI)</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-top">
            <div class="kpi-icono-box orange">📈</div>
            <span class="kpi-cambio positivo" id="kpi4Trend">—</span>
          </div>
          <div class="kpi-numero" id="kpiHighScore">—</div>
          <div class="kpi-label">High score (3)</div>
        </div>
      </div>

      <!-- Top companies and trending technologies -->
      <div class="graficas-row" style="margin-bottom:20px;">
        <div class="grafica-card" style="flex:1;">
          <span class="grafica-titulo">Top companies by score</span>
          <div id="topCompaniesList" class="reporte-lista" style="max-height:220px;overflow-y:auto;">
            <p style="color:#64748b;font-size:13px;">Loading…</p>
          </div>
        </div>
        <div class="grafica-card" style="flex:1;">
          <span class="grafica-titulo">Trending technologies</span>
          <div id="trendingTechList" class="reporte-lista" style="max-height:220px;overflow-y:auto;">
            <p style="color:#64748b;font-size:13px;">Loading…</p>
          </div>
        </div>
      </div>

    </div>
  `;

  async function loadDashboardStats() {
    if (!document.getElementById('kpiTotalCompanies')) return;

    try {
      const stats = await apiClient.getDashboardStats();
      if (stats) {
        const el1 = document.getElementById('kpiTotalCompanies');
        const el2 = document.getElementById('kpiEmailsSent');
        const el3 = document.getElementById('kpiScored');
        const el4 = document.getElementById('kpiHighScore');
        if (el1) el1.textContent = stats.total_companies ?? '—';
        if (el2) el2.textContent = stats.emails_sent ?? '—';
        if (el3) el3.textContent = stats.scored_companies ?? '—';
        if (el4) el4.textContent = stats.high_score_companies ?? '—';
      }
    } catch (_) {
      const el1 = document.getElementById('kpiTotalCompanies');
      const el2 = document.getElementById('kpiEmailsSent');
      const el3 = document.getElementById('kpiScored');
      const el4 = document.getElementById('kpiHighScore');
      if (el1) el1.textContent = '0';
      if (el2) el2.textContent = '0';
      if (el3) el3.textContent = '0';
      if (el4) el4.textContent = '0';
    }
    try {
      const top = await apiClient.getCompaniesTop();
      const el = document.getElementById('topCompaniesList');
      if (el) {
        if (Array.isArray(top) && top.length > 0) {
          el.innerHTML = top
            .map(
              (c) =>
                `<div class="reporte-item"><span class="reporte-item-ico">🏢</span><span><strong>${c.name || '—'}</strong> ${c.category || ''} · Score ${c.score ?? '—'}</span></div>`
            )
            .join('');
        } else {
          el.innerHTML = '<p style="color:#64748b;font-size:13px;">No companies with score yet.</p>';
        }
      }
    } catch (_) {
      const el = document.getElementById('topCompaniesList');
      if (el) el.innerHTML = '<p style="color:#64748b;font-size:13px;">Could not load top companies.</p>';
    }
    try {
      const trend = await apiClient.getTechnologiesTrending();
      const el = document.getElementById('trendingTechList');
      if (el) {
        if (Array.isArray(trend) && trend.length > 0) {
          el.innerHTML = trend
            .map(
              (t) =>
                `<div class="reporte-item"><span class="reporte-item-ico">⚙</span><span><strong>${t.name_tech || '—'}</strong> · ${t.companies_using ?? 0} companies</span></div>`
            )
            .join('');
        } else {
          el.innerHTML = '<p style="color:#64748b;font-size:13px;">No technologies yet.</p>';
        }
      }
    } catch (_) {
      const el = document.getElementById('trendingTechList');
      if (el) el.innerHTML = '<p style="color:#64748b;font-size:13px;">Could not load trending tech.</p>';
    }
  }
  loadDashboardStats();
}

