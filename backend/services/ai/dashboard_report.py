"""
Dashboard AI report (market intelligence para Riwi):
- Recolecta métricas reales desde PostgreSQL (empresas, tecnologías, scores).
- Construye contexto sin narrativa de correos / pipeline comercial.
- Llama a OpenAI para un reporte ejecutivo en JSON fijo.
- Si OpenAI falla o no hay API key, devuelve fallback alineado con el mismo enfoque.
"""

from __future__ import annotations

import json
import re
from typing import Any

from backend.core.config import get_settings
from backend.db.connection import execute_query


def collect_dashboard_stats() -> dict[str, int]:
    """KPIs reales para contexto del reporte (incluye emails_sent solo por compatibilidad interna; no se envía al LLM)."""

    total = execute_query("SELECT COUNT(*) AS c FROM company")
    scored = execute_query("SELECT COUNT(*) AS c FROM company WHERE score IS NOT NULL")
    high = execute_query("SELECT COUNT(*) AS c FROM company WHERE score = 3")
    emails = execute_query("SELECT COUNT(*) AS c FROM emails WHERE send_status = 'sent'")

    def n(q: Any, default: int = 0) -> int:
        return int(q[0]["c"]) if q and len(q) > 0 else default

    return {
        "total_companies": n(total),
        "scored_companies": n(scored),
        "high_score_companies": n(high),
        "emails_sent": n(emails),
    }


def collect_score_distribution() -> dict[str, int]:
    """Distribución global de empresas con score (1/2/3); ignora score NULL."""
    row = execute_query(
        """
        SELECT
          SUM(CASE WHEN score = 3 THEN 1 ELSE 0 END) AS high,
          SUM(CASE WHEN score = 2 THEN 1 ELSE 0 END) AS medium,
          SUM(CASE WHEN score = 1 THEN 1 ELSE 0 END) AS low,
          SUM(CASE WHEN score IS NOT NULL THEN 1 ELSE 0 END) AS total_scored
        FROM company
        """
    )
    if not row:
        return {"high": 0, "medium": 0, "low": 0, "total_scored": 0}
    r = row[0]
    return {
        "high": int(r.get("high") or 0),
        "medium": int(r.get("medium") or 0),
        "low": int(r.get("low") or 0),
        "total_scored": int(r.get("total_scored") or 0),
    }


def collect_top_technologies(limit: int = 10) -> list[dict[str, int | str]]:
    """Top N tecnologías por número de empresas que las usan."""
    rows = execute_query(
        """
        SELECT t.name_tech, COUNT(ct.id_company) AS companies_using
        FROM technologies t
        JOIN company_technologies ct ON ct.id_tech = t.id_tech
        GROUP BY t.id_tech, t.name_tech
        ORDER BY companies_using DESC
        LIMIT %s
        """,
        (limit,),
    )
    if not rows:
        return []
    return [
        {"name_tech": r["name_tech"], "companies_using": int(r["companies_using"])}
        for r in rows
    ]


def collect_top_companies(limit: int = 10) -> list[dict[str, int | str | None]]:
    """Top N empresas por score DESC, luego created_at DESC."""
    rows = execute_query(
        """
        SELECT id_company, name, category, score, country
        FROM company
        WHERE score IS NOT NULL
        ORDER BY score DESC, created_at DESC
        LIMIT %s
        """,
        (limit,),
    )
    if not rows:
        return []

    def map_row(r: dict[str, Any]) -> dict[str, int | str | None]:
        score = r.get("score")
        return {
            "id_company": r.get("id_company"),
            "name": r.get("name"),
            "category": r.get("category"),
            "score": int(score) if score is not None else None,
            "country": r.get("country"),
        }

    return [map_row(dict(r)) for r in rows]


def _market_context_for_prompt(context: dict[str, Any]) -> dict[str, Any]:
    """Solo datos permitidos para el LLM (sin correos ni métricas comerciales fuera de scope)."""
    stats = context.get("stats") or {}
    return {
        "market_overview": {
            "total_companies_analyzed": int(stats.get("total_companies") or 0),
            "companies_with_score": int(stats.get("scored_companies") or 0),
            "companies_high_score_3": int(stats.get("high_score_companies") or 0),
        },
        "score_distribution": context.get("score_distribution") or {},
        "top_technologies_by_company_demand": context.get("top_technologies") or [],
        "top_companies_by_score": context.get("top_companies") or [],
        "note": (
            "Score numérico en datos: 3 = mayor afinidad/prioridad respecto al perfil que Riwi impulsa, "
            "2 = media, 1 = menor en este conjunto. No infirir causas no soportadas por los números."
        ),
    }


