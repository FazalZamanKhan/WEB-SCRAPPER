# Personal Google Maps Lead Extraction Tool

## Architecture

- **Frontend:** React (user interface)
- **Backend:** FastAPI (API, scraping controller)
- **Scraper:** Playwright (Google Maps automation)
- **Filter Engine:** Python (business logic)
- **Excel Exporter:** Python (xlsx output)

## Setup

### Backend
- Python 3.10+
- FastAPI
- Playwright
- openpyxl

### Frontend
- React (Vite or Create React App)

## Usage
- Start backend: `uvicorn main:app --reload`
- Start frontend: `npm start` or `npm run dev`

See code for details.
