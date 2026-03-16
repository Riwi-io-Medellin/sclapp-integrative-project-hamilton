"""
OpenAI-based job classification for Riwi: relevance, profile, score, technologies.
Fallback to rule-based extraction if API key missing or request fails.
"""

import json
import re
from typing import Any

from backend.core.config import get_settings

PROFILE_OPTIONS = [
    "Backend Developer",
    "Frontend Developer",
    "Full Stack Developer",
    "Data Analyst",
    "QA Engineer",
    "DevOps Engineer",
    "Software Developer",
]


def _build_prompt(raw_job: dict[str, Any]) -> str:
    """Build a short text block for the LLM from raw_job."""
    parts = []
    if raw_job.get("company_name"):
        parts.append(f"Company: {raw_job['company_name']}")
    if raw_job.get("job_title") or raw_job.get("position") or raw_job.get("title"):
        title = raw_job.get("job_title") or raw_job.get("position") or raw_job.get("title")
        parts.append(f"Job title: {title}")
    if raw_job.get("job_category") or raw_job.get("category"):
        cat = raw_job.get("job_category") or raw_job.get("category")
        parts.append(f"Category: {cat}")
    tags = raw_job.get("tags") or raw_job.get("technologies")
    if tags:
        parts.append(f"Tags: {tags if isinstance(tags, list) else [tags]}")
    if raw_job.get("job_description") or raw_job.get("description"):
        desc = (raw_job.get("job_description") or raw_job.get("description")) or ""
        if isinstance(desc, str) and len(desc) > 1200:
            desc = desc[:1200] + "..."
        parts.append(f"Description: {desc}")
    if raw_job.get("source"):
        parts.append(f"Source: {raw_job['source']}")
    return "\n".join(parts) if parts else "No job data"


def _validate_ai_response(data: dict[str, Any]) -> dict[str, Any]:
    """Ensure profile, score, technologies match expected schema."""
    profile = data.get("profile")
    if profile not in PROFILE_OPTIONS:
        profile = "Software Developer"
    score = data.get("score")
    if score is not None:
        try:
            score = int(score)
            if score not in (1, 2, 3):
                score = None
        except (TypeError, ValueError):
            score = None
    techs = data.get("technologies")
    if not isinstance(techs, list):
        techs = []
    techs = [str(t).strip().lower() for t in techs if t and isinstance(t, (str, int))][:15]
    return {
        "is_relevant": bool(data.get("is_relevant")),
        "profile": profile,
        "score": score,
        "technologies": techs,
        "reason": str(data.get("reason") or "")[:200],
    }


# Stable model for the classifier (JSON in message.content). Do not use gpt-5-mini here.
CLASSIFIER_MODEL = "gpt-4o-mini"


