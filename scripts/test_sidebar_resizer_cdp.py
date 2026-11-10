import asyncio
import json
import subprocess
import urllib.request
import websockets
import base64
import os

ARTIFACT_DIR = r"C:\Users\sshee\.gemini\antigravity\brain\0b4a2b11-3c48-4ba0-81ff-eee15c0ec9f9"

async def test_sidebar_resizing():
    print("Launching Edge headless on port 9231...")
    p = subprocess.Popen([
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "--headless=new",
        "--remote-debugging-port=9231",
        "--window-size=1400,900",
        "http://127.0.0.1:7860"
    ])
    await asyncio.sleep(2.5)

    try:
        targets_raw = urllib.request.urlopen("http://127.0.0.1:9231/json").read()
        targets = json.loads(targets_raw)
        target = next(t for t in targets if t.get("type") == "page")
        
        async with websockets.connect(target['webSocketDebuggerUrl']) as ws:
            # 1. Switch to chat tab
            await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': 'switchTab("chat")'}}))
            await asyncio.sleep(1.0)

            # 2. Get initial resizer coordinates & sidebar width
            await ws.send(json.dumps({
                'id': 2,
                'method': 'Runtime.evaluate',
                'params': {
                    'expression': '''
                        (function() {
                            const sidebar = document.getElementById("chat-sidebar");
                            const resizer = document.getElementById("sidebar-resizer");
                            if (!sidebar || !resizer) return { error: "missing_elements" };
                            const rBox = resizer.getBoundingClientRect();
                            const sBox = sidebar.getBoundingClientRect();
                            return {
                                initialWidth: sBox.width,
                                resizerX: rBox.x + rBox.width / 2,
                                resizerY: rBox.y + 200
                            };
                        })()
                    ''',
                    'returnByValue': True
                }
            }))

            coords = None
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 2:
                    coords = data['result']['result']['value']
                    print("Initial elements & coords:", coords)
                    break

            if not coords or 'error' in coords:
                print("Failed to get coords:", coords)
                return

            rx = coords['resizerX']
            ry = coords['resizerY']

            # 3. Simulate dragging resizer by +140px (expanding sidebar from 260px to ~400px)
            print(f"Dragging from ({rx}, {ry}) to ({rx + 140}, {ry})...")
            
            # mousePressed
            await ws.send(json.dumps({
                'id': 10,
                'method': 'Input.dispatchMouseEvent',
                'params': {
                    'type': 'mousePressed',
                    'x': rx,
                    'y': ry,
                    'button': 'left',
                    'buttons': 1,
                    'clickCount': 1
                }
            }))
            await asyncio.sleep(0.05)

            # mouseMoved steps
            steps = 7
            for i in range(1, steps + 1):
                cur_x = rx + (140 * i / steps)
                await ws.send(json.dumps({
                    'id': 10 + i,
                    'method': 'Input.dispatchMouseEvent',
                    'params': {
                        'type': 'mouseMoved',
                        'x': cur_x,
                        'y': ry,
                        'buttons': 1
                    }
                }))
                await asyncio.sleep(0.03)

            # mouseReleased
            await ws.send(json.dumps({
                'id': 20,
                'method': 'Input.dispatchMouseEvent',
                'params': {
                    'type': 'mouseReleased',
                    'x': rx + 140,
                    'y': ry,
                    'button': 'left',
                    'clickCount': 1
                }
            }))
            await asyncio.sleep(0.5)

            # 4. Read updated width & localStorage
            await ws.send(json.dumps({
                'id': 21,
                'method': 'Runtime.evaluate',
                'params': {
                    'expression': '''
                        (function() {
                            const sidebar = document.getElementById("chat-sidebar");
                            const sBox = sidebar.getBoundingClientRect();
                            const stored = localStorage.getItem("modeldock_sidebar_width");
                            return {
                                resizedWidth: Math.round(sBox.width),
                                localStorageWidth: stored
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
                    result = data['result']['result']['value']
                    print("After drag resize:", result)
                    break

            # 5. Capture screenshot of resized sidebar
            await ws.send(json.dumps({'id': 22, 'method': 'Page.captureScreenshot', 'params': {'format': 'png'}}))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 22:
                    img_data = base64.b64decode(data['result']['data'])
                    out_path = os.path.join(ARTIFACT_DIR, "sidebar_drag_resized_verified.png")
                    with open(out_path, "wb") as f:
                        f.write(img_data)
                    print(f"Saved resized screenshot to: {out_path}")
                    break

            # 6. Test Double-Click to Reset to Default (260px)
            await ws.send(json.dumps({
                'id': 30,
                'method': 'Runtime.evaluate',
                'params': {
                    'expression': '''
                        (function() {
                            const resizer = document.getElementById("sidebar-resizer");
                            resizer.dispatchEvent(new MouseEvent("dblclick", { bubbles: true }));
                            return "dblclick_fired";
                        })()
                    ''',
                    'returnByValue': True
                }
            }))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 30:
                    break

            # Wait for 0.24s transition to finish
            await asyncio.sleep(0.35)

            await ws.send(json.dumps({
                'id': 31,
                'method': 'Runtime.evaluate',
                'params': {
                    'expression': '''
                        (function() {
                            const sidebar = document.getElementById("chat-sidebar");
                            const sBox = sidebar.getBoundingClientRect();
                            const stored = localStorage.getItem("modeldock_sidebar_width");
                            return {
                                resetWidth: Math.round(sBox.width),
                                localStorageWidth: stored
                            };
                        })()
                    ''',
                    'returnByValue': True
                }
            }))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 31:
                    result = data['result']['result']['value']
                    print("After double-click reset and transition:", result)
                    break

            # 7. Capture screenshot after reset
            await ws.send(json.dumps({'id': 32, 'method': 'Page.captureScreenshot', 'params': {'format': 'png'}}))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 32:
                    img_data = base64.b64decode(data['result']['data'])
                    out_path = os.path.join(ARTIFACT_DIR, "sidebar_drag_reset_verified.png")
                    with open(out_path, "wb") as f:
                        f.write(img_data)
                    print(f"Saved reset screenshot to: {out_path}")
                    break

            # 8. Test dragging left to clamp at MIN_WIDTH (190px)
            # Current resizer X is now at 340 (left edge of sidebar is ~80px nav + 260px = 340px)
            resizer_current_x = 340
            print(f"Dragging left from {resizer_current_x} by -200px (aiming for <190px to test min bound)...")
            await ws.send(json.dumps({
                'id': 40,
                'method': 'Input.dispatchMouseEvent',
                'params': {'type': 'mousePressed', 'x': resizer_current_x, 'y': ry, 'button': 'left', 'buttons': 1, 'clickCount': 1}
            }))
            for i in range(1, 6):
                await ws.send(json.dumps({
                    'id': 40 + i,
                    'method': 'Input.dispatchMouseEvent',
                    'params': {'type': 'mouseMoved', 'x': resizer_current_x - (200 * i / 5), 'y': ry, 'buttons': 1}
                }))
                await asyncio.sleep(0.02)
            await ws.send(json.dumps({
                'id': 50,
                'method': 'Input.dispatchMouseEvent',
                'params': {'type': 'mouseReleased', 'x': resizer_current_x - 200, 'y': ry, 'button': 'left', 'clickCount': 1}
            }))
            await asyncio.sleep(0.3)

            await ws.send(json.dumps({
                'id': 51,
                'method': 'Runtime.evaluate',
                'params': {
                    'expression': '''
                        (function() {
                            const sidebar = document.getElementById("chat-sidebar");
                            const sBox = sidebar.getBoundingClientRect();
                            const stored = localStorage.getItem("modeldock_sidebar_width");
                            return {
                                clampedMinWidth: Math.round(sBox.width),
                                localStorageWidth: stored
                            };
                        })()
                    ''',
                    'returnByValue': True
                }
            }))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 51:
                    result = data['result']['result']['value']
                    print("After dragging below minimum (clamped):", result)
                    break

            # 9. Capture screenshot at min width
            await ws.send(json.dumps({'id': 52, 'method': 'Page.captureScreenshot', 'params': {'format': 'png'}}))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 52:
                    img_data = base64.b64decode(data['result']['data'])
                    out_path = os.path.join(ARTIFACT_DIR, "sidebar_drag_min_verified.png")
                    with open(out_path, "wb") as f:
                        f.write(img_data)
                    print(f"Saved min width screenshot to: {out_path}")
                    break

    finally:
        p.terminate()
        p.kill()

if __name__ == "__main__":
    asyncio.run(test_sidebar_resizing())
