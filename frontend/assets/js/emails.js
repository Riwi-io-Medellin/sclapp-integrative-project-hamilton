// Emails / Outreach view: Kanban with 5 columns. Data from getEmailPipeline() -> GET /emails/pipeline.

import { apiClient } from './apiClient.js';

const FALLBACK_COLUMNS = [
  {
    id: 'ready',
    icono: '☰',
    nombre: 'Ready',
    color: '#94a3b8',
    tarjetas: [
      { empresa: 'TechCorp Solutions', desc: 'Junior React talent proposal', prioridad: 'Alta', tiempo: '2h ago' },
      { empresa: 'AppWorks Studio', desc: 'Angular developers available', prioridad: 'Media', tiempo: '4h ago' },
      { empresa: 'ByteForge', desc: 'Node.js talent for project', prioridad: 'Media', tiempo: '5h ago' },
    ],
  },
  {
    id: 'enviados',
    icono: '✈',
    nombre: 'Sent',
    color: '#2dd4bf',
    tarjetas: [
      { empresa: 'InnovateTech', desc: 'Tech collaboration proposal', prioridad: 'Alta', tiempo: '1d ago' },
      { empresa: 'CloudNine Labs', desc: 'Junior Vue.js talent', prioridad: 'Media', tiempo: '2d ago' },
    ],
  },
  {
    id: 'abiertos',
    icono: '👁',
    nombre: 'Opened',
    color: '#f59e0b',
    tarjetas: [
      { empresa: 'DevFactory', desc: 'Python developers available', prioridad: 'Alta', tiempo: '3d ago' },
      { empresa: 'StartupXYZ', desc: 'React team for Q1 project', prioridad: 'Alta', tiempo: '4d ago' },
    ],
  },
  {
    id: 'negociacion',
    icono: '💬',
    nombre: 'Negotiation',
    color: '#a78bfa',
    tarjetas: [
      { empresa: 'DataDriven Co', desc: 'Tech services agreement', prioridad: 'Alta', tiempo: '1w ago' },
    ],
  },
  {
    id: 'vinculados',
    icono: '🛡',
    nombre: 'Engaged',
    color: '#34d399',
    tarjetas: [
      { empresa: 'DevFactory', desc: 'Contract signed — 3 juniors', prioridad: 'Alta', tiempo: '2w ago' },
    ],
  },
];

function buildColumnHtml(col) {
  let cardsHtml = '';
  if (col.tarjetas.length === 0) {
    cardsHtml = '<div class="kanban-vacio">No companies in this stage</div>';
  } else {
    cardsHtml = col.tarjetas
      .map((t) => {
        const badgeClass = t.prioridad === 'Alta' ? 'badge-alta' : 'badge-media';
        return `
          <div class="kanban-tarjeta">
            <div class="kanban-tarjeta-top">
              <div class="kanban-empresa-info">
                <div class="kanban-empresa-ico">🏢</div>
                <span class="kanban-empresa-nombre">${t.empresa}</span>
              </div>
              <button class="kanban-kebab">⋮</button>
            </div>
            <p class="kanban-tarjeta-desc">${t.desc}</p>
            <div class="kanban-tarjeta-footer">
              <span class="badge ${badgeClass}">${t.prioridad}</span>
              <span class="kanban-tiempo">🕐 ${t.tiempo}</span>
            </div>
          </div>
        `;
      })
      .join('');
  }
  return `
    <div class="kanban-col">
      <div class="kanban-col-header">
        <span class="col-icono" style="color:${col.color};">${col.icono}</span>
        <span class="col-nombre" style="color:${col.color};">${col.nombre}</span>
        <span class="col-badge">${col.tarjetas.length}</span>
      </div>
      <div class="kanban-col-body">${cardsHtml}</div>
    </div>
  `;
}

