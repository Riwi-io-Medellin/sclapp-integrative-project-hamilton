// Companies view: table with search/tech/score filters and scraping modal.
// Loads data from getCompanies(search, tech, score) -> GET /companies/enriched.
// Run scraping via runScraping() -> POST /scraping/start; tech options from getTechnologiesTrending().

import { apiClient } from './apiClient.js';

const FALLBACK_COMPANIES = [];

function scoreToBadge(score) {
  if (score === 3) return 'Alta';
  if (score === 2) return 'Media';
  if (score === 1) return 'Baja';
  return '—';
}

function scoreToClass(score) {
  if (score === 3) return 'badge-alta';
  if (score === 2) return 'badge-media';
  if (score === 1) return 'badge-baja';
  return 'badge-media';
}

export function renderCompaniesView(main) {
  main.innerHTML = `
    <div class="view-container">
      <div class="view-header">
        <div>
          <h2 class="view-title">Companies</h2>
          <p class="view-subtitle">Intelligent data on tech vacancy opportunities</p>
        </div>
        <button class="btn-primario" id="btnOpenScraping">🔍 Run scraping</button>
      </div>

      <div class="filtros-bar">
        <div class="filtro-item" style="flex: 1;">
          <input type="text" class="filtro-input" style="width:100%;" placeholder="🔎 Search by name..." id="filtroBuscar" />
        </div>
        <div class="filtro-item">
          <select class="filtro-select" id="filtroTech">
            <option value="">All technologies</option>
          </select>
        </div>
        <div class="filtro-item">
          <select class="filtro-select" id="filtroScore">
            <option value="">Any score</option>
            <option value="3">High (3)</option>
            <option value="2">Medium (2)</option>
            <option value="1">Low (1)</option>
          </select>
        </div>
      </div>

      <p class="view-subtitle" style="margin-bottom:8px;margin-top:0;">Companies identified from remote job postings and scored by AI relevance.</p>
      <div class="tabla-wrapper">
        <table class="tabla">
          <thead>
            <tr>
              <th>Company</th>
              <th>Technologies</th>
              <th>Category</th>
              <th>Location</th>
              <th>AI Score</th>
            </tr>
          </thead>
          <tbody id="tablaBody"></tbody>
        </table>
      </div>
    </div>

    <div class="panel-overlay" id="modalScraping" style="display:none;">
      <div class="panel">
        <div class="panel-header">
          <h3>🔍 Configure scraping</h3>
          <button class="modal-cerrar" id="btnCloseScraping">✕</button>
        </div>
        <div class="panel-body">
          <div class="form-group">
            <label>Search platform</label>
            <select class="filtro-select" style="width:100%;" id="scrapingSource">
              <option value="remotive">Remotive</option>
              <option value="remoteok">RemoteOK</option>
              <!-- <option value="getonboard">GetOnBoard</option> -->
            </select>
          </div>
          <div class="form-group">
            <label>Target technology / role (optional)</label>
            <input type="text" class="filtro-input" style="width:100%;" placeholder="e.g. python, react, data (optional)" id="scrapingQuery" />
          </div>
          <div id="scrapingStatus" style="margin-top:15px;"></div>
        </div>
        <div class="panel-footer">
          <button class="btn-cancelar" id="btnCancelScraping">Cancel</button>
          <button class="btn-primario" id="btnStartScraping">Start search</button>
        </div>
      </div>
    </div>
  `;

  let companiesData = [];

  function renderTableRows() {
    const tbody = document.getElementById('tablaBody');
    if (!tbody) return;

    const filtered = companiesData;

    if (filtered.length === 0) {
      tbody.innerHTML =
        '<tr><td colspan="5" class="tabla-vacia">🔍 No companies found. Run scraping or adjust filters.</td></tr>';
      return;
    }

    tbody.innerHTML = filtered
      .map((e) => {
        const scoreLabel = e.scoreLabel ?? scoreToBadge(e.scoreNum);
        const scoreClass = scoreToClass(e.scoreNum);
        return `
          <tr>
            <td>
              <div style="display:flex;align-items:center;gap:10px;">
                <div style="width:30px;height:30px;background:#1a2535;border-radius:6px;display:flex;align-items:center;justify-content:center;color:#2dd4bf;font-weight:bold;font-size:12px;">${(e.nombre || '—')[0]}</div>
                <span style="font-weight:600;color:#e2e8f0;">${e.nombre || '—'}</span>
              </div>
            </td>
            <td style="color:#64748b;font-size:12px;">${e.tech || '—'}</td>
            <td style="color:#64748b;font-size:12px;">${e.nivel || '—'}</td>
            <td style="color:#64748b;font-size:12px;">${e.ciudad || '—'}</td>
            <td><span class="badge ${scoreClass}">${scoreLabel}</span></td>
          </tr>
        `;
      })
      .join('');
  }

  async function loadTechnologyOptions() {
    const techSelect = document.getElementById('filtroTech');
    if (!techSelect) return;
  
    try {
      const trend = await apiClient.getTechnologiesTrending();
  
      techSelect.innerHTML = '<option value="">All technologies</option>';
  
      if (Array.isArray(trend) && trend.length > 0) {
        trend.forEach((item) => {
          const option = document.createElement('option');
          option.value = item.name_tech || '';
          option.textContent = `${item.name_tech || '—'} (${item.companies_using ?? 0})`;
          techSelect.appendChild(option);
        });
      }
    } catch (error) {
      techSelect.innerHTML = '<option value="">All technologies</option>';
    }
  }

  async function loadCompanies() {
    const search = document.getElementById('filtroBuscar')?.value?.trim() || '';
    const tech = document.getElementById('filtroTech')?.value || '';
    const score = document.getElementById('filtroScore')?.value || '';
    try {
      const data = await apiClient.getCompanies(search, tech, score);
      if (Array.isArray(data) && data.length > 0) {
        companiesData = data.map((c) => ({
          nombre: c.name || '—',
          tech: typeof c.technologies === 'string' ? c.technologies : (Array.isArray(c.technologies) ? c.technologies.join(', ') : '—'),
          nivel: c.category || '—',
          ciudad: c.country || '—',
          scoreNum: c.score != null ? Number(c.score) : null,
          scoreLabel: scoreToBadge(c.score != null ? Number(c.score) : null),
        }));
      } else {
        companiesData = [];
      }
    } catch (_) {
      companiesData = [...FALLBACK_COMPANIES];
    }
    renderTableRows();
  }

  ['filtroBuscar', 'filtroTech', 'filtroScore'].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.addEventListener(id === 'filtroBuscar' ? 'input' : 'change', loadCompanies);
  });

  document.getElementById('btnOpenScraping')?.addEventListener('click', () => {
    document.getElementById('modalScraping').style.display = 'flex';
  });

  document.getElementById('btnCloseScraping')?.addEventListener('click', () => {
    document.getElementById('modalScraping').style.display = 'none';
    document.getElementById('scrapingStatus').innerHTML = '';
  });

  document.getElementById('btnCancelScraping')?.addEventListener('click', () => {
    document.getElementById('modalScraping').style.display = 'none';
    document.getElementById('scrapingStatus').innerHTML = '';
  });

  document.getElementById('btnStartScraping')?.addEventListener('click', async () => {
    const queryEl = document.getElementById('scrapingQuery');
    const statusEl = document.getElementById('scrapingStatus');
    const query = queryEl?.value?.trim() || '';
  
  
    statusEl.innerHTML = `
      <div style="padding:15px;background:rgba(45,212,191,0.05);border:1px dashed #2dd4bf44;border-radius:8px;text-align:center;">
        <p style="color:#2dd4bf;font-size:13px;margin-bottom:5px;">⏳ Searching vacancies ${query ? `for "${query}"` : "(general search)"}...</p>
        <div style="width:100%;height:3px;background:#1a2535;border-radius:10px;overflow:hidden;">
          <div id="scrapingBar" style="width:0;height:100%;background:#2dd4bf;transition:width 3s linear;"></div>
        </div>
      </div>
    `;
  
    setTimeout(() => {
      const bar = document.getElementById('scrapingBar');
      if (bar) bar.style.width = '100%';
    }, 50);
  
    let result = null;
  
    try {
      // Limit scraping size for demo to reduce API usage and avoid hitting OpenAI quota
      result = await apiClient.runScraping({
        parameters: {
          source: document.getElementById('scrapingSource')?.value || 'remotive',
          query,
          max_items: 3,
          only_riwi_relevant: true,
          require_junior_focus: false
        }
      });
  
      statusEl.innerHTML = `
        <div style="padding:15px;background:rgba(52,211,153,0.1);border:1px solid #34d39944;border-radius:8px;text-align:center;">
          <p style="color:#34d399;font-size:13px;font-weight:600;">✅ Scraping completed!</p>
          <p style="color:#64748b;font-size:11px;">
            Found: ${result?.total_found ?? 0} · New: ${result?.total_new ?? 0} · Updated: ${result?.total_updated ?? 0} · Failed: ${result?.total_failed ?? 0}
          </p>
        </div>
      `;

      if (result?.total_new > 0 || result?.total_updated > 0) {
        loadTechnologyOptions();
      }
  
      loadCompanies();
    } catch (error) {
      statusEl.innerHTML = `
        <div style="padding:15px;background:rgba(239,68,68,0.1);border:1px solid #ef444444;border-radius:8px;text-align:center;">
          <p style="color:#ef4444;font-size:13px;font-weight:600;">❌ Scraping failed</p>
          <p style="color:#64748b;font-size:11px;">Please try again.</p>
        </div>
      `;
    }
  });

  loadTechnologyOptions();
  loadCompanies();
}


