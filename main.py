import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from loguru import logger
import httpx
import sys

from scraper import BrandScraper, SESSIONS_DIR
from analyzer import BrandAnalyzer
from config import settings

# Configure Loguru
logger.remove()
logger.add(sys.stdout, colorize=True, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
logger.add("logs/brand_monitor.log", rotation="10 MB", level="DEBUG")

app = FastAPI(
    title="KhomDev CryptoScrape",
    description="AI-powered Crypto Twitter (X) & Discord Sentiment Scraper for Web3 projects.",
    version="2.0.0"
)

# Serve static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/static", StaticFiles(directory=static_dir), name="static")


# ────────────────────────── Request models ──────────────────────────

class AnalysisRequest(BaseModel):
    brand_name: str
    platforms: List[str]
    competitor_name: Optional[str] = None

class SocialConnectRequest(BaseModel):
    platform: str   # "x" or "instagram"
    username: str
    password: str


# ────────────────────────── Global error handler ──────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later.", "error": str(exc)},
    )


# ────────────────────────── Routes ──────────────────────────

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.get("/status")
async def get_status():
    return {
        "status": "online",
        "demo_mode": settings.DEMO_MODE,
        "gemini_connected": bool(settings.GEMINI_API_KEY)
    }

@app.get("/social/status")
async def social_status():
    """Returns whether saved sessions exist for each social platform."""
    return {
        "x": (SESSIONS_DIR / "x_cookies.json").exists(),
        "instagram": (SESSIONS_DIR / "instagram_cookies.json").exists(),
    }

@app.post("/social/connect")
async def social_connect(request: SocialConnectRequest):
    """
    Triggers a real Playwright login for the given platform.
    Opens a visible browser window — user may need to solve a CAPTCHA manually.
    Saves the session cookies on success.
    """
    if request.platform not in ("x", "instagram"):
        raise HTTPException(status_code=400, detail="Platform must be 'x' or 'instagram'")

    logger.info(f"Starting login flow for platform: {request.platform}")
    scraper = BrandScraper(headless=False)
    result = await scraper.login_and_save_session(
        platform=request.platform,
        username=request.username,
        password=request.password
    )
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["message"])
    return result

@app.delete("/social/disconnect/{platform}")
async def social_disconnect(platform: str):
    """Clears the saved session for a platform."""
    session_file = SESSIONS_DIR / f"{platform}_cookies.json"
    if session_file.exists():
        session_file.unlink()
        return {"success": True, "message": f"Disconnected from {platform}"}
    return {"success": False, "message": "No session was active"}

# ── Brand search & info (Wikipedia proxy) ────────────────────────────────

@app.get("/brand/search")
async def brand_search(q: str = Query(..., min_length=2)):
    """
    Smart Brand Search using Wikidata Entity Search.
    Prioritizes brands and companies over geographical or historical entities.
    """
    logger.info(f"Smart Brand search request: query='{q}'")
    url = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "wbsearchentities",
        "search": q,
        "language": "en",
        "format": "json",
        "limit": 50
    }
    headers = {"User-Agent": "BrandMonitor/1.0 (https://github.com/user/brand_monitor)"}
    
    try:
        async with httpx.AsyncClient(timeout=8, headers=headers) as client:
            res = await client.get(url, params=params)
            res.raise_for_status()
            data = res.json()
            
            search_results = data.get("search", [])
            
            # Entity keywords to strictly validate as a brand/company
            positive_kws = {"brand", "company", "manufacturer", "business", "retailer", "products", "corporation", 
                            "subsidiary", "chips", "beer", "software", "tech", "hardware", "conglomerate", "enterprise", "startup",
                            "blockchain", "cryptocurrency", "token", "protocol", "dao", "defi", "nft", "crypto", "platform", 
                            "exchange", "wallet", "web3", "network", "ecosystem", "metaverse", "dapp", "service", "app", "application",
                            "ledger", "node", "validator", "mining", "staking", "yield", "liquidity", "currency", "cash", "finance", 
                            "asset", "system", "foundation", "open source", "project"}
            
            # Exclusion list: Stop results like countries, regions, people, or media from appearing
            negative_kws = {"human", "person", "actor", "musician", "singer", "athlete", "writer", "director", "country", 
                            "city", "region", "village", "river", "mountain", "island", "historical", "film", "album", 
                            "song", "protectorate", "state", "territory", "capital"}
            
            results = []
            for item in search_results:
                label = item.get("display", {}).get("label", {}).get("value", "")
                desc  = item.get("display", {}).get("description", {}).get("value", "").lower()
                
                # Biasing: Check if description mentions brand-like keywords
                mentions_commercial = any(kw in desc for kw in positive_kws)
                mentions_negative   = any(kw in desc for kw in negative_kws)
                
                # RELAXED FILTERING: 
                # 1. If it has strong commercial markers, we trust it more
                # 2. We only skip if it's strictly a person or location without any commercial context
                
                is_brand = mentions_commercial
                
                # If it's a "country" or "person" but HAS a commercial marker (like a tech company in a city), we keep it
                if mentions_negative and not mentions_commercial:
                    continue
                    
                # We only collect results that pass the "brand-ness" test
                if is_brand or (len(desc) == 0 and not mentions_negative):
                    results.append({
                        "title": label,
                        "description": item.get("display", {}).get("description", {}).get("value", ""),
                        "is_brand": True,
                        "id": item.get("id")
                    })
            
            # Sort: Prioritize exact matches
            results.sort(key=lambda x: (x["title"].lower() == q.lower()), reverse=True)
            
            logger.info(f"Strict search results for '{q}': {len(results)} items found")
            return results
    except Exception as e:
        logger.warning(f"Smart brand search failed: {e}")
        return []


@app.get("/brand/info")
async def brand_info(name: str = Query(..., min_length=1)):
    """
    Wikipedia REST Summary — returns a concise brand/company card:
    thumbnail, short description, and a plain-text extract.
    """
    logger.info(f"Brand info request: name='{name}'")
    encoded = name.replace(" ", "_")
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"
    headers = {"User-Agent": "BrandMonitor/1.0 (https://github.com/user/brand_monitor)"}
    try:
        async with httpx.AsyncClient(timeout=8, headers=headers) as client:
            res = await client.get(url, follow_redirects=True)
            if res.status_code != 200:
                logger.warning(f"Brand info not found for '{name}' (status: {res.status_code})")
                raise HTTPException(status_code=404, detail="Brand not found")
            d = res.json()
            logger.info(f"Brand info fetched successfully for '{name}'")
            return {
                "title":       d.get("title", name),
                "description": d.get("description", ""),
                "extract":     d.get("extract", ""),
                "thumbnail":   d.get("thumbnail", {}).get("source", None),
                "url":         d.get("content_urls", {}).get("desktop", {}).get("page", ""),
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Brand info failed for '{name}': {e}")
        raise HTTPException(status_code=502, detail=str(e))


@app.post("/analyze")
async def analyze_brand(request: AnalysisRequest):
    logger.info(f"Starting analysis for brand: {request.brand_name}")
    try:
        scraper = BrandScraper(headless=settings.HEADLESS)

        logger.info(f"Scraping platforms: {request.platforms}")
        scraped_data = await scraper.scrape(request.brand_name, request.platforms, request.competitor_name)

        logger.info("Sending data to AI Analyzer...")
        analyzer = BrandAnalyzer()
        report = await analyzer.analyze(request.brand_name, scraped_data, request.competitor_name)

        logger.info("Analysis complete.")
        return report
    except Exception as e:
        logger.exception("Failed to analyze brand")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