export function renderEmailsView(main) {
  let columnsData = [...FALLBACK_COLUMNS];

  async function loadPipeline() {
    try {
      const data = await apiClient.getEmailPipeline();
      if (data && Array.isArray(data.columns)) {
        columnsData = data.columns;
      }
    } catch (_) {}
    const columnsHtml = columnsData.map(buildColumnHtml).join('');

    main.innerHTML = `
      <div class="view-container">
        <div class="view-header">
          <div>
            <h2 class="view-title">Emails — Outreach</h2>
            <p class="view-subtitle">Manage your contact pipeline with companies</p>
          </div>
          <div class="view-header-botones">
            <button class="btn-secundario" id="btnOpenAiPanel">✦ Generate AI template</button>
            <button class="btn-primario" id="btnBulkSend">✈ Bulk send</button>
          </div>
        </div>
        <div class="kanban-board">${columnsHtml}</div>
      </div>

      <div class="panel-overlay" id="panelIA" style="display:none;">
        <div class="panel">
          <div class="panel-header">
            <h3>✦ AI template generator</h3>
            <button class="modal-cerrar" id="btnClosePanel">✕</button>
          </div>
          <div class="panel-body">
            <div class="form-group">
              <label style="font-size:13px;color:#64748b;display:block;margin-bottom:7px;">Email subject</label>
              <input type="text" class="filtro-input" style="width:100%;" placeholder="e.g. Tech collaboration opportunity" id="asuntoPlantilla" />
            </div>
            <div class="form-group" style="margin-top:14px;">
              <label style="font-size:13px;color:#64748b;display:block;margin-bottom:7px;">Message</label>
              <textarea class="email-textarea" id="cuerpoPlantilla" placeholder="Describe the context and the AI will generate the email..."></textarea>
            </div>
            <button class="btn-ia" id="btnGenerateAi">🤖 Generate with AI</button>
          </div>
          <div class="panel-footer">
            <button class="btn-cancelar" id="btnCancelPanel">Cancel</button>
            <button class="btn-primario" id="btnSaveTemplate">Save template</button>
          </div>
        </div>
      </div>
    `;

    document.getElementById('btnOpenAiPanel')?.addEventListener('click', () => {
      document.getElementById('panelIA').style.display = 'flex';
    });

    document.getElementById('btnClosePanel')?.addEventListener('click', () => {
      document.getElementById('panelIA').style.display = 'none';
    });

    document.getElementById('btnCancelPanel')?.addEventListener('click', () => {
      document.getElementById('panelIA').style.display = 'none';
    });

    document.getElementById('btnSaveTemplate')?.addEventListener('click', () => {
      window.alert('Template saved. (Will be connected to backend.)');
      document.getElementById('panelIA').style.display = 'none';
    });

    document.getElementById('btnGenerateAi')?.addEventListener('click', async () => {
      const bodyEl = document.getElementById('cuerpoPlantilla');
      if (!bodyEl) return;
      const subject = document.getElementById('asuntoPlantilla')?.value || '';
      const context = bodyEl.value;
      bodyEl.value = 'Generating with AI...';
      try {
        const result = await apiClient.generateEmailTemplate({ subject, context });
        if (result && result.body) {
          bodyEl.value = result.body;
        } else {
          bodyEl.value =
            'Hello {{company_name}},\n\nWe have identified that your company is looking for junior tech talent, and at SCLAPP we connect exactly that profile with companies like yours.\n\nCould we schedule a 15-minute call this week?\n\nBest regards,\n{{your_name}} — SCLAPP';
        }
      } catch (_) {
        bodyEl.value =
          'Hello {{company_name}},\n\nWe have identified that your company is looking for junior tech talent, and at SCLAPP we connect exactly that profile with companies like yours.\n\nCould we schedule a 15-minute call this week?\n\nBest regards,\n{{your_name}} — SCLAPP';
      }
    });

    document.getElementById('btnBulkSend')?.addEventListener('click', () => {
      window.alert('Bulk send — will be connected to the backend to send emails in batch.');
    });
  }

  loadPipeline();
}
