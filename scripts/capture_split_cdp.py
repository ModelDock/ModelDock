import asyncio
import base64
import json
import subprocess
import urllib.request
import websockets

async def capture_cdp():
    p = subprocess.Popen([
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "--headless=new",
        "--remote-debugging-port=9223",
        "--window-size=1400,900",
        "http://127.0.0.1:7860"
    ])
    await asyncio.sleep(2.5)
    try:
        targets_raw = urllib.request.urlopen("http://127.0.0.1:9223/json").read()
        targets = json.loads(targets_raw)
        target = next(t for t in targets if t.get("type") == "page")
        async with websockets.connect(target['webSocketDebuggerUrl']) as ws:
            # 1. Switch to Library tab
            await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': 'switchTab("library")'}}))
            await asyncio.sleep(1.5)
            
            # Capture Library Screenshot
            await ws.send(json.dumps({'id': 2, 'method': 'Page.captureScreenshot', 'params': {'format': 'png'}}))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 2:
                    img_data = base64.b64decode(data['result']['data'])
                    out_path = r"C:\Users\sshee\.gemini\antigravity\brain\0b4a2b11-3c48-4ba0-81ff-eee15c0ec9f9\library_split_warning_verified.png"
                    with open(out_path, "wb") as f:
                        f.write(img_data)
                    print(f"Captured Library screenshot: {out_path}")
                    break

            # 2. Switch to Chat tab
            await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': 'switchTab("chat")'}}))
            await asyncio.sleep(1.0)
            await ws.send(json.dumps({'id': 4, 'method': 'Page.captureScreenshot', 'params': {'format': 'png'}}))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 4:
                    img_data = base64.b64decode(data['result']['data'])
                    out_path = r"C:\Users\sshee\.gemini\antigravity\brain\0b4a2b11-3c48-4ba0-81ff-eee15c0ec9f9\chat_view_verified.png"
                    with open(out_path, "wb") as f:
                        f.write(img_data)
                    print(f"Captured Chat screenshot: {out_path}")
                    break

    finally:
        p.terminate()

asyncio.run(capture_cdp())
