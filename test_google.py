import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://www.google.com/search?q=Nike+reviews", timeout=15000)
        await page.wait_for_timeout(3000)
        content = await page.content()
        with open("google_debug.html", "w") as f:
            f.write(content)
        print(f"Contains div.g? {'div class=\"g\"' in content or 'div class=\"g ' in content}")
        if 'cookie' in content.lower():
            print("Cookie consent might be present.")
        await browser.close()

asyncio.run(run())
