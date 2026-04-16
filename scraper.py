import asyncio
import json
import os
from pathlib import Path
from playwright.async_api import async_playwright, BrowserContext
from bs4 import BeautifulSoup
from loguru import logger

SESSIONS_DIR = Path(__file__).parent / "sessions"
SESSIONS_DIR.mkdir(exist_ok=True)


class BrandScraper:
    def __init__(self, headless=True):
        self.headless = headless

    # ─────────────────────────── Session helpers ───────────────────────────

    def _session_path(self, platform: str) -> Path:
        return SESSIONS_DIR / f"{platform}_cookies.json"

    def _has_session(self, platform: str) -> bool:
        return self._session_path(platform).exists()

    async def _save_session(self, context: BrowserContext, platform: str):
        cookies = await context.cookies()
        self._session_path(platform).write_text(json.dumps(cookies))
        logger.info(f"Session saved for {platform}")

    async def _load_session(self, context: BrowserContext, platform: str):
        cookies = json.loads(self._session_path(platform).read_text())
        await context.add_cookies(cookies)
        logger.info(f"Session loaded for {platform}")

    # ────────────────────────── Public: login flow ──────────────────────────

    async def login_and_save_session(self, platform: str, username: str, password: str) -> dict:
        """
        Opens a real browser (visible), logs in to the platform,
        saves the session cookies, and closes the browser.
        Returns {"success": bool, "message": str}
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # always visible during login
            context = await browser.new_context()
            page = await context.new_page()
            try:
                if platform == "x":
                    result = await self._login_x(page, username, password)
                elif platform == "instagram":
                    result = await self._login_instagram(page, username, password)
                else:
                    return {"success": False, "message": f"Unknown platform: {platform}"}

                if result["success"]:
                    await self._save_session(context, platform)
                return result
            except Exception as e:
                logger.exception(f"Login failed for {platform}")
                return {"success": False, "message": str(e)}
            finally:
                await browser.close()

    async def _login_x(self, page, username: str, password: str) -> dict:
        try:
            logger.info(f"Navigating to X login for {username}...")
            await page.goto("https://x.com/i/flow/login", timeout=45000, wait_until="domcontentloaded")
            
            # Step 1: Enter username/email
            await page.wait_for_selector('input[autocomplete="username"]', timeout=30000)
            await page.fill('input[autocomplete="username"]', username)
            await page.keyboard.press("Enter")
            
            # Step 2: Handle potential "Unusual activity" or "Enter phone/username" verification
            await page.wait_for_timeout(3000)
            
            # Check for various verification/unusual activity fields
            # X sometimes asks for phone number or email again if it suspects a bot
            verifiers = [
                'input[data-testid="ocfEnterTextTextInput"]',
                'input[name="text"]',
                'text=Enter your phone number or username'
            ]
            
            for selector in verifiers:
                loc = page.locator(selector)
                if await loc.count() > 0 and await loc.is_visible():
                    logger.warning(f"X requested additional verification using selector: {selector}")
                    await loc.fill(username)
                    await page.keyboard.press("Enter")
                    await page.wait_for_timeout(2000)
                    break

            # Step 3: Password
            await page.wait_for_selector('input[name="password"]', timeout=20000)
            await page.fill('input[name="password"]', password)
            await page.keyboard.press("Enter")
            
            # Check for immediate password error
            await page.wait_for_timeout(2000)
            error_locator = page.locator('[data-testid="toast"], [data-testid="error-detail"]')
            if await error_locator.count() > 0:
                err_text = await error_locator.first.inner_text()
                if "password" in err_text.lower() or "did not match" in err_text.lower():
                    return {"success": False, "message": "Incorrect password. Please check your X credentials."}

            # Wait for home timeline or search results - indicates success
            # We wait for either the primary column (home) or the search results header
            logger.info("Waiting for login completion...")
            try:
                await page.wait_for_selector('[data-testid="primaryColumn"], [data-testid="SideNav_AccountMenu_Button"]', timeout=30000)
                logger.info("X login successful")
                return {"success": True, "message": "Logged in to X successfully"}
            except Exception:
                # One last check: are we on the home page?
                if "home" in page.url or "x.com" in page.url and await page.locator('[data-testid="AppTabBar_Home_Link"]').count() > 0:
                    return {"success": True, "message": "Logged in to X successfully"}
                raise Exception("Timed out waiting for home screen. You may need to manually complete a CAPTCHA or verification in the browser window.")
                
        except Exception as e:
            logger.error(f"X login exception: {str(e)}")
            return {"success": False, "message": f"X login failed: {str(e)}"}

    async def _login_instagram(self, page, username: str, password: str) -> dict:
        try:
            logger.info(f"Navigating to Instagram login for {username}...")
            await page.goto("https://www.instagram.com/accounts/login/", timeout=45000, wait_until="domcontentloaded")
            
            # Handle cookie consent dialog if it appears
            try:
                # Use .click() with timeout so Playwright actively waits for the
                # button to finish animating/loading and become clickable.
                allow_btn = page.get_by_role("button", name="Allow all cookies")
                await allow_btn.click(timeout=5000)
                logger.info("Clicked 'Allow all cookies'")
            except Exception:
                try:
                    decline_btn = page.get_by_role("button", name="Decline optional cookies")
                    await decline_btn.click(timeout=2000)
                    logger.info("Clicked 'Decline optional cookies'")
                except Exception as e:
                    logger.debug(f"Cookie bypass skipped or not found: {e}")

            await page.wait_for_selector('input[name="username"], input[name="email"]', timeout=30000)
            
            if await page.locator('input[name="username"]').count() > 0:
                await page.fill('input[name="username"]', username)
            else:
                await page.fill('input[name="email"]', username)
                
            if await page.locator('input[name="password"]').count() > 0:
                await page.fill('input[name="password"]', password)
                await page.locator('input[name="password"]').press("Enter")
            else:
                await page.fill('input[name="pass"]', password)
                await page.locator('input[name="pass"]').press("Enter")
                
            # Fallback click just in case
            try:
                if await page.get_by_role("button", name="Log in", exact=True).count() > 0:
                    await page.get_by_role("button", name="Log in", exact=True).click(timeout=1000)
            except:
                pass
            
            # Check for immediate password error
            await page.wait_for_timeout(3000)
            error_loc = page.locator('p[role="alert"], div[role="alert"], #slfErrorAlert, div[data-testid="login-error-message"]')
            if await error_loc.count() > 0:
                err_text = await error_loc.first.inner_text()
                if "incorrect" in err_text.lower() or "password" in err_text.lower():
                    return {"success": False, "message": "Incorrect password. Please check your Instagram credentials."}

            # Wait past "Save Login Info?" or "Suspicious Login" popup
            logger.info("Submitted login, waiting for redirect or challenges...")
            await page.wait_for_timeout(5000)
            
            # Check for suspicious login attempt / verification code
            if "checkpoint" in page.url or await page.get_by_text("Suspicious Login Attempt").count() > 0:
                return {"success": False, "message": "Instagram triggered a security checkpoint. Please solve it in the browser window then try connecting again."}

            # Dismiss "Save login info" dialog
            not_now = page.locator('text=Not Now').first
            if await not_now.count() > 0:
                await not_now.click()
                await page.wait_for_timeout(2000)
                
            # Dismiss "Turn on Notifications?"
            not_now2 = page.locator('text=Not Now').first
            if await not_now2.count() > 0:
                await not_now2.click()
            
            # Verify login by checking navigation bar or home icon
            try:
                await page.wait_for_selector('svg[aria-label="Home"], svg[aria-label="Search"], img[alt*="profile"]', timeout=20000)
                logger.info("Instagram login successful")
                return {"success": True, "message": "Logged in to Instagram successfully"}
            except Exception:
                if await page.locator('svg[aria-label="Home"]').count() > 0:
                    return {"success": True, "message": "Logged in to Instagram successfully"}
                raise Exception("Timed out waiting for Instagram home screen. Check the browser window for any blocks or verification steps.")

        except Exception as e:
            logger.error(f"Instagram login exception: {str(e)}")
            return {"success": False, "message": f"Instagram login failed: {str(e)}"}

    # ────────────────────────── Public: main scrape ──────────────────────────

    async def scrape(self, brand_name, platforms, competitor_name=None):
        results = {}
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)

            tasks = []
            platform_order = []

            if "google" in platforms:
                tasks.append(self._scrape_google_reviews(browser, brand_name))
                platform_order.append("google")

            if "x" in platforms:
                tasks.append(self._scrape_x(browser, brand_name))
                platform_order.append("x")

            if "instagram" in platforms:
                tasks.append(self._scrape_instagram(browser, brand_name))
                platform_order.append("instagram")

            if "news" in platforms:
                tasks.append(self._scrape_google_news(browser, brand_name))
                platform_order.append("news")

            if competitor_name:
                logger.info(f"Targeting competitor: {competitor_name}")
                tasks.append(self._scrape_google_news(browser, competitor_name, prefix="competitor_news"))
                platform_order.append("competitor_data")

            scraped_results = await asyncio.gather(*tasks, return_exceptions=True)

            for key, value in zip(platform_order, scraped_results):
                if isinstance(value, Exception):
                    logger.warning(f"Scrape failed for {key}: {value}")
                    results[key] = [f"Scrape error: {str(value)}"]
                else:
                    results[key] = value

            await browser.close()
        return results

    # ───────────────────────── Scrapers: Google ─────────────────────────────

    async def _scrape_google_reviews(self, browser, brand_name):
        logger.debug(f"Scraping Google Reviews for {brand_name}")
        page = await browser.new_page()
        try:
            search_url = f"https://www.google.com/search?q={brand_name}+reviews"
            await page.goto(search_url, timeout=15000)
            await page.wait_for_selector("div.g", timeout=5000)
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            reviews = []
            for g in soup.select('div.g')[:5]:
                snippet = g.select_one('div.VwiC3b')
                if snippet:
                    reviews.append(snippet.get_text())
            return reviews if reviews else ["No reviews found on Google."]
        except Exception as e:
            logger.warning(f"Google Review scrape failed for {brand_name}: {str(e)}")
            return [f"Scrape blocked by bot-protection. Directly analyze your internal knowledge base to evaluate typical Google Reviews, customer sentiment, strengths, and weaknesses for '{brand_name}'."]
        finally:
            await page.close()

    async def _scrape_google_news(self, browser, query, prefix=""):
        logger.debug(f"Scraping Google News for {query}")
        page = await browser.new_page()
        try:
            search_url = f"https://www.google.com/search?q={query}&tbm=nws"
            await page.goto(search_url, timeout=15000)
            await page.wait_for_selector("div.SoEx9c, div.g", timeout=5000)
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            news_items = []
            for item in soup.select('div[data-ved]')[:8]:
                text = item.get_text()
                if len(text) > 30:
                    news_items.append(text[:200] + "...")
            return news_items
        except Exception as e:
            logger.warning(f"Google News scrape failed for {query}: {str(e)}")
            return [f"Scrape blocked by bot-protection. Please summarize recent well-known news, public perception, and market positioning for '{query}' based on your internal knowledge."]
        finally:
            await page.close()

    # ───────────────────── Scrapers: X (Twitter) — Real ─────────────────────

    async def _scrape_x(self, browser, brand_name):
        logger.debug(f"Scraping X for {brand_name}")
        if not self._has_session("x"):
            logger.warning("No X session found. Returning placeholder — connect account in Social Accounts tab.")
            return [f"No session active. Summarize the general sentiment and common topics discussed on X (Twitter) regarding '{brand_name}' using your internal knowledge."]

        context = await browser.new_context()
        await self._load_session(context, "x")
        page = await context.new_page()
        try:
            search_url = f"https://x.com/search?q={brand_name}&src=typed_query&f=top"
            await page.goto(search_url, timeout=20000)
            await page.wait_for_selector('[data-testid="tweet"]', timeout=15000)

            tweets = []
            tweet_elements = await page.query_selector_all('[data-testid="tweet"]')
            for el in tweet_elements[:15]:
                text_el = await el.query_selector('[data-testid="tweetText"]')
                if text_el:
                    text = await text_el.inner_text()
                    # Try to get engagement stats
                    likes_el = await el.query_selector('[data-testid="like"] span')
                    likes = await likes_el.inner_text() if likes_el else "0"
                    retweets_el = await el.query_selector('[data-testid="retweet"] span')
                    retweets = await retweets_el.inner_text() if retweets_el else "0"
                    tweets.append(f"{text.strip()} [❤️ {likes} | 🔁 {retweets}]")

            logger.info(f"X: scraped {len(tweets)} tweets for '{brand_name}'")
            return tweets if tweets else ["No tweets found for this brand."]
        except Exception as e:
            logger.warning(f"X scrape failed: {str(e)}")
            return [f"Scrape blocked by bot-protection. Summarize the general sentiment and common topics discussed on X (Twitter) regarding '{brand_name}' using your internal knowledge."]
        finally:
            await page.close()
            await context.close()

    # ─────────────────── Scrapers: Instagram — Real ──────────────────────────

    async def _scrape_instagram(self, browser, brand_name):
        logger.debug(f"Scraping Instagram for {brand_name}")
        if not self._has_session("instagram"):
            logger.warning("No Instagram session found. Returning placeholder.")
            return [f"No session active. Summarize the typical Instagram aesthetic, influencer perception, and visual brand identity for '{brand_name}' using your internal knowledge."]

        context = await browser.new_context()
        await self._load_session(context, "instagram")
        page = await context.new_page()
        try:
            # Search via hashtag explore
            tag = brand_name.replace(" ", "").lower()
            await page.goto(f"https://www.instagram.com/explore/tags/{tag}/", timeout=20000)
            await page.wait_for_selector('article', timeout=15000)

            # Click first post to get captions
            posts_data = []
            post_links = await page.query_selector_all('article a')
            for link in post_links[:8]:
                href = await link.get_attribute('href')
                if href and '/p/' in href:
                    post_url = f"https://www.instagram.com{href}"
                    post_page = await browser.new_page()
                    try:
                        await post_page.goto(post_url, timeout=15000)
                        await post_page.wait_for_selector('article', timeout=10000)
                        content = await post_page.content()
                        soup = BeautifulSoup(content, 'html.parser')
                        # Caption is in meta description
                        meta = soup.find('meta', {'name': 'description'})
                        if meta and meta.get('content'):
                            posts_data.append(meta['content'][:300])
                    except Exception:
                        pass
                    finally:
                        await post_page.close()
                    if len(posts_data) >= 5:
                        break

            logger.info(f"Instagram: scraped {len(posts_data)} posts for '#{tag}'")
            return posts_data if posts_data else ["No Instagram posts found for this brand."]
        except Exception as e:
            logger.warning(f"Instagram scrape failed: {str(e)}")
            return [f"Scrape blocked by bot-protection. Summarize the typical Instagram aesthetic, influencer perception, and visual brand identity for '{brand_name}' using your internal knowledge."]
        finally:
            await page.close()
            await context.close()


if __name__ == "__main__":
    scraper = BrandScraper(headless=False)
    asyncio.run(scraper.scrape("Apple", ["google", "news"], competitor_name="Samsung"))
