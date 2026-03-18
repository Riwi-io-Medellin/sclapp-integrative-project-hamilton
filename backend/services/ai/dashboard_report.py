"""
Dashboard AI report:
- Recolecta métricas reales desde PostgreSQL (stats + top technologies + top companies).
- Construye un contexto de negocio.
- Llama a OpenAI para redactar un reporte con JSON limpio.
- Si OpenAI falla o no hay API key, devuelve un fallback útil con datos reales.
"""

from __future__ import annotations

import json
import re
from typing import Any

from backend.core.config import get_settings
from backend.db.connection import execute_query


def collect_dashboard_stats() -> dict[str, int]:
    """KPIs reales: total_companies, scored_companies, high_score_companies, emails_sent."""

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


def collect_email_performance() -> dict[str, float | int]:
    """Métricas adicionales reales para el contexto: tasa de apertura estimada y engagement."""

    opened = execute_query("SELECT COUNT(*) AS opened FROM email_events WHERE event_type = 'open'")
    total_sent = execute_query("SELECT COUNT(*) AS total FROM emails WHERE send_status = 'sent'")
    companies_engaged = execute_query(
        "SELECT COUNT(*) AS count "
        "FROM company c "
        "JOIN statuses s ON s.id_status = c.id_status "
        "WHERE s.code IN ('negotiation', 'contacted')"
    )

    opened_val = int(opened[0]["opened"]) if opened else 0
    total_sent_val = int(total_sent[0]["total"]) if total_sent else 0
    engaged_val = int(companies_engaged[0]["count"]) if companies_engaged else 0
    open_rate_percent = round((opened_val / total_sent_val * 100) if total_sent_val else 0.0, 1)

    return {
        "opened_emails": opened_val,
        "open_rate_percent": open_rate_percent,
        "companies_engaged": engaged_val,
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
    # Nota: 'score' en DB es smallint (o None). Convertimos a int cuando aplica.
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


def build_dashboard_ai_report_prompt(context: dict[str, Any]) -> tuple[str, str]:
    """Construye system/user prompt para forzar JSON limpio y no inventar datos."""

    stats = context.get("stats") or {}
    perf = context.get("email_performance") or {}
    top_tech = context.get("top_technologies") or []
    top_companies = context.get("top_companies") or []

    context_block = {
        "stats": stats,
        "email_performance": perf,
        "top_technologies": top_tech,
        "top_companies": top_companies,
    }

    system = (
        "Eres un analista de mercado tech para SCLAPP (lead generation y scraping). "
        "Genera un reporte para el dashboard usando SOLO los datos provistos en el input. "
        "No inventes números, porcentajes, empresas o tecnologías que no estén en los datos. "
        "Responde SOLO con JSON (sin markdown) y con esta estructura exacta: "
        '{ "summary": string, "highlights": [string, string, ...], "recommendation": string }. '
        "Reglas: "
        "- 'highlights' debe tener entre 2 y 4 items. "
        "- resume hallazgos concretos apoyados en métricas (conteos, tasas, rankings). "
        "- 'recommendation' debe ser una recomendación accionable y específica, basada en los datos."
    )

    user = (
        "Genera el reporte usando este contexto JSON. "
        "Si hay listas vacías, adapta el texto sin inventar: \n"
        f"{json.dumps(context_block, ensure_ascii=False)}"
    )

    return system, user


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    # Quita fences típicas ```json ... ```
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

    # Asegura mínimo de 2 highlights para el card.
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
    """Fallback determinístico basado en datos reales (sin IA)."""
    stats = context.get("stats") or {}
    perf = context.get("email_performance") or {}
    top_tech = context.get("top_technologies") or []
    top_companies = context.get("top_companies") or []

    total_companies = int(stats.get("total_companies") or 0)
    scored_companies = int(stats.get("scored_companies") or 0)
    high_score_companies = int(stats.get("high_score_companies") or 0)
    emails_sent = int(stats.get("emails_sent") or 0)

    open_rate_percent = float(perf.get("open_rate_percent") or 0.0)
    opened_emails = int(perf.get("opened_emails") or 0)
    companies_engaged = int(perf.get("companies_engaged") or 0)

    top_tech_line = "Sin datos de tecnologías."
    if top_tech:
        t0 = top_tech[0]
        name_tech = t0.get("name_tech") or "—"
        companies_using = int(t0.get("companies_using") or 0)
        top_tech_line = f"Tecnología más usada: {name_tech} (en {companies_using} empresas)."

    top_company_lines: list[str] = []
    for c in (top_companies[:3] if top_companies else []):
        name = c.get("name") or "—"
        score = c.get("score")
        score_txt = f"score {score}" if score is not None else "sin score"
        top_company_lines.append(f"{name} ({score_txt}).")

    if not top_company_lines:
        top_company_lines = ["Sin datos de empresas con score."]

    summary = (
        f"Hoy hay {total_companies} empresas en la base; {scored_companies} tienen score y {high_score_companies} "
        f"alcanzan el score alto (3). Se enviaron {emails_sent} correos; tasa de apertura estimada: {open_rate_percent}% "
        f"({opened_emails}/{emails_sent} abiertos)."
    )

    highlights: list[str] = []
    highlights.append(top_tech_line)
    highlights.append(
        f"Empresas en etapa de conversación/negociación: {companies_engaged}."
    )
    # Agrega 1-2 líneas de top empresas para que el card sea más "accionable".
    highlights.append(top_company_lines[0])
    if len(top_company_lines) > 1:
        highlights.append(top_company_lines[1])

    # Mantén 2-4
    highlights = highlights[:4]

    recommendation = (
        "Recomendación: prioriza outreach a empresas con score alto (3) y enfoca tu mensajería en la tecnología "
        f"{top_tech[0].get('name_tech') if top_tech else 'principal'} para aumentar relevancia. "
        "Luego, usa las primeras 3 empresas con mejor score como cuentas objetivo para pruebas de contacto."
    )

    return {
        "summary": summary,
        "highlights": highlights if len(highlights) >= 2 else ["Resumen disponible.", "Recomendación disponible."],
        "recommendation": recommendation,
    }


def _extract_openai_content(response: Any) -> str:
    """Extrae content de una respuesta de OpenAI (compatible con distintas estructuras)."""
    if not response:
        return ""
    try:
        if getattr(response, "choices", None):
            msg = response.choices[0].message
            raw_content = getattr(msg, "content", None)
            if isinstance(raw_content, str):
                return raw_content.strip()
            # A veces el SDK devuelve content_parts (ej. multimodal, etc.)
            if hasattr(msg, "content_parts") and msg.content_parts:
                for p in msg.content_parts:
                    if isinstance(p, dict) and p.get("type") == "text":
                        return (p.get("text") or "").strip()
                    if getattr(p, "type", None) == "text":
                        return (getattr(p, "text", None) or "").strip()
            # Fallback: intenta convertir el objeto a str si trae payload
            return str(raw_content or "").strip()
    except Exception:
        return ""
    return ""


def generate_dashboard_ai_report() -> dict[str, Any]:
    """
    Genera el reporte AI (contrato del endpoint):
    {
      "summary": str,
      "highlights": [str, str, ...],
      "recommendation": str
    }
    """
    # 1) Datos reales de negocio
    context: dict[str, Any] = {
        "stats": {},
        "email_performance": {},
        "top_technologies": [],
        "top_companies": [],
    }

    try:
        context["stats"] = collect_dashboard_stats()
    except Exception as e:
        # Si la DB falla, fallback con texto general (sin romper).
        context["stats"] = {
            "total_companies": 0,
            "scored_companies": 0,
            "high_score_companies": 0,
            "emails_sent": 0,
        }
        print("[AI REPORT] Error collect_dashboard_stats:", type(e).__name__, str(e)[:200])

    try:
        context["email_performance"] = collect_email_performance()
    except Exception as e:
        context["email_performance"] = {"opened_emails": 0, "open_rate_percent": 0.0, "companies_engaged": 0}
        print("[AI REPORT] Error collect_email_performance:", type(e).__name__, str(e)[:200])

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

    # 2) Prompt + fallback
    fallback = build_dashboard_ai_report_fallback(context)

    settings = get_settings()
    api_key = settings.get("openai_api_key")
    model = settings.get("openai_model") or "gpt-4o-mini"

    if not api_key or not str(api_key).strip():
        return fallback

    system, user = build_dashboard_ai_report_prompt(context)

    # 3) Llamada a OpenAI con parsing robusto
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
            max_completion_tokens=500,
        )

        content = _extract_openai_content(response)
        if not content:
            return fallback

        content = _strip_code_fences(content)
        data = json.loads(content)
        return _coerce_report_payload(data, fallback)
    except Exception as e:
        print("[AI REPORT] OpenAI failed:", type(e).__name__, str(e)[:200])
        return fallback