def classify_job_with_ai(raw_job: dict[str, Any]) -> dict[str, Any] | None:
    """
    Classify job with OpenAI: is_relevant, profile, score (1-3), technologies, reason.
    Returns None if API key missing or request fails (caller should use rule-based fallback).
    """
    settings = get_settings()
    api_key = settings.get("openai_api_key")
    model = CLASSIFIER_MODEL

    if not api_key or not str(api_key).strip():
        return None

    print("[OPENAI MODEL]", model)

    prompt_text = _build_prompt(raw_job)
    system = (
        "Reply only with valid JSON, no markdown.\n"
        "Keys: is_relevant (boolean), profile (string), score (int), technologies (list of strings), reason (short string).\n"
        "profile must be exactly one of: Backend Developer, Frontend Developer, Full Stack Developer, "
        "You classify job postings for Riwi, a tech-talent organization. "
        "Data Analyst, QA Engineer, DevOps Engineer, Software Developer.\n"
        "Interpretation rules:\n"
        "- is_relevant = true if the job is clearly technical/software-related and potentially useful for Riwi, "
        "even if it is not ideal for junior talent.\n"
        "- is_relevant = false only if the role is clearly non-technical or clearly unrelated to software/tech hiring.\n"
        "- score = 3 if the role is highly aligned with junior/trainee/apprentice/entry-level tech talent.\n"
        "- score = 2 if the role is technical and useful for Riwi but not strongly junior-focused.\n"
        "- score = 1 if the role is technical but has low affinity for Riwi's junior talent pipeline.\n"
        "- Do not reject a role only because it is mid-level or senior if it is still clearly a technical/software role.\n"
        "- Reject non-technical roles such as sales, marketing, recruiter, HR, finance, legal, executive, or operations.\n"
        "technologies:\n"
        "- return a short list of real technical stack items only.\n"
        "- include only concrete technologies such as python, javascript, typescript, react, docker, postgresql, aws.\n"
        "- exclude business/domain words such as insurance, trading, onboarding, research, project management, strategy.\n"
        "reason:\n"
        "- keep it short, one sentence, explaining relevance and score."
    )
    
    user = f"Classify this job:\n{prompt_text}"

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_completion_tokens=400,
        )

        # --- Diagnóstico: tipo y estructura de la respuesta ---
        print("[OPENAI RESPONSE OBJECT TYPE]", type(response).__name__)
        try:
            dump = getattr(response, "model_dump", None) or getattr(response, "dict", None)
            if callable(dump):
                d = dump()
                summary = {k: type(v).__name__ if k == "choices" else (str(v)[:80] if v is not None else None) for k, v in (list(d.items())[:8])}
                print("[OPENAI RESPONSE DUMP]", summary)
            else:
                attrs = [a for a in dir(response) if not a.startswith("_")]
                print("[OPENAI RESPONSE DUMP]", "attrs:", attrs[:20])
        except Exception as dump_err:
            print("[OPENAI RESPONSE DUMP]", "dump_err:", type(dump_err).__name__, str(dump_err)[:200])

        # --- Robust text extraction (content may be str or list of parts) ---
        content = ""
        if response.choices:
            msg = response.choices[0].message
            # If content is empty, inspect the message for diagnostics
            raw_content = getattr(msg, "content", None)
            if raw_content is None or (isinstance(raw_content, str) and not raw_content.strip()):
                try:
                    msg_dump = getattr(msg, "model_dump", None) or getattr(msg, "dict", None)
                    if callable(msg_dump):
                        print("[OPENAI RESPONSE DUMP] message keys:", list(msg_dump().keys()))
                    else:
                        print("[OPENAI RESPONSE DUMP] message attrs:", [a for a in dir(msg) if not a.startswith("_")])
                except Exception:
                    pass
            if isinstance(raw_content, str):
                content = raw_content.strip()
            elif isinstance(raw_content, list):
                parts = []
                for part in raw_content:
                    if isinstance(part, dict):
                        parts.append(part.get("text") or part.get("content") or "")
                    elif hasattr(part, "text"):
                        parts.append(getattr(part, "text", "") or "")
                    elif hasattr(part, "content"):
                        parts.append(getattr(part, "content", "") or "")
                    elif isinstance(part, str):
                        parts.append(part)
                content = "".join(parts).strip()
            if not content and getattr(msg, "refusal", None):
                print("[OPENAI RAW CONTENT] (refusal)", str(msg.refusal)[:200])
            if not content and hasattr(msg, "content_parts") and msg.content_parts:
                for p in msg.content_parts:
                    if isinstance(p, dict) and p.get("type") == "text":
                        content = (p.get("text") or "").strip()
                        break
                    if getattr(p, "type", None) == "text":
                        content = (getattr(p, "text", None) or "").strip()
                        break
                content = content or ""

        print("[OPENAI RAW CONTENT]", content[:500] + ("..." if len(content) > 500 else "") if content else "(empty)")
        if not content:
            return None
        # Strip markdown code fences if present, then parse JSON
        content = re.sub(r"^```\w*\n?", "", content)
        content = re.sub(r"\n?```\s*$", "", content)
        data = json.loads(content)
        print("[OPENAI PARSED JSON]", data)
        result = _validate_ai_response(data)
        print("[OPENAI VALIDATED SCORE]", result.get("score"))
        return result
    except Exception as e:
        print("[OPENAI CLASSIFIER ERROR]", type(e).__name__, str(e))
        return None
