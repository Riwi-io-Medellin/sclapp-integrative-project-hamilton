"""
Job filters for Riwi alignment: relevance, profile extraction, technology extraction.
Used before persisting companies from job-based sources (remoteok, remotive).
"""

import re
from typing import Any

# --- Tech role signals (accept) ---
RIWI_ACCEPT_SIGNALS = [
    # Software general
    "software developer", "software engineer", "developer", "backend", "frontend",
    "fullstack", "full stack", "web developer", "mobile developer", "app developer",
    "application engineer", "application developer", "platform engineer", "cloud engineer",

    # QA / testing
    "qa", "qa engineer", "quality assurance", "testing", "test engineer", "automation tester",

    # DevOps / infra
    "devops", "dev ops", "site reliability", "sre", "infrastructure", "cloud", "platform engineer",

    # Data / analytics
    "data analyst", "data analytics", "business intelligence", "data engineer", "data engineering",
    "data pipeline", "etl", "elt", "data scientist", "data science",

    # AI / ML
    "machine learning", "machine learning engineer", "ml engineer", "artificial intelligence",
    "generative ai", "genai", "llm", "predictive model",

    # Automation
    "ai automation", "workflow automation", "process automation", "automation engineer",
    "automation developer", "chatbot", "agentic workflow", "n8n", "zapier", "make",

    # Valid technical support
    "support engineer", "technical support engineer"
]

# --- Exclusion signals: only clearly non-tech roles (do not discard senior/lead if tech) ---
RIWI_EXCLUDE_SIGNALS = [
    "marketing",
    "sales",
    "account executive",
    "sales executive",
    "business development",
    "recruiter",
    "recruitment",
    "talent acquisition",
    "human resources",
    "hr",
    "people operations",
    "finance",
    "financial analyst",
    "accountant",
    "legal",
    "attorney",
    "lawyer",
    "customer success",
    "customer support",
    "support specialist",
    "operations",
    "administrative",
    "office manager",
    "executive assistant",
    "chief marketing officer",
    "chief financial officer",
    "vp marketing",
    "vp sales",
    "content creator",
    "copywriter",
    "seo",
    "social media",
    "community manager",
    "product marketing",
    "partnerships",
]

# --- Preference signals (junior / entry) ---
RIWI_JUNIOR_SIGNALS = [
    "junior", "trainee", "internship", "intern ", " apprentice", "apprentice",
    "entry level", "entry-level", "graduate", "associate developer",
]

# --- Supported profiles (company.category) ---
PROFILE_OPTIONS = [
    "Backend Developer",
    "Frontend Developer",
    "Full Stack Developer",
    "Data Analyst",
    "Data Engineer",
    "Data Scientist",
    "QA Engineer",
    "DevOps Engineer",
    "AI Automation Specialist",
    "Machine Learning Specialist",
    "Software Developer",
]

# --- Title/tags to profile mapping ---
PROFILE_KEYWORDS = [
    # Software
    (["backend", "back-end", "back end", "api developer", "server-side"], "Backend Developer"),
    (["frontend", "front-end", "front end", "react", "vue", "angular", "ui developer"], "Frontend Developer"),
    (["fullstack", "full-stack", "full stack"], "Full Stack Developer"),

    # QA
    (["qa", "quality assurance", "test engineer", "automation tester", "selenium", "playwright", "testing"], "QA Engineer"),

    # DevOps
    (["devops", "dev ops", "sre", "site reliability", "platform engineer", "cloud engineer", "infrastructure"], "DevOps Engineer"),

    # Data
    (["data analyst", "data analysis", "analytics", "business intelligence", "power bi", "tableau", "bi"], "Data Analyst"),
    (["data engineer", "data engineering", "etl", "elt", "data pipeline", "airflow", "dbt"], "Data Engineer"),
    (["data scientist", "data science", "machine learning", "ml", "predictive model", "model training"], "Data Scientist"),

    # AI / automation
    (["ai automation", "automation", "workflow automation", "process automation", "n8n", "zapier", "make", "chatbot", "automator"], "AI Automation Specialist"),
    (["machine learning specialist", "ml engineer", "artificial intelligence", "llm", "genai", "generative ai"], "Machine Learning Engineer"),
]

