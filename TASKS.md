# 🚀 PLAN EJECUCIÓN SCLAPP — DASHBOARD IMPACTO (1 DÍA)

## 🎯 OBJETIVO

Convertir el dashboard actual en un **producto tipo BI con AI**, listo para demo final.

### Nivel 1 (OBLIGATORIO)

* KPIs reales funcionando
* 2 gráficas reales
* Reporte AI dinámico
* Dashboard estable y visualmente sólido

### Nivel 2 (SI ALCANZA)

* Copiar reporte
* Refresh dashboard
* Filtro simple (top 5 / 10)

### Nivel 3 (SOLO SI SOBRA TIEMPO)

* Pipeline de correos (demo)

---

# 🧠 ESTRATEGIA

Trabajar en paralelo por verticales:

## 🔵 STREAM A — LÍDER (AI + INTEGRACIÓN)

Responsable: Tú

### Tareas

1. Definir contratos de datos
2. Implementar `/dashboard/ai-report`
3. Integrar OpenAI
4. Crear fallback seguro
5. Conectar botón "Generar Reporte IA"
6. QA final

---

## 🟢 STREAM B — DASHBOARD VISUAL

Responsable: Compañero

### Tareas

1. Conectar KPIs reales
2. Implementar gráfica Top tecnologías
3. Implementar gráfica Top empresas
4. Estados UI (loading/error)
5. Refresh dashboard

---

# 🔌 CONTRATOS DE API

## GET /dashboard/stats

```json
{
  "total_companies": 42,
  "emails_sent": 17,
  "scored_companies": 29,
  "high_score_companies": 11
}
```

## GET /companies/technologies/trending

```json
[
  { "name_tech": "React", "companies_using": 18 }
]
```

## GET /companies/top

```json
[
  { "name": "Globant", "score": 95 }
]
```

## GET /dashboard/ai-report

```json
{
  "summary": "",
  "highlights": [],
  "recommendation": ""
}
```

---

# 🖥️ DASHBOARD FINAL

## Estructura

### Fila 1

KPIs

### Fila 2

* Gráfica Top tecnologías
* Gráfica Top empresas

### Fila 3

Reporte AI

---

# 🧩 CAMBIOS EN dashboard.js

## Reemplazar:

* Listas → Gráficas
* Mock IA → Fetch real

## Agregar:

* Loading states
* Error handling
* Destroy charts previos

---

# 🤖 PROMPTS CURSOR

## 🔵 AI REPORT BACKEND

```text
Necesito implementar un endpoint GET /dashboard/ai-report en FastAPI.

Debe:
1. Consultar métricas reales (stats, technologies, companies)
2. Construir contexto
3. Llamar OpenAI
4. Devolver JSON:
{
  summary,
  highlights,
  recommendation
}

Requisitos:
- Fallback si falla IA
- Código modular
- No romper frontend
```

---

## 🔵 PROMPT MODELO

```text
Eres un analista de mercado tech.

Genera:
- summary
- highlights (2-4)
- recommendation

No inventes datos.
Responde SOLO JSON.
```

---

## 🟢 DASHBOARD FRONTEND

```text
Tengo un dashboard en JS vanilla.

Quiero:
- Mantener KPIs
- Reemplazar listas por 2 gráficas con Chart.js
- Conectar endpoints reales
- Manejar loading/error
- Evitar memory leaks

Genera dashboard.js refactorizado.
```

---

## 🔵 INTEGRACIÓN AI FRONTEND

```text
Tengo endpoint /dashboard/ai-report.

Necesito:
- Botón "Generar reporte"
- Loading
- Render card elegante
- Manejo de error

JS vanilla.
```

---

# ⚡ PLAN POR HORAS

## Bloque 1 (0-3h)

* Definir contratos
* Backend listo

## Bloque 2 (3-6h)

* Gráficas funcionando
* UI lista

## Bloque 3 (6-9h)

* AI funcionando
* Integración completa

## Bloque 4

* Pulido demo
* Testing

---

# 🚫 NO HACER

* Scrapear nuevas fuentes
* Features incompletas
* Refactor grande

---

# 🎤 NARRATIVA DEMO

"Sclapp transforma datos del mercado laboral en insights accionables con AI."

Mostrar:

1. Tendencias
2. Empresas
3. Reporte AI

---

# 🏁 RESULTADO FINAL

✔ Dashboard real
✔ AI funcional
✔ Visual profesional
✔ Demo estable

---

💥 Esto los pone en nivel ganador.


---------




Prompt para el contenido del modelo

Eres un analista de mercado laboral tecnológico.

Vas a recibir métricas reales obtenidas de una plataforma llamada Sclapp. Debes generar un reporte ejecutivo breve para un dashboard de demo.

Tu respuesta debe:
- basarse solo en el contexto dado
- sonar profesional y convincente
- ser concreta
- no inventar porcentajes ni comparaciones no soportadas
- resaltar tecnologías dominantes, empresas con mejor score y una recomendación accionable

Debes responder únicamente en JSON válido con esta estructura exacta:
{
  "summary": "",
  "highlights": [],
  "recommendation": ""
}

Contexto:
{{JSON_METRICS}}