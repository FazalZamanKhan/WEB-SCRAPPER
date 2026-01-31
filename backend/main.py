


from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import threading
import asyncio
from backend.scraper.scraper_controller import ScraperController
from backend.scraper.maps_scraper import scrape_google_maps
from backend.exporter.excel_exporter import export_to_excel


app = FastAPI()

# Enable CORS for frontend (React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Models ---
class Filters(BaseModel):
    require_phone: bool
    no_website_only: bool
    with_website_only: bool
    exclude_closed: bool
    min_rating: Optional[float] = 0

class ScrapeRequest(BaseModel):
    business_keyword: str
    location: str
    radius_km: int
    max_results: int
    filters: Filters


# --- Scraping State ---
scraper_controller = ScraperController()
scraping_thread = None
scraped_file_path = "leads/leads.xlsx"

def run_scraper_async(params: ScrapeRequest):
    """Run the async scraper in a thread for FastAPI compatibility."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # Prepare params dict for scraper
    params_dict = {
        "business_keyword": params.business_keyword,
        "location": params.location,
        "radius_km": params.radius_km,
        "max_results": params.max_results,
        "filters": params.filters.dict()
    }
    # Start and WAIT for scraping to finish
    loop.run_until_complete(scraper_controller._run(scrape_google_maps, params_dict))
    results = scraper_controller.get_results()
    # Determine if website column is needed
    filters = params.filters
    include_website = filters.no_website_only or filters.with_website_only
    export_to_excel(results, scraped_file_path, include_website=include_website)


@app.get("/")
def root():
    return {"message": "Google Maps Lead Extraction Tool Backend"}


# --- API Endpoints ---

@app.post("/scrape/start")
def start_scraping(request: ScrapeRequest, background_tasks: BackgroundTasks):
    global scraping_thread
    if scraper_controller.get_status() == "running":
        raise HTTPException(status_code=400, detail="Scraping already in progress")
    scraping_thread = threading.Thread(target=run_scraper_async, args=(request,))
    scraping_thread.start()
    return {"status": "started"}


@app.post("/scrape/stop")
def stop_scraping():
    if scraper_controller.get_status() != "running":
        return {"status": "not running"}
    scraper_controller.stop()
    return {"status": "stopping"}

@app.get("/scrape/download")
def download_results():
    if not os.path.exists(scraped_file_path):
        raise HTTPException(status_code=404, detail="No results available")
    return FileResponse(scraped_file_path, filename="leads.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
