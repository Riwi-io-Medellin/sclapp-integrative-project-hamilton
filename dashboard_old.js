// =============================================
// dashboard.js — Vista del Dashboard
// Inyecta el HTML del dashboard en #main-content
// Incluye KPIs + 3 gráficas (Chart.js) + Reporte IA
// =============================================

function renderDashboard() {

    var main = document.getElementById('main-content');
  
    main.innerHTML = `
      <div class="view-container">
  
        <!-- Título + botones de acción -->
        <div class="view-header">
          <div>
            <h2 class="view-title">Dashboard</h2>
            <p class="view-subtitle">Intelligent data for real opportunities</p>
          </div>
          <div class="view-header-botones">
            <button class="btn-secundario" onclick="exportarPDF()">📄 Exportar PDF</button>
            <button class="btn-primario" onclick="generarReporteIA()">✦ Generar Reporte IA</button>
          </div>
        </div>
  
        <!-- ====== KPIs ====== -->
        <div class="kpis-grid">
  
          <div class="kpi-card">
            <div class="kpi-top">
              <div class="kpi-icono-box teal">🏢</div>
              <span class="kpi-cambio positivo">↑ +12.5%</span>
            </div>
            <div class="kpi-numero">1,247</div>
            <div class="kpi-label">Empresas con vacantes</div>
          </div>
  
          <div class="kpi-card">
            <div class="kpi-top">
              <div class="kpi-icono-box blue">✉</div>
              <span class="kpi-cambio positivo">↑ +8.3%</span>
            </div>
            <div class="kpi-numero">3,842</div>
            <div class="kpi-label">Correos enviados</div>
          </div>
  
          <div class="kpi-card">
            <div class="kpi-top">
              <div class="kpi-icono-box purple">🛡</div>
              <span class="kpi-cambio positivo">↑ +23.1%</span>
            </div>
            <div class="kpi-numero">89</div>
            <div class="kpi-label">Empresas vinculadas</div>
          </div>
  
          <div class="kpi-card">
            <div class="kpi-top">
              <div class="kpi-icono-box orange">📈</div>
              <span class="kpi-cambio negativo">↓ -2.1%</span>
            </div>
            <div class="kpi-numero">42.7%</div>
            <div class="kpi-label">Tasa de apertura</div>
          </div>
  
        </div>
  
        <!-- ====== Fila 1: Gráfica de área + Donut pipeline ====== -->
        <div class="graficas-row">
  
          <!-- Gráfica de área: actividad de correos -->
          <div class="grafica-card">
            <div class="grafica-top">
              <span class="grafica-titulo">Actividad de correos</span>
              <div class="leyenda">
                <div class="leyenda-item">
                  <div class="leyenda-dot" style="background:#2dd4bf;"></div> Enviados
                </div>
                <div class="leyenda-item">
                  <div class="leyenda-dot" style="background:#f59e0b;"></div> Abiertos
                </div>
                <div class="leyenda-item">
                  <div class="leyenda-dot" style="background:#34d399;"></div> Negociación
                </div>
              </div>
            </div>
            <div class="chart-box">
              <canvas id="chartArea"></canvas>
            </div>
          </div>
  
          <!-- Donut: pipeline kanban -->
          <div class="grafica-card">
            <span class="grafica-titulo">Pipeline</span>
            <div class="chart-box-sm" style="margin-top:12px;">
              <canvas id="chartDonut"></canvas>
            </div>
            <div class="donut-leyenda">
              <div class="donut-item">
                <div class="donut-item-izq">
                  <div class="donut-dot" style="background:#60a5fa;"></div> Ready
                </div>
                <span class="donut-valor">245</span>
              </div>
              <div class="donut-item">
                <div class="donut-item-izq">
                  <div class="donut-dot" style="background:#2dd4bf;"></div> Enviados
                </div>
                <span class="donut-valor">180</span>
              </div>
              <div class="donut-item">
                <div class="donut-item-izq">
                  <div class="donut-dot" style="background:#f59e0b;"></div> Abiertos
                </div>
                <span class="donut-valor">55</span>
              </div>
              <div class="donut-item">
                <div class="donut-item-izq">
                  <div class="donut-dot" style="background:#a78bfa;"></div> Negociación
                </div>
                <span class="donut-valor">42</span>
              </div>
              <div class="donut-item">
                <div class="donut-item-izq">
                  <div class="donut-dot" style="background:#34d399;"></div> Vinculados
                </div>
                <span class="donut-valor">18</span>
              </div>
            </div>
          </div>
  
        </div>
  
        <!-- ====== Fila 2: Gráfica de línea + Reporte IA ====== -->
        <div class="graficas-row-2">
  
          <!-- Gráfica de línea: crecimiento semanal -->
          <div class="grafica-card">
            <span class="grafica-titulo">Empresas vinculadas</span>
            <p class="grafica-subtitulo">Crecimiento semanal</p>
            <div class="chart-box-sm">
              <canvas id="chartLinea"></canvas>
            </div>
          </div>
  
          <!-- Reporte IA -->
          <div class="reporte-card">
            <div class="reporte-encabezado">
              <div>
                <div class="reporte-titulo">✦ Reporte IA</div>
                <div class="reporte-subtitulo">Análisis automático de tu pipeline</div>
              </div>
              <button class="btn-secundario" onclick="exportarPDF()">📄 Exportar PDF</button>
            </div>
            <div class="reporte-lista" id="reporte-lista">
              <div class="reporte-item">
                <span class="reporte-item-ico">📊</span>
                <span>
                  <strong style="color:#e2e8f0;">Tendencia positiva:</strong>
                  Las empresas que usan React y Python tienen un 34% más de probabilidad de contratar talento junior.
                </span>
              </div>
              <div class="reporte-item">
                <span class="reporte-item-ico">🎯</span>
                <span>
                  <strong style="color:#e2e8f0;">Recomendación:</strong>
                  Priorizar startups del sector fintech — 3x más tasa de respuesta que empresas enterprise.
                </span>
              </div>
              <div class="reporte-item">
                <span class="reporte-item-ico">⚡</span>
                <span>
                  <strong style="color:#e2e8f0;">Oportunidad:</strong>
                  18 empresas en "Negociación" llevan más de 5 días sin seguimiento. Re-contacto recomendado.
                </span>
              </div>
            </div>
          </div>
  
        </div>
  
      </div>
    `;
  
    // Crear las gráficas después de inyectar el HTML
    setTimeout(function() {
      crearGraficaArea();
      crearGraficaDonut();
      crearGraficaLinea();
    }, 50);
  }
  
  // ——————————————————————————————————————————
  // Gráfica de área — Actividad de correos
  // ——————————————————————————————————————————
  function crearGraficaArea() {
    var ctx = document.getElementById('chartArea');
    if (!ctx) return;
  
    new Chart(ctx, {
      type: 'line',
      data: {
        labels: ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sab', 'Dom'],
        datasets: [
          {
            label: 'Enviados',
            data: [100, 120, 140, 130, 150, 110, 90],
            borderColor: '#2dd4bf',
            backgroundColor: 'rgba(45,212,191,0.15)',
            fill: true,
            tension: 0.4,
            borderWidth: 2,
            pointRadius: 0
          },
          {
            label: 'Abiertos',
            data: [40, 50, 55, 60, 70, 55, 45],
            borderColor: '#f59e0b',
            backgroundColor: 'rgba(245,158,11,0.15)',
            fill: true,
            tension: 0.4,
            borderWidth: 2,
            pointRadius: 0
          },
          {
            label: 'Negociación',
            data: [5, 8, 6, 10, 12, 8, 6],
            borderColor: '#34d399',
            backgroundColor: 'rgba(52,211,153,0.05)',
            fill: true,
            tension: 0.4,
            borderWidth: 1.5,
            borderDash: [4, 4],
            pointRadius: 0
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: {
            grid: { color: '#1a2535' },
            ticks: { color: '#475569', font: { size: 11 } }
          },
          y: {
            grid: { color: '#1a2535' },
            ticks: { color: '#475569', font: { size: 11 } },
            beginAtZero: true
          }
        }
      }
    });
  }
  
  // ——————————————————————————————————————————
  // Gráfica donut — Pipeline kanban
  // ——————————————————————————————————————————
  function crearGraficaDonut() {
    var ctx = document.getElementById('chartDonut');
    if (!ctx) return;
  
    new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Ready', 'Enviados', 'Abiertos', 'Negociación', 'Vinculados'],
        datasets: [{
          data: [245, 180, 55, 42, 18],
          backgroundColor: ['#60a5fa', '#2dd4bf', '#f59e0b', '#a78bfa', '#34d399'],
          borderWidth: 0,
          hoverOffset: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '70%',
        plugins: { legend: { display: false } }
      }
    });
  }
  
  // ——————————————————————————————————————————
  // Gráfica de línea — Empresas vinculadas
  // ——————————————————————————————————————————
  function crearGraficaLinea() {
    var ctx = document.getElementById('chartLinea');
    if (!ctx) return;
  
    new Chart(ctx, {
      type: 'line',
      data: {
        labels: ['Semana 1', 'Semana 2', 'Semana 3', 'Semana 4', 'Semana 5', 'Semana 6'],
        datasets: [{
          label: 'Vinculadas',
          data: [2, 5, 9, 16, 24, 32],
          borderColor: '#2dd4bf',
          backgroundColor: 'rgba(45,212,191,0.08)',
          fill: true,
          tension: 0.4,
          borderWidth: 2,
          pointRadius: 3,
          pointBackgroundColor: '#2dd4bf'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: {
            grid: { color: '#1a2535' },
            ticks: { color: '#475569', font: { size: 11 } }
          },
          y: {
            grid: { color: '#1a2535' },
            ticks: { color: '#475569', font: { size: 11 } },
            beginAtZero: true
          }
        }
      }
    });
  }
  
  // ——————————————————————————————————————————
  // Acciones de los botones del dashboard
  // ——————————————————————————————————————————
  function exportarPDF() {
    alert('📄 Exportar PDF — se conectará con el backend en la próxima fase.');
  }
  
  function generarReporteIA() {
    var lista = document.getElementById('reporte-lista');
    if (!lista) return;
  
    // Mostrar estado de carga
    lista.innerHTML = '<p style="color:#475569;font-size:13px;padding:10px 0;">⏳ Generando análisis con IA...</p>';
  
    // Simular respuesta de la IA (luego conectar con backend)
    setTimeout(function() {
      lista.innerHTML = `
        <div class="reporte-item">
          <span class="reporte-item-ico">📊</span>
          <span>
            <strong style="color:#e2e8f0;">Tendencia positiva:</strong>
            Las empresas que usan React y Python tienen un 34% más de probabilidad de contratar talento junior.
          </span>
        </div>
        <div class="reporte-item">
          <span class="reporte-item-ico">🎯</span>
          <span>
            <strong style="color:#e2e8f0;">Recomendación:</strong>
            Priorizar startups del sector fintech — 3x más tasa de respuesta que empresas enterprise.
          </span>
        </div>
        <div class="reporte-item">
          <span class="reporte-item-ico">⚡</span>
          <span>
            <strong style="color:#e2e8f0;">Oportunidad:</strong>
            18 empresas en "Negociación" llevan más de 5 días sin seguimiento. Re-contacto recomendado.
          </span>
        </div>
      `;
    }, 1800);
  }