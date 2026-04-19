import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("Navigating...")
        await page.goto("https://www.instagram.com/accounts/login/", timeout=60000, wait_until="networkidle")
        
        allow_btn = page.locator('button:has-text("Allow all cookies")')
        if await allow_btn.count() > 0:
            print("Allow button found, clicking...")
            await allow_btn.first.click()
            await page.wait_for_timeout(3000)
        
        print("Checking for inputs...")
        inputs = await page.query_selector_all('input')
        print(f"Total inputs found: {len(inputs)}")
        for i in inputs:
            name = await i.get_attribute("name")
            print(f"Input name: {name}")
            
        await browser.close()

asyncio.run(main())
