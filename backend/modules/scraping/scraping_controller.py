"""
Scraping controller: receives request data, calls module service, returns JSON and status.
"""

from backend.modules.scraping.scraping_service import ScrapingService


def start_scraping(user_id: int, parameters: dict | None = None) -> tuple[dict, int]:
    """
    Start a scraping run. Accepts user_id and optional parameters (e.g. source).
    Returns (response_dict, status_code).
    """
    return ScrapingService.start_scraping(user_id=user_id, parameters=parameters)
