import asyncio
from playwright.async_api import async_playwright
import pandas as pd

# ================= CONFIGURATION SECTION =================
# Update these names based on what you see in "Inspect"
TARGET_URL = "https://mentorbaik.com/"
AUTH_FILE = "auth.json"

# CSS SELECTORS
# Use . for classes (e.g., .post-card) or # for IDs (e.g., #main-content)
SELECTOR_POST_CONTAINER = ".post-item"   # The box wrapping the whole article
SELECTOR_AUTHOR_NAME    = ".author-name" # The tag holding the writer's name
SELECTOR_TIMESTAMP      = ".timestamp"
SELECTOR_READ_MORE      = "text='Read More'" # The text of the JS link
SELECTOR_CONTENT_BODY   = ".post-content" # The tag holding the full text
# =========================================================

async def run_scraper():
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(headless=False)
        
        # Load session from auth.json
        try:
            context = await browser.new_context(storage_state=AUTH_FILE)
        except:
            print(f"Error: {AUTH_FILE} not found. Please run the login script first.")
            return

        page = await context.new_page()
        await page.goto(TARGET_URL)
        await page.wait_for_load_state("networkidle")

        # 1. Scroll to load content
        print("Scrolling to load all articles...")
        for _ in range(5): 
            await page.mouse.wheel(0, 5000)
            await asyncio.sleep(2)

        # 2. Find all articles
        articles = await page.locator(SELECTOR_POST_CONTAINER).all()
        extracted_data = []

        print(f"Found {len(articles)} posts. Starting extraction...")

        for article in articles:
            try:
                # Get Author Name
                author = await article.locator(SELECTOR_AUTHOR_NAME).inner_text()
                
                # Expand Javascript Link
                read_more_btn = article.locator(SELECTOR_READ_MORE)
                if await read_more_btn.count() > 0:
                    await read_more_btn.click()
                    await asyncio.sleep(1) # Wait for JS expansion

                # Get Full Content
                content = await article.locator(SELECTOR_CONTENT_BODY).inner_text()

                extracted_data.append({
                    "Writer": author.strip(),
                    "Content": content.strip()
                })
            except Exception as e:
                print(f"Skipped an item due to error: {e}")

        # 3. Save and Categorize
        if extracted_data:
            df = pd.DataFrame(extracted_data)
            df.to_csv("master_data.csv", index=False)
            
            # Save individual files per writer
            for writer, group in df.groupby("Writer"):
                clean_name = "".join(x for x in writer if x.isalnum())
                group.to_csv(f"articles_{clean_name}.csv", index=False)
                print(f"File created for: {writer}")
        
        print("Done!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())