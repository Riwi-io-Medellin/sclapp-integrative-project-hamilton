"""Email pipeline, AI template, and bulk send."""

from fastapi import APIRouter
from pydantic import BaseModel

from backend.db.connection import execute_query

router = APIRouter(prefix="/emails", tags=["emails"])


@router.get("/pipeline")
def get_email_pipeline():
    """Return kanban columns with cards (mapped from DB statuses/emails)."""
    # Placeholder: return structure expected by frontend (columns with tarjetas)
    rows = execute_query("""
        SELECT e.id_email, e.id_company, e.subject, e.send_status, e.status,
               c.name AS company_name
        FROM emails e
        JOIN company c ON c.id_company = e.id_company
        ORDER BY e.created_at DESC
        LIMIT 50
    """)
    if not rows:
        return {
            "columns": [
                {"id": "ready", "icono": "☰", "nombre": "Ready", "color": "#94a3b8", "tarjetas": []},
                {"id": "enviados", "icono": "✈", "nombre": "Sent", "color": "#2dd4bf", "tarjetas": []},
                {"id": "abiertos", "icono": "👁", "nombre": "Opened", "color": "#f59e0b", "tarjetas": []},
                {"id": "negociacion", "icono": "💬", "nombre": "Negotiation", "color": "#a78bfa", "tarjetas": []},
                {"id": "vinculados", "icono": "🛡", "nombre": "Engaged", "color": "#34d399", "tarjetas": []},
            ]
        }

    def map_to_card(r):
        return {
            "empresa": r["company_name"],
            "desc": r["subject"] or "—",
            "prioridad": "Alta",
            "tiempo": "—",
        }

    columns = {
        "ready": {"id": "ready", "icono": "☰", "nombre": "Ready", "color": "#94a3b8", "tarjetas": []},
        "enviados": {"id": "enviados", "icono": "✈", "nombre": "Sent", "color": "#2dd4bf", "tarjetas": []},
        "abiertos": {"id": "abiertos", "icono": "👁", "nombre": "Opened", "color": "#f59e0b", "tarjetas": []},
        "negociacion": {"id": "negociacion", "icono": "💬", "nombre": "Negotiation", "color": "#a78bfa", "tarjetas": []},
        "vinculados": {"id": "vinculados", "icono": "🛡", "nombre": "Engaged", "color": "#34d399", "tarjetas": []},
    }
    for r in rows:
        row = dict(r)
        status = (row.get("status") or row.get("send_status") or "ready").lower()
        if "sent" in status:
            col = "enviados"
        elif "open" in status:
            col = "abiertos"
        elif "negotiation" in status:
            col = "negociacion"
        elif "contacted" in status or "engaged" in status:
            col = "vinculados"
        else:
            col = "ready"
        columns[col]["tarjetas"].append(map_to_card(row))

    return {"columns": list(columns.values())}


class GenerateTemplateRequest(BaseModel):
    subject: str | None = None
    context: str | None = None


@router.post("/template/ai")
def generate_email_template(payload: GenerateTemplateRequest):
    """Generate email body from context (placeholder or call AI service)."""
    body = (
        "Hello {{company_name}},\n\nWe have identified that your company is looking for junior tech talent, "
        "and at SCLAPP we connect exactly that profile with companies like yours.\n\n"
        "Could we schedule a 15-minute call this week?\n\nBest regards,\n{{your_name}} — SCLAPP"
    )
    return {"body": body, "subject": payload.subject or "Tech collaboration opportunity"}


class BulkSendRequest(BaseModel):
    template_id: int | None = None
    company_ids: list[int] = []


@router.post("/send-bulk")
def send_bulk_emails(payload: BulkSendRequest):
    """Enqueue or send bulk emails (placeholder)."""
    return {"message": "Bulk send queued", "count": len(payload.company_ids)}
