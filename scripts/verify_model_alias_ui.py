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
            # 1. Switch to Library Tab
            await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': 'switchTab("library");'}}))
            await asyncio.sleep(1.2)

            # 2. Set aliases for models to demonstrate both aliased models and default un-aliased models
            alias_setup = """
            (async () => {
                await fetch("/api/models/alias", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ model_name: "DeepSeek-R1-Distill-Qwen-7B-Q4_K_M", alias: "DeepSeek R1 Reasoner (7B)" })
                });
                await fetch("/api/models/alias", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ model_name: "qwen2.5-coder-7b-instruct-q4_k_m-00002-of-00002", alias: "Qwen 2.5 Coder (7B)" })
                });
                await loadLocalModels();
            })()
            """
            await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': alias_setup, 'awaitPromise': True}}))
            await asyncio.sleep(1.5)

            # 3. Check cards in DOM
            check_dom = """
            (() => {
                const grid = document.getElementById("local-models-grid");
                const cards = grid ? Array.from(grid.querySelectorAll(".model-card")) : [];
                return cards.map(c => {
                    const title = c.querySelector(".model-name");
                    const sub = c.querySelector(".model-author");
                    const badge = c.querySelector(".model-name .badge");
                    return {
                        title: title ? title.textContent.trim() : "",
                        sub: sub ? sub.textContent.trim() : "",
                        hasAliasBadge: Boolean(badge),
                    };
                });
            })()
            """
            await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': check_dom, 'returnByValue': True}}))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 3:
                    cards_info = data['result']['result']['value']
                    print("Library Cards with Aliases:", json.dumps(cards_info, indent=2))
                    break

            # 4. Open Alias modal for z-image-turbo-Q4_K_M to capture the modal UI in action
            await ws.send(json.dumps({'id': 4, 'method': 'Runtime.evaluate', 'params': {'expression': 'openModelAliasModal("z-image-turbo-Q4_K_M", "Z-Image Turbo Fast");'}}))
            await asyncio.sleep(0.8)

            # 5. Capture Screenshot showing Library and open Alias Modal
            await ws.send(json.dumps({'id': 5, 'method': 'Page.captureScreenshot'}))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 5:
                    img_bytes = base64.b64decode(data['result']['data'])
                    out_path = r'C:\Users\sshee\.gemini\antigravity\brain\0b4a2b11-3c48-4ba0-81ff-eee15c0ec9f9\model_alias_modal_verified.png'
                    with open(out_path, 'wb') as f:
                        f.write(img_bytes)
                    print(f"[OK] Alias modal screenshot saved to {out_path}!")
                    break

            # 6. Save the alias and close modal
            await ws.send(json.dumps({'id': 6, 'method': 'Runtime.evaluate', 'params': {'expression': 'saveModelAlias();', 'awaitPromise': True}}))
            await asyncio.sleep(1.2)

            # 7. Capture Library cards after alias saved
            await ws.send(json.dumps({'id': 7, 'method': 'Page.captureScreenshot'}))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 7:
                    img_bytes = base64.b64decode(data['result']['data'])
                    out_path = r'C:\Users\sshee\.gemini\antigravity\brain\0b4a2b11-3c48-4ba0-81ff-eee15c0ec9f9\model_alias_library_verified.png'
                    with open(out_path, 'wb') as f:
                        f.write(img_bytes)
                    print(f"[OK] Library with custom aliases saved to {out_path}!")
                    break

            # 8. Switch to Chat tab to verify dropdown shows alias
            await ws.send(json.dumps({'id': 8, 'method': 'Runtime.evaluate', 'params': {'expression': 'switchTab("chat");'}}))
            await asyncio.sleep(1.0)
            await ws.send(json.dumps({'id': 9, 'method': 'Page.captureScreenshot'}))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 9:
                    img_bytes = base64.b64decode(data['result']['data'])
                    out_path = r'C:\Users\sshee\.gemini\antigravity\brain\0b4a2b11-3c48-4ba0-81ff-eee15c0ec9f9\model_alias_chat_dropdown_verified.png'
                    with open(out_path, 'wb') as f:
                        f.write(img_bytes)
                    print(f"[OK] Chat selector with aliases saved to {out_path}!")
                    break

    finally:
        p.terminate()
        p.wait()

if __name__ == "__main__":
    asyncio.run(run())
