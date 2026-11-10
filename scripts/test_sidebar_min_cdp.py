import asyncio
import json
import subprocess
import urllib.request
import websockets
import base64
import os

ARTIFACT_DIR = r"C:\Users\sshee\.gemini\antigravity\brain\0b4a2b11-3c48-4ba0-81ff-eee15c0ec9f9"

async def test_min():
    p = subprocess.Popen([
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "--headless=new",
        "--remote-debugging-port=9232",
        "--window-size=1400,900",
        "http://127.0.0.1:7860"
    ])
    await asyncio.sleep(2.5)

    try:
        target = None
        for _ in range(10):
            try:
                targets_raw = urllib.request.urlopen("http://127.0.0.1:9232/json").read()
                targets = json.loads(targets_raw)
                for t in targets:
                    if t.get("type") == "page" and ("7860" in t.get("url", "") or "about:blank" in t.get("url", "")):
                        target = t
                        break
                if target and "7860" in target.get("url", ""):
                    break
            except Exception:
                pass
            await asyncio.sleep(0.5)

        if not target:
            targets_raw = urllib.request.urlopen("http://127.0.0.1:9232/json").read()
            targets = json.loads(targets_raw)
            target = next(t for t in targets if t.get("type") == "page")
        
        async with websockets.connect(target['webSocketDebuggerUrl']) as ws:
            await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': 'switchTab("chat")'}}))
            await asyncio.sleep(1.0)

            # Wait for resizer element with retry
            rx = None
            ry = None
            for attempt in range(10):
                await ws.send(json.dumps({
                    'id': 100 + attempt,
                    'method': 'Runtime.evaluate',
                    'params': {
                        'expression': '''
                            (function() {
                                const resizer = document.getElementById("sidebar-resizer");
                                if (!resizer) return null;
                                const rBox = resizer.getBoundingClientRect();
                                if (rBox.width === 0 && rBox.height === 0) return null;
                                return { resizerX: rBox.x + rBox.width / 2, resizerY: rBox.y + 200 };
                            })()
                        ''',
                        'returnByValue': True
                    }
                }))
                while True:
                    msg = await ws.recv()
                    data = json.loads(msg)
                    if data.get('id') == 100 + attempt:
                        val = data.get('result', {}).get('result', {}).get('value')
                        if val:
                            rx = val['resizerX']
                            ry = val['resizerY']
                        break
                if rx is not None:
                    print(f"Found resizer at ({rx}, {ry}) on attempt {attempt}")
                    break
                await asyncio.sleep(0.5)

            if rx is None:
                print("Could not find resizer element after retries")
                return

            # Drag far to the left (-200px) which would attempt to go below min
            await ws.send(json.dumps({
                'id': 10,
                'method': 'Input.dispatchMouseEvent',
                'params': {'type': 'mousePressed', 'x': rx, 'y': ry, 'button': 'left', 'buttons': 1, 'clickCount': 1}
            }))
            for i in range(1, 6):
                await ws.send(json.dumps({
                    'id': 10 + i,
                    'method': 'Input.dispatchMouseEvent',
                    'params': {'type': 'mouseMoved', 'x': rx - (200 * i / 5), 'y': ry, 'buttons': 1}
                }))
                await asyncio.sleep(0.02)
            await ws.send(json.dumps({
                'id': 20,
                'method': 'Input.dispatchMouseEvent',
                'params': {'type': 'mouseReleased', 'x': rx - 200, 'y': ry, 'button': 'left', 'clickCount': 1}
            }))
            await asyncio.sleep(0.5)

            # Check clamped width
            await ws.send(json.dumps({
                'id': 21,
                'method': 'Runtime.evaluate',
                'params': {
                    'expression': '''
                        (function() {
                            const sidebar = document.getElementById("chat-sidebar");
                            const sBox = sidebar.getBoundingClientRect();
                            return {
                                width: Math.round(sBox.width),
                                stored: localStorage.getItem("modeldock_sidebar_width")
                            };
                        })()
                    ''',
                    'returnByValue': True
                }
            }))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 21:
                    print('Clamped to min result:', data['result']['result']['value'])
                    break

            # Capture screenshot
            await ws.send(json.dumps({'id': 22, 'method': 'Page.captureScreenshot', 'params': {'format': 'png'}}))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 22:
                    img_data = base64.b64decode(data['result']['data'])
                    out_path = os.path.join(ARTIFACT_DIR, 'sidebar_drag_min_verified.png')
                    with open(out_path, 'wb') as f:
                        f.write(img_data)
                    print(f'Saved min width screenshot to: {out_path}')
                    break
    finally:
        p.terminate()
        p.kill()

if __name__ == '__main__':
    asyncio.run(test_min())
