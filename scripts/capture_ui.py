import asyncio
import os
import time
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 820})
        await page.goto("http://127.0.0.1:7860")
        await page.wait_for_timeout(2000)

        # 1. Switch to Explore Tab
        await page.click('button[data-tab="hf-hub"]')
        await page.wait_for_timeout(1500)
        await page.screenshot(path="C:/Users/sshee/.gemini/antigravity/brain/0b4a2b11-3c48-4ba0-81ff-eee15c0ec9f9/explore_view_fixed.png")
        print("[OK] Explore view captured")

        # 2. Click 'Inspect & Download GGUF' on DeepSeek R1
        inspect_btn = await page.wait_for_selector(".btn-primary", timeout=5000)
        buttons = await page.query_selector_all(".card-footer .btn-primary")
        if buttons:
            await buttons[0].click()
            await page.wait_for_timeout(2500)
            await page.screenshot(path="C:/Users/sshee/.gemini/antigravity/brain/0b4a2b11-3c48-4ba0-81ff-eee15c0ec9f9/modal_inspector_fixed.png")
            print("[OK] Modal Inspector view captured")

        # 3. Switch to Downloads Tab
        close_btn = await page.query_selector("#modal-repo-inspect .btn-close")
        if close_btn:
            await close_btn.click()
            await page.wait_for_timeout(500)

        await page.click('button[data-tab="downloads"]')
        await page.wait_for_timeout(1000)
        await page.screenshot(path="C:/Users/sshee/.gemini/antigravity/brain/0b4a2b11-3c48-4ba0-81ff-eee15c0ec9f9/downloads_view_fixed.png")
        print("[OK] Downloads view captured")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
