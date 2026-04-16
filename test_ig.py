import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("Navigating...")
        await page.goto("https://www.instagram.com/accounts/login/", timeout=60000, wait_until="domcontentloaded")
        print("Waiting 5 seconds...")
        await page.wait_for_timeout(5000)
        
        print("Looking for cookie buttons...")
        allow_btn = page.locator('button:has-text("Allow all cookies")')
        if await allow_btn.count() > 0:
            print("Allow button found, clicking...")
            await allow_btn.first.click()
            await page.wait_for_timeout(2000)
        else:
            print("Allow button not found.")
            
        print("Checking for input visibility...")
        username_input = page.locator('input[name="username"]')
        print(f"Username input count: {await username_input.count()}")
        print(f"Username input visible: {await username_input.first.is_visible() if await username_input.count() > 0 else 'N/A'}")
        
        await browser.close()

asyncio.run(main())
