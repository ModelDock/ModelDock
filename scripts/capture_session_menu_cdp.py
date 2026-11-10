import asyncio
import json
import subprocess
import urllib.request
import websockets
import base64

async def test_session_menu():
    p = subprocess.Popen([
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "--headless=new",
        "--remote-debugging-port=9227",
        "--window-size=1400,900",
        "http://127.0.0.1:7860"
    ])
    await asyncio.sleep(2.5)
    try:
        targets_raw = urllib.request.urlopen("http://127.0.0.1:9227/json").read()
        targets = json.loads(targets_raw)
        target = next(t for t in targets if t.get("type") == "page")
        async with websockets.connect(target['webSocketDebuggerUrl']) as ws:
            # 1. Switch to chat tab
            await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': 'switchTab("chat")'}}))
            await asyncio.sleep(1.0)

            # 2. Check if a session exists in sidebar; if not, create one
            await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': '''
                (function() {
                    const items = document.querySelectorAll(".session-item");
                    if (items.length === 0) {
                        const input = document.getElementById("user-input");
                        if (input) input.value = "Test session for menu";
                        const btn = document.getElementById("btn-send");
                        if (btn) btn.click();
                        return "created_session";
                    }
                    return "session_exists";
                })()
            ''', 'returnByValue': True}}))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 2:
                    print("Step 1:", data['result']['result']['value'])
                    break

            await asyncio.sleep(3.0)

            # 3. Simulate hover on first session-item to display the Pin and 3-dots icons
            await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': '''
                (function() {
                    const item = document.querySelector(".session-item");
                    if (item) {
                        const actions = item.querySelector(".session-actions");
                        if (actions) actions.style.display = "flex";
                        return "hovered";
                    }
                    return "no_item";
                })()
            ''', 'returnByValue': True}}))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 3:
                    print("Step 2:", data['result']['result']['value'])
                    break

            # Capture screenshot showing Pin + 3 dots icon on row
            await ws.send(json.dumps({'id': 4, 'method': 'Page.captureScreenshot', 'params': {'format': 'png'}}))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 4:
                    img_data = base64.b64decode(data['result']['data'])
                    out_path = r"C:\Users\sshee\.gemini\antigravity\brain\0b4a2b11-3c48-4ba0-81ff-eee15c0ec9f9\pin_and_dots_icon_verified.png"
                    with open(out_path, "wb") as f:
                        f.write(img_data)
                    print("Captured Pin and 3-dots icon screenshot:", out_path)
                    break

            # 4. Click the 3-dots button to open the context menu
            await ws.send(json.dumps({'id': 5, 'method': 'Runtime.evaluate', 'params': {'expression': '''
                (function() {
                    const dotsBtn = document.querySelector(".session-dots-btn");
                    if (dotsBtn) {
                        dotsBtn.click();
                        return "clicked_dots";
                    }
                    return "no_dots_btn";
                })()
            ''', 'returnByValue': True}}))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 5:
                    print("Step 3:", data['result']['result']['value'])
                    break

            await asyncio.sleep(1.0)

            # Capture screenshot with open 3-dots context menu
            await ws.send(json.dumps({'id': 6, 'method': 'Page.captureScreenshot', 'params': {'format': 'png'}}))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 6:
                    img_data = base64.b64decode(data['result']['data'])
                    out_path = r"C:\Users\sshee\.gemini\antigravity\brain\0b4a2b11-3c48-4ba0-81ff-eee15c0ec9f9\session_context_menu_verified.png"
                    with open(out_path, "wb") as f:
                        f.write(img_data)
                    print("Captured 3-dots context menu screenshot:", out_path)
                    break

    finally:
        p.terminate()

asyncio.run(test_session_menu())
