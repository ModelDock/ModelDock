import asyncio
import json
import base64
import subprocess
import urllib.request
import websockets

async def capture():
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
            # 1. Switch to Explore Tab (hf-hub)
            await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': 'switchTab("hf-hub")'}}))
            await asyncio.sleep(1.5)

            # Capture Explore Tab
            await ws.send(json.dumps({'id': 2, 'method': 'Page.captureScreenshot'}))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 2:
                    img_bytes = base64.b64decode(data['result']['data'])
                    out_path = r'C:\Users\sshee\.gemini\antigravity\brain\0b4a2b11-3c48-4ba0-81ff-eee15c0ec9f9\explore_models_fixed.png'
                    with open(out_path, 'wb') as f:
                        f.write(img_bytes)
                    print('[OK] Explore models fixed captured!')
                    break

            # 2. Open DeepSeek R1 inspect modal
            await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': 'openInspectModal("unsloth/DeepSeek-R1-Distill-Qwen-7B-GGUF")'}}))
            await asyncio.sleep(2.5)

            # Capture Modal Inspector
            await ws.send(json.dumps({'id': 4, 'method': 'Page.captureScreenshot'}))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 4:
                    img_bytes = base64.b64decode(data['result']['data'])
                    out_path = r'C:\Users\sshee\.gemini\antigravity\brain\0b4a2b11-3c48-4ba0-81ff-eee15c0ec9f9\model_inspector_fixed.png'
                    with open(out_path, 'wb') as f:
                        f.write(img_bytes)
                    print('[OK] Model inspector fixed captured!')
                    break

    finally:
        p.terminate()

if __name__ == "__main__":
    asyncio.run(capture())
