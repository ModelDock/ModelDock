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
        "--window-size=1280,800",
        "http://localhost:7860"
    ])
    await asyncio.sleep(2.5)
    try:
        targets_raw = urllib.request.urlopen("http://localhost:9222/json").read()
        targets = json.loads(targets_raw)
        target = next(t for t in targets if t.get("type") == "page")
        async with websockets.connect(target['webSocketDebuggerUrl']) as ws:
            positions = [
                ("left", "nav_left_view.png"),
                ("top", "nav_top_view.png"),
                ("right", "nav_right_view.png"),
                ("bottom", "nav_bottom_view.png"),
            ]

            req_id = 1
            for pos, filename in positions:
                # Apply nav position
                req_id += 1
                await ws.send(json.dumps({
                    'id': req_id,
                    'method': 'Runtime.evaluate',
                    'params': {'expression': f'applyNavPosition("{pos}")'}
                }))
                await asyncio.sleep(1.0)

                # Capture screenshot
                req_id += 1
                await ws.send(json.dumps({'id': req_id, 'method': 'Page.captureScreenshot'}))
                while True:
                    msg = await ws.recv()
                    data = json.loads(msg)
                    if data.get('id') == req_id:
                        img_bytes = base64.b64decode(data['result']['data'])
                        out_path = rf'C:\Users\sshee\.gemini\antigravity\brain\0b4a2b11-3c48-4ba0-81ff-eee15c0ec9f9\{filename}'
                        with open(out_path, 'wb') as f:
                            f.write(img_bytes)
                        print(f'[OK] Captured {filename} ({pos})')
                        break

            # Reset back to left
            req_id += 1
            await ws.send(json.dumps({
                'id': req_id,
                'method': 'Runtime.evaluate',
                'params': {'expression': 'applyNavPosition("left")'}
            }))
            await asyncio.sleep(0.5)

    finally:
        p.terminate()

if __name__ == "__main__":
    asyncio.run(capture())
