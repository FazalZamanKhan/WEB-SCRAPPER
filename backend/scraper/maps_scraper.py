
import asyncio
from typing import AsyncGenerator, Dict, Any

from playwright.async_api import async_playwright

async def scrape_google_maps(stop_event: asyncio.Event, params: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
    print("[scraper] Starting Google Maps scraping with params:", params, flush=True)
    business_keyword = params.get("business_keyword", "")
    location = params.get("location", "")
    max_results = params.get("max_results", 10)
    filters = params.get("filters", {})
    search_url = f"https://www.google.com/maps/search/{business_keyword.replace(' ', '+')}+in+{location.replace(' ', '+')}"
    print(f"[scraper] Navigating to: {search_url}", flush=True)

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            page = await context.new_page()
            await page.goto(search_url)
            await page.wait_for_selector('[role="main"]')
            print("[scraper] Page loaded.", flush=True)

            # Scroll and collect business cards
            results = []
            last_count = 0
            scroll_attempts = 0
            while len(results) < max_results and scroll_attempts < 30 and not stop_event.is_set():
                cards = await page.query_selector_all('[role="article"]')
                print(f"[scraper] Found {len(cards)} cards so far.", flush=True)
                for card in cards[len(results):]:
                    try:
                        await card.click()
                        await page.wait_for_timeout(1500)
                        name = await page.locator('h1 span').first.text_content()
                        address = await page.locator('[data-item-id="address"]').first.text_content() if await page.locator('[data-item-id="address"]').count() else None
                        phone = await page.locator('[data-item-id="phone"]').first.text_content() if await page.locator('[data-item-id="phone"]').count() else None
                        website = await page.locator('[data-item-id="authority"] a').first.get_attribute('href') if await page.locator('[data-item-id="authority"] a').count() else None
                        rating = None
                        try:
                            rating_text = await page.locator('span[aria-label*="stars"]').first.text_content()
                            rating = float(rating_text.split()[0])
                        except Exception as e:
                            print(f"[scraper] Rating parse error: {e}", flush=True)
                        maps_url = page.url

                        # Apply filters
                        if filters.get("require_phone") and not phone:
                            continue
                        if filters.get("no_website_only") and website:
                            continue
                        if filters.get("with_website_only") and not website:
                            continue
                        if filters.get("exclude_closed") and (name and "permanently closed" in name.lower()):
                            continue
                        if filters.get("min_rating", 0) > 0 and (not rating or rating < filters["min_rating"]):
                            continue

                        results.append(1)
                        print(f"[scraper] Yielding business: {name}", flush=True)
                        yield {
                            "name": name,
                            "phone": phone,
                            "address": address,
                            "website": website,
                            "rating": rating,
                            "location": location,
                            "maps_url": maps_url
                        }
                        if len(results) >= max_results:
                            break
                    except Exception as e:
                        print(f"[scraper] Card parse error: {e}", flush=True)
                        continue
                # Scroll results panel
                results_panel = await page.query_selector('[role="main"] [aria-label]')
                if results_panel:
                    await results_panel.evaluate('(el) => { el.scrollBy(0, 500); }')
                await page.wait_for_timeout(2000)
                if len(results) == last_count:
                    scroll_attempts += 1
                else:
                    scroll_attempts = 0
                last_count = len(results)
            await browser.close()
            print("[scraper] Scraping finished.", flush=True)
    except Exception as e:
        print(f"[scraper] Playwright error: {e}", flush=True)
