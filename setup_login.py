import asyncio
from playwright.async_api import async_playwright

async def save_session():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.goto("https://mentorbaik.com/login")
        print("Please log in manually in the browser window...")
        
        # The script waits for you to finish logging in
        # It will wait until it sees a selector that only exists after login (e.g., your profile)
        await page.wait_for_selector(".profile-icon", timeout=0) 
        
        # Save the cookies/session info
        await context.storage_state(path="auth.json")
        print("Login saved to auth.json!")
        await browser.close()

asyncio.run(save_session())