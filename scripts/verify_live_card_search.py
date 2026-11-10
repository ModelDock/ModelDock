import asyncio
import json
import base64
import subprocess
import urllib.request
import websockets
import os

async def run():
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    p = subprocess.Popen([
        edge_path,
        "--headless=new",
        "--remote-debugging-port=9222",
        "--window-size=1280,850",
        "http://localhost:7860"
    ])
    await asyncio.sleep(2.5)

    try:
        targets_raw = urllib.request.urlopen("http://localhost:9222/json").read()
        targets = json.loads(targets_raw)
        target = next(t for t in targets if t.get("type") == "page")

        async with websockets.connect(target['webSocketDebuggerUrl']) as ws:
            # 1. Switch to Explore Tab
            await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': 'switchTab("hf-hub");'}}))
            await asyncio.sleep(1.5)

            # 2. Type "Z-Image" character by character or as an input event
            type_script = """
            (() => {
                const input = document.getElementById("hf-search-query");
                input.focus();
                input.value = "Z-Image";
                input.dispatchEvent(new Event("input", { bubbles: true }));
            })()
            """
            await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': type_script}}))
            # Wait for local cards + debounced Hugging Face search to populate grid
            await asyncio.sleep(1.5)

            # 3. Inspect DOM state
            check_script = """
            (() => {
                const dd = document.getElementById("omni-search-dropdown");
                const grid = document.getElementById("hf-models-grid");
                const cards = grid ? Array.from(grid.querySelectorAll(".model-card")) : [];
                const installedCards = grid ? Array.from(grid.querySelectorAll(".model-card-installed")) : [];
                const modelNames = cards.map(c => {
                    const el = c.querySelector(".model-name");
                    return el ? el.textContent.trim() : "";
                });
                const ddComputedDisplay = dd ? window.getComputedStyle(dd).display : "none";

                return {
                    dropdownDisplay: ddComputedDisplay,
                    dropdownHidden: dd ? dd.classList.contains("hidden") : true,
                    totalCards: cards.length,
                    installedCardsCount: installedCards.length,
                    modelNames: modelNames.slice(0, 8),
                };
            })()
            """
            await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': check_script, 'returnByValue': True}}))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 3:
                    eval_result = data['result']['result']['value']
                    print("DOM Check Result:", json.dumps(eval_result, indent=2))
                    break

            # 4. Capture Screenshot of Live Model Cards Grid
            await ws.send(json.dumps({'id': 4, 'method': 'Page.captureScreenshot'}))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 4:
                    img_bytes = base64.b64decode(data['result']['data'])
                    out_path = r'C:\Users\sshee\.gemini\antigravity\brain\0b4a2b11-3c48-4ba0-81ff-eee15c0ec9f9\live_card_search_verified.png'
                    with open(out_path, 'wb') as f:
                        f.write(img_bytes)
                    print(f"[OK] Live model cards grid screenshot captured to {out_path}!")
                    break

    finally:
        p.terminate()
        p.wait()

if __name__ == "__main__":
    asyncio.run(run())
