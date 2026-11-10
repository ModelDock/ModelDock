import asyncio
from playwright.async_api import async_playwright

async def capture():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1400, "height": 900})
        
        # 1. Capture Library with split shard warning
        await page.goto("http://127.0.0.1:7860")
        await page.wait_for_timeout(2000)
        
        # Click on Library tab
        await page.click('button[data-tab="library"], button:has-text("Library")')
        await page.wait_for_timeout(1500)
        await page.screenshot(path=r"C:\Users\sshee\.gemini\antigravity\brain\0b4a2b11-3c48-4ba0-81ff-eee15c0ec9f9\library_split_warning_verified.png")
        print("Captured library screenshot.")

        # 2. Go to Chat tab
        await page.click('button[data-tab="chat"], button:has-text("Chat")')
        await page.wait_for_timeout(1500)
        await page.screenshot(path=r"C:\Users\sshee\.gemini\antigravity\brain\0b4a2b11-3c48-4ba0-81ff-eee15c0ec9f9\chat_view_verified.png")
        print("Captured chat screenshot.")

        await browser.close()

asyncio.run(capture())
