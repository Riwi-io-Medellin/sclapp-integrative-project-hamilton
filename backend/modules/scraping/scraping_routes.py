"""
Scraping routes: POST /scraping/start to trigger a scraping run.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.modules.scraping.scraping_controller import start_scraping

router = APIRouter(prefix="/scraping", tags=["scraping"])


class StartScrapingBody(BaseModel):
    user_id: int | None = None
    parameters: dict | None = None


@router.post("/start")
def post_scraping_start(body: StartScrapingBody | None = None):
    """
    Start scraping. Optional body: { "user_id": 1, "parameters": { "source": "example_source" } }.
    If user_id is omitted, the first user in the DB is used for scraping_logs (avoids FK errors).
    """
    payload = body or StartScrapingBody()
    user_id = payload.user_id  # None is ok: run_scraping will use first user for log
    parameters = payload.parameters
    try:
        data, status = start_scraping(user_id=user_id, parameters=parameters)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
