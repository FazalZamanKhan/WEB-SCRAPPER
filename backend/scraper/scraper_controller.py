import asyncio
from typing import Optional

class ScraperController:
    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        self._results = []
        self._status = "idle"

    async def start(self, scrape_func, *args, **kwargs):
        if self._task and not self._task.done():
            raise RuntimeError("Scraping already in progress")
        self._stop_event.clear()
        self._status = "running"
        self._results = []
        self._task = asyncio.create_task(self._run(scrape_func, *args, **kwargs))

    async def _run(self, scrape_func, *args, **kwargs):
        try:
            async for item in scrape_func(self._stop_event, *args, **kwargs):
                self._results.append(item)
        except Exception as e:
            self._status = f"error: {e}"
        else:
            self._status = "completed" if not self._stop_event.is_set() else "stopped"

    def stop(self):
        self._stop_event.set()
        self._status = "stopping"

    def get_results(self):
        return self._results

    def get_status(self):
        return self._status