# --- Known technologies (for extraction) ---
KNOWN_TECHNOLOGIES = [
    # Languages
    "python", "javascript", "typescript", "java", "c#", "c++", "php", "ruby",
    "go", "golang", "rust", "sql",

    # Backend / frontend
    "node", "node.js", "nodejs", "react", "vue", "angular",
    "django", "flask", "fastapi", "spring", "laravel", "nestjs", "next.js",
    "html", "css", "redux", "graphql",

    # Databases
    "postgresql", "mysql", "mongodb", "redis", "snowflake", "bigquery",

    # Infra
    "docker", "kubernetes", "k8s", "aws", "azure", "gcp", "linux", "git",

    # QA
    "selenium", "playwright", "cypress", "pytest", "postman",

    # Data
    "pandas", "numpy", "power bi", "tableau", "airflow", "dbt", "spark", "hadoop",

    # AI / ML
    "tensorflow", "pytorch", "scikit-learn", "openai", "langchain", "llamaindex",

    # Automation
    "n8n", "zapier", "make", "power automate",

    "keras", "xgboost", "pyspark", "databricks", "looker", "superset", "prefect", "azure devops", "github"
]


def _text_from(raw_job: dict[str, Any], *keys: str) -> str:
    """Concatenate string values from raw_job for given keys."""
    parts = []
    for k in keys:
        v = raw_job.get(k)
        if v is None:
            continue
        if isinstance(v, str):
            parts.append(v)
        elif isinstance(v, list):
            parts.append(" ".join(str(x) for x in v))
    return " ".join(parts).lower()


def _has_any_signal(text: str, signals: list[str]) -> bool:
    """True if text (lower) contains any of the signals as whole words or clear substrings."""
    if not text:
        return False
    text = f" {text} "
    for s in signals:
        if not s.strip():
            continue
        # word boundary style: avoid "sales" in "analytics"
        pattern = r"\b" + re.escape(s.strip().lower()) + r"\b"
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def is_riwi_relevant_job(
    raw_job: dict[str, Any],
    only_riwi_relevant: bool = True,
    require_junior_focus: bool = False,
) -> bool:
    """
    Evaluates whether the vacancy is relevant for Riwi (tech roles).
    Uses title, category, tags and description when present.
    - Accepts if there are tech role signals (developer, engineer, etc.).
    - Excludes only clearly non-tech roles (marketing, sales, recruiter, hr, finance, etc.).
    - Does not exclude by seniority (senior/lead/manager tech pass); AI score differentiates.
    - Optional: require_junior_focus requires junior signals to accept.
    """
    if not only_riwi_relevant:
        return True

    text = _text_from(
        raw_job,
        "job_title", "position", "title",
        "job_category", "category",
        "tags", "technologies",
        "job_description", "description",
    )

    if not text.strip():
        return True

    if _has_any_signal(text, RIWI_EXCLUDE_SIGNALS):
        return False
    if not _has_any_signal(text, RIWI_ACCEPT_SIGNALS):
        return False
    if require_junior_focus and not _has_any_signal(text, RIWI_JUNIOR_SIGNALS):
        return False
    return True


def extract_profile_from_job(raw_job: dict[str, Any]) -> str | None:
    """
    Returns the main profile detected for company.category.
    Options: Backend Developer, Frontend Developer, Full Stack Developer,
    Data Analyst, QA Engineer, DevOps Engineer, Software Developer.
    If none is clear, returns None or "Software Developer".
    """
    text = _text_from(
        raw_job,
        "job_title", "position", "title",
        "job_category", "category",
        "tags", "technologies",
    )
    if not text:
        return "Software Developer"
    text = f" {text} "
    for keywords, profile in PROFILE_KEYWORDS:
        for kw in keywords:
            if re.search(r"\b" + re.escape(kw) + r"\b", text, re.IGNORECASE):
                return profile
    return "Software Developer"


def extract_technologies_from_job(raw_job: dict[str, Any]) -> list[str]:
    """
    Extracts technologies from tags, category, job_title, job_description.
    Uses known technologies list; returns normalized names (lowercase, no duplicates).
    """
    text = _text_from(
        raw_job,
        "job_title", "position", "title",
        "job_category", "category",
        "tags", "technologies",
        "job_description", "description",
    )
    found: list[str] = []
    seen: set[str] = set()
    text_lower = text.lower()
    for tech in KNOWN_TECHNOLOGIES:
        if tech in seen:
            continue
        # match as word to avoid "go" in "google"
        pattern = r"\b" + re.escape(tech) + r"\b"
        if re.search(pattern, text_lower):
            found.append(tech)
            seen.add(tech)
    return found
