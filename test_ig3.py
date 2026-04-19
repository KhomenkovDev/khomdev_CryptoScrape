import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://www.instagram.com/accounts/login/", timeout=60000, wait_until="networkidle")
        
        allow_btn = page.locator('button:has-text("Allow all cookies")')
        if await allow_btn.count() > 0:
            await allow_btn.first.click()
            await page.wait_for_timeout(3000)
        
        print(f"Current URL: {page.url}")
        html = await page.content()
        with open("ig_page.html", "w") as f:
            f.write(html)
            
        await browser.close()

asyncio.run(main())
