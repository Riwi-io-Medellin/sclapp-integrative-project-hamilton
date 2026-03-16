"""
Module scraping service: delegates to the real orchestrator (run_scraping),
returns a clean response for the controller. No hardcoded companies.
"""

from backend.services.scraping.scrape_service import run_scraping


class ScrapingService:
    @staticmethod
    def start_scraping(user_id: int, parameters: dict | None = None):
        """
        Start scraping: run the real orchestrator (example_source + PostgreSQL),
        then return a clear result. The orchestrator already persists scraping_logs.
        """
        if parameters is None:
            parameters = {"source": "example_source"}
        result = run_scraping(parameters=parameters, user_id=user_id, debug=False)
        return (
            {
                "message": "Scraping completed",
                "total_found": result["total_found"],
                "total_new": result["total_new"],
                "total_updated": result["total_updated"],
                "total_failed": result["total_failed"],
                "execution_status": result["execution_status"],
            },
            200,
        )
