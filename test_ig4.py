import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://www.instagram.com/accounts/login/", timeout=60000, wait_until="domcontentloaded")
        await page.wait_for_timeout(4000)
        
        # get all buttons and elements with role="button"
        elements = await page.query_selector_all('button, [role="button"]')
        print(f"Found {len(elements)} buttons/roles")
        for el in elements:
            try:
                text = await el.inner_text()
                print(f"Button text: {text.strip()[:50]}")
            except Exception:
                pass
                
        await browser.close()

asyncio.run(main())
