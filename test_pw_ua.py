import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = await context.new_page()
        print("Navigating to Google...")
        await page.goto("https://www.google.com/search?q=Nike+reviews", timeout=15000)
        try:
            await page.wait_for_selector("div.g", timeout=10000)
            print("Found div.g")
        except Exception as e:
            print("Timeout", e)
        await browser.close()

asyncio.run(run())