def build_dashboard_ai_report_prompt(context: dict[str, Any]) -> tuple[str, str]:
    """System y user: enfoque decisión para Riwi (formación, empleabilidad, alineación con empresas)."""

    json_metrics = json.dumps(_market_context_for_prompt(context), ensure_ascii=False)

    system = (
        "Eres un analista de inteligencia de mercado enfocado en decisiones estratégicas para Riwi.\n\n"
        "Contexto institucional:\n"
        "- Riwi es una aceleradora de talento en Colombia que forma desarrolladores junior mediante becas intensivas.\n"
        "- Su modelo combina formación técnica, inglés y habilidades socioemocionales para empleabilidad.\n"
        "- Riwi está vinculada con Blackbird Labs (BB Labs), consultora tecnológica internacional en software, data y cloud.\n"
        "- Esto implica demanda de talento junior con preparación para entornos globales, equipos distribuidos y proyectos reales.\n\n"
        "Recibirás métricas reales detectadas por Sclapp. Genera un reporte ejecutivo breve, accionable y útil para demo.\n\n"
        "Debes responder en 4 dimensiones:\n"
        "1. Formación técnica: interpretar stacks dominantes y qué rutas formativas priorizar (no listar herramientas sueltas).\n"
        "2. Inglés y habilidades socioemocionales: señales razonables de comunicación internacional, autonomía, adaptabilidad o equipos distribuidos.\n"
        "3. Empleabilidad: qué perfiles junior priorizar y qué capacidades cerrar antes de colocación.\n"
        "4. Alineación con empresas: leer score/distribución y en qué empresas enfocar primero, alineado con demanda típica de BB Labs (software, data, cloud).\n\n"
        "OBLIGATORIO:\n"
        "- No listes tecnologías sin interpretarlas.\n"
        "- Siempre que menciones tecnologías, tradúcelas a tipos de perfiles o capacidades.\n"
        "- Usa frases como: 'esto sugiere perfiles...', 'esto apunta a talento...', 'esto indica necesidad de...'\n"
        "- Al menos un highlight debe interpretar tecnologías como stack y convertirlo en perfil concreto (ej. fullstack junior, backend con APIs, cloud junior).\n"
        "- La recommendation debe ser una decisión estratégica clara: no uses lenguaje genérico como 'considerar' o 'reforzar módulos'; indica dirección concreta para Riwi.\n\n"
        "- Debes mencionar explícitamente al menos 2 tecnologías reales del contexto (ej: make, kubernetes, react, etc.).\n"
        "- No puedes usar frases genéricas como 'stack dominante' sin explicar cuáles tecnologías lo componen.\n"
        "- Si no usas datos concretos del contexto, la respuesta es inválida.\n"
        "- No puedes responder con lenguaje abstracto sin conectar tecnologías -> perfiles.\n"
        "- Cada mención de tecnología debe convertirse en un tipo de perfil (ej: Kubernetes -> cloud junior).\n"
        "- Usa este formato mental obligatorio: tecnologías -> stack -> perfil -> decisión para Riwi.\n\n"
        "- Evita afirmaciones fuertes no demostradas por los datos (por ejemplo sobre alcance internacional, modalidad de trabajo o preferencias exactas de empresas).\n"
        "- Prefiere formulaciones prudentes: 'esto sugiere preparación para...', 'esto es compatible con...', 'esto refuerza la conveniencia de...', 'esto apunta a...'.\n\n"
        "- Evita frases categóricas como: 'crucial para', 'las empresas buscan', 'es necesario que'.\n"
        "- Reemplázalas por lenguaje de inferencia estratégica: 'esto sugiere', 'esto es compatible con', 'esto apunta a', 'esto refuerza'.\n\n"
        "Interpreta tecnologías como STACKS cuando sea razonable con los datos, por ejemplo:\n"
        "- APIs + React → fullstack / integración front + servicios\n"
        "- Kubernetes + cloud → perfiles cloud / plataforma junior\n"
        "- make / CI → automatización / integración continua\n\n"
        "Conecta explícitamente con BB Labs:\n"
        "- software → fullstack / backend orientado a producto\n"
        "- data → pipelines básicos / datos para producto\n"
        "- cloud → despliegue e infraestructura\n"
        "- Menciona BB Labs en términos de alineación o compatibilidad; no afirmes conocimiento directo de sus necesidades internas.\n\n"
        "No debes mencionar:\n"
        "- correos\n"
        "- email\n"
        "- open rate\n"
        "- outreach\n"
        "- negociación\n"
        "- pipeline\n"
        "- engagement\n\n"
        "No inventes datos ni porcentajes no presentes en el contexto.\n"
        "Puedes hacer inferencias suaves, pero deben estar claramente apoyadas por los datos.\n\n"
        "Responde únicamente en JSON válido con esta estructura exacta:\n\n"
        '{\n  "summary": "",\n  "highlights": [],\n  "recommendation": ""\n}\n\n'
        "Reglas adicionales:\n"
        "- 'highlights' debe tener entre 2 y 4 strings.\n"
        "- 'summary' debe:\n"
        "  * mencionar explícitamente tecnologías reales del contexto\n"
        "  * interpretarlas como stack (no lista)\n"
        "  * explicar qué tipo de perfiles sugiere ese stack\n"
        "  * conectar esa lectura con decisiones para Riwi\n"
        "- En highlights, al menos uno debe conectar la señal de mercado con líneas de demanda de BB Labs (software, data, cloud).\n"
        "- Evita causalidades fuertes; usa lenguaje de señal, tendencia o prioridad.\n"
        "- 'recommendation' debe conectar formación + empleabilidad + mercado + BB Labs en una sola dirección ejecutable, sin lenguaje comercial.\n"
        "- En recommendation, prioriza explícitamente empresas score 3 y score 2: score 3 como validación fuerte de afinidad y score 2 como universo amplio de oportunidad.\n\n"
        "Evita lenguaje débil vago: 'considerar' sin decisión, 'podría' sin dirección, recomendaciones sin verbo de acción.\n"
        "Sí puedes usar 'esto sugiere perfiles...' siempre que cierre con perfil o acción concreta.\n"
        "Prefiere: priorizar, orientar, enfocar, ejecutar, decidir.\n\n"
        "El tono debe ser ejecutivo, claro, convincente, útil para demo y orientado a toma de decisiones."
    )

    user = (
        "EJEMPLO DE RESPUESTA ESPERADA\n\n"
        "{\n"
        '  "summary": "El mercado analizado sugiere un stack dominante orientado a integración de servicios y despliegue en entornos cloud, con señales de demanda en interfaces modernas. La distribución de score indica dónde enfocar la validación de empleabilidad sin asumir causalidad fuerte.",\n'
        '  "highlights": [\n'
        '    "Esto sugiere perfiles fullstack junior con capacidad de integrar APIs y construir interfaces modernas, en lugar de especialización aislada en frontend o backend.",\n'
        '    "La presencia de tecnologías asociadas a despliegue y orquestación apunta a talento cloud junior con fundamentos en infraestructura y entornos reproducibles, alineado con BB Labs.",\n'
        '    "Esto indica necesidad de perfiles con habilidades prácticas en integración de servicios y automatización, más que conocimiento teórico de herramientas individuales.",\n'
        '    "La señal de mercado es compatible con líneas de software, data y cloud de BB Labs, lo que sugiere preparar talento adaptable a entornos internacionales."\n'
        "  ],\n"
        '  "recommendation": "Decidir: orientar la formación hacia perfiles fullstack junior con integración de APIs y fundamentos cloud, incorporando proyectos reales desplegables. En empleabilidad, priorizar colocación en empresas con score 3 y 2 para validar ajuste con demanda real y retroalimentar el modelo formativo."\n'
        "}\n\n"
        "Tu respuesta debe usar datos reales del contexto, no generalidades.\n"
        "Tu respuesta debe parecerse a este nivel de interpretación, no a una lista de tecnologías.\n\n"
        "Regla crítica:\n"
        "Si tu respuesta no menciona tecnologías específicas del contexto (como make, kubernetes, react, etc.), está incorrecta.\n\n"
        f"Contexto:\n{json_metrics}"
    )

    return system, user


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```[a-zA-Z0-9_]*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


def _coerce_report_payload(payload: Any, fallback: dict[str, Any]) -> dict[str, Any]:
    """Normaliza la respuesta al contrato del frontend (sin romper la UI)."""
    if not isinstance(payload, dict):
        return fallback

    summary = str(payload.get("summary") or "").strip()
    recommendation = str(payload.get("recommendation") or "").strip()
    highlights_raw = payload.get("highlights")

    highlights: list[str] = []
    if isinstance(highlights_raw, list):
        for h in highlights_raw:
            if h is None:
                continue
            hs = str(h).strip()
            if hs:
                highlights.append(hs)

    if len(highlights) < 2:
        for h in fallback.get("highlights", []):
            if h not in highlights:
                highlights.append(str(h))
            if len(highlights) >= 2:
                break

    if not summary:
        summary = str(fallback.get("summary") or "")
    if not recommendation:
        recommendation = str(fallback.get("recommendation") or "")

    highlights = highlights[:4]

    return {
        "summary": summary,
        "highlights": highlights,
        "recommendation": recommendation,
    }


def build_dashboard_ai_report_fallback(context: dict[str, Any]) -> dict[str, Any]:
    """Fallback determinístico: market intelligence para Riwi (formación, empleabilidad, empresas). Sin correos."""
    stats = context.get("stats") or {}
    dist = context.get("score_distribution") or {}
    top_tech = context.get("top_technologies") or []
    top_companies = context.get("top_companies") or []

    total = int(stats.get("total_companies") or 0)
    scored = int(stats.get("scored_companies") or 0)
    high3 = int(stats.get("high_score_companies") or 0)
    d_high = int(dist.get("high") or 0)
    d_med = int(dist.get("medium") or 0)
    d_low = int(dist.get("low") or 0)
    total_scored = int(dist.get("total_scored") or scored)

    tech_names = [str(t.get("name_tech") or "") for t in top_tech[:5] if t.get("name_tech")]
    tech_line = (
        f"Tecnologías con mayor presencia en el muestreo: {', '.join(tech_names)}."
        if tech_names
        else "Aún no hay ranking de tecnologías suficiente para priorizar rutas formativas."
    )

    score_read = (
        f"De {total_scored} empresas con score, {d_high} están en nivel alto (3), {d_med} en medio (2) y {d_low} en bajo (1)."
        if total_scored
        else "No hay empresas con score asignado para interpretar afinidad en este momento."
    )

    top_names = [f"{c.get('name')} (score {c.get('score')})" for c in top_companies[:3] if c.get("name")]
    companies_line = (
        f"Ejemplos de empresas mejor posicionadas por score: {', '.join(top_names)}."
        if top_names
        else "Sin empresas con score suficientes para citar casos concretos."
    )

    summary = (
        f"Sclapp detectó {total} empresas analizadas, de las cuales {scored} tienen score asignado; "
        f"{high3} alcanzan score alto (3). {tech_line} "
        f"{score_read} Señal para Riwi: usar tecnologías repetidas como guía de demanda y el score como priorización relativa dentro de este universo."
    )

    highlights: list[str] = []

    if tech_names:
        highlights.append(
            f"Formación: orientar rutas hacia perfiles junior alineados con el stack que concentran {', '.join(tech_names[:3])}, "
            "porque concentran la mayor demanda observada entre empresas."
        )
    else:
        highlights.append(
            "Formación: cuando existan datos de tecnologías, priorizar rutas que cubran las stacks más frecuentes en el ranking."
        )

    if total_scored:
        highlights.append(
            f"Empleabilidad: con la distribución actual (alto {d_high}, medio {d_med}, bajo {d_low}), "
            "tiene sentido priorizar talento cuyas competencias coincidan con empresas en score alto y medio antes que en bajo, dentro de este conjunto."
        )
    else:
        highlights.append(
            "Empleabilidad: al completar scoring de empresas, priorizar perfiles cuyas competencias coincidan con las empresas en mejor score."
        )

    highlights.append(
        "Inglés y socioemocionales: la presencia de empresas de alcance internacional y stacks modernos sugiere "
        "reforzar comunicación técnica en inglés, trabajo colaborativo en equipos distribuidos y autonomía para resolver tareas en contexto real."
    )

    highlights.append(
        f"Alineación con empresas: {companies_line} "
        "El score es una señal de afinidad relativa respecto al universo capturado; BB Labs puede usarse como referente de demanda en software, data y cloud."
    )

    highlights = highlights[:4]

    tech_focus = tech_names[0] if tech_names else "las tecnologías dominantes del ranking"
    recommendation = (
        f"Recomendación para Riwi: alinear el plan formativo y los workshops con {tech_focus}, "
        "integrando objetivos explícitos de inglés técnico y habilidades socioemocionales (comunicación, adaptabilidad y autonomía). "
        "En empleabilidad, priorizar perfiles junior con evidencia práctica en esas tecnologías para empresas con score 3 y 2. "
        "En relacionamiento, comenzar por empresas de mayor score y validar afinidad con necesidades de software/data/cloud donde BB Labs opera como referencia estratégica."
    )

    return {
        "summary": summary.strip(),
        "highlights": highlights if len(highlights) >= 2 else [
            "Usa el ranking de tecnologías para decidir refuerzos formativos.",
            "Usa la distribución por score para ordenar qué empresas y perfiles conviene priorizar.",
        ],
        "recommendation": recommendation.strip(),
    }


def _extract_openai_content(response: Any) -> str:
    if not response:
        return ""
    try:
        if getattr(response, "choices", None):
            msg = response.choices[0].message
            raw_content = getattr(msg, "content", None)
            if isinstance(raw_content, str):
                return raw_content.strip()
            if hasattr(msg, "content_parts") and msg.content_parts:
                for p in msg.content_parts:
                    if isinstance(p, dict) and p.get("type") == "text":
                        return (p.get("text") or "").strip()
                    if getattr(p, "type", None) == "text":
                        return (getattr(p, "text", None) or "").strip()
            return str(raw_content or "").strip()
    except Exception:
        return ""
    return ""


def generate_dashboard_ai_report() -> dict[str, Any]:
    """
    Contrato del endpoint:
    { "summary": str, "highlights": [str, ...], "recommendation": str }
    """
    context: dict[str, Any] = {
        "stats": {},
        "score_distribution": {},
        "top_technologies": [],
        "top_companies": [],
    }

    try:
        context["stats"] = collect_dashboard_stats()
    except Exception as e:
        context["stats"] = {
            "total_companies": 0,
            "scored_companies": 0,
            "high_score_companies": 0,
            "emails_sent": 0,
        }
        print("[AI REPORT] Error collect_dashboard_stats:", type(e).__name__, str(e)[:200])

    try:
        context["score_distribution"] = collect_score_distribution()
    except Exception as e:
        context["score_distribution"] = {"high": 0, "medium": 0, "low": 0, "total_scored": 0}
        print("[AI REPORT] Error collect_score_distribution:", type(e).__name__, str(e)[:200])

    try:
        context["top_technologies"] = collect_top_technologies(limit=10)
    except Exception as e:
        context["top_technologies"] = []
        print("[AI REPORT] Error collect_top_technologies:", type(e).__name__, str(e)[:200])

    try:
        context["top_companies"] = collect_top_companies(limit=10)
    except Exception as e:
        context["top_companies"] = []
        print("[AI REPORT] Error collect_top_companies:", type(e).__name__, str(e)[:200])

    fallback = build_dashboard_ai_report_fallback(context)

    settings = get_settings()
    api_key = settings.get("openai_api_key")
    model = settings.get("openai_model") or "gpt-4o-mini"
    print("[AI REPORT] model from settings:", model)
    print("[AI REPORT] api key present:", bool(api_key and str(api_key).strip()))
    print("[AI REPORT] api key prefix:", str(api_key)[:8] if api_key else None)

    if not api_key or not str(api_key).strip():
        print("[AI REPORT] fallback due to missing OPENAI_API_KEY")
        return fallback

    system, user = build_dashboard_ai_report_prompt(context)

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.4,
            max_completion_tokens=550,
        )

        content = _extract_openai_content(response)
        print("[AI REPORT] raw model content:", content[:500] if content else "(empty)")
        if not content:
            print("[AI REPORT] fallback due to empty model content")
            return fallback

        content = _strip_code_fences(content)
        data = json.loads(content)
        print("[AI REPORT] parsed JSON successfully")
        return _coerce_report_payload(data, fallback)
    except Exception as e:
        print("[AI REPORT] OpenAI failed:", type(e).__name__, str(e)[:200])
        return fallback
