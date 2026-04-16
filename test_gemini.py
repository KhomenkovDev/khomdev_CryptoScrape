import asyncio
from analyzer import BrandAnalyzer

async def run():
    analyzer = BrandAnalyzer()
    
    # Fake scraped data indicating blocking
    scraped_data = {
        "google": ["Scrape blocked by bot-protection. Provide a highly realistic analysis of typical Google Reviews for this brand based on your internal knowledge."],
        "news": ["Scrape blocked. Summarize recent well-known news and public perception for this brand based on your internal knowledge.", "Also analyze their competitor if provided."]
    }
    
    res = await analyzer.analyze("Nike", scraped_data, "Adidas AG")
    import json
    print(json.dumps(res.model_dump(), indent=2))

asyncio.run(run())
