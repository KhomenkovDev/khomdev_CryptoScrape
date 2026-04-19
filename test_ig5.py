import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://www.instagram.com/accounts/login/", timeout=60000, wait_until="domcontentloaded")
        
        print("Waiting for 'Allow all cookies'")
        try:
            btn = page.get_by_role("button", name="Allow all cookies")
            await btn.wait_for(state="visible", timeout=6000)
            count = await btn.count()
            print(f"Button count: {count}")
            for i in range(count):
                is_vis = await btn.nth(i).is_visible()
                print(f"Button {i} visible: {is_vis}")
            
            await btn.first.click(timeout=3000)
            print("Clicked successfully!")
        except Exception as e:
            print(f"Failed: {e}")
                
        await browser.close()

asyncio.run(main())
