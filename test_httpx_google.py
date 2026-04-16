import asyncio
import httpx
from bs4 import BeautifulSoup

async def run():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    async with httpx.AsyncClient(headers=headers) as client:
        res = await client.get('https://www.google.com/search?q=Nike+reviews')
        content = res.text
        print('div class g in content:', 'div class="g"' in content or 'div class="g ' in content)
        print('captcha in content:', 'captcha' in content.lower() or 'unusual traffic' in content.lower())
        
asyncio.run(run())
