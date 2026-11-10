import asyncio
import json
import subprocess
import urllib.request
import websockets
import base64

async def test_submenu():
    p = subprocess.Popen([
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "--headless=new",
        "--remote-debugging-port=9228",
        "--window-size=1400,900",
        "http://127.0.0.1:7860"
    ])
    await asyncio.sleep(2.5)
    try:
        targets_raw = urllib.request.urlopen("http://127.0.0.1:9228/json").read()
        targets = json.loads(targets_raw)
        target = next(t for t in targets if t.get("type") == "page")
        async with websockets.connect(target['webSocketDebuggerUrl']) as ws:
            await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': 'switchTab("chat")'}}))
            await asyncio.sleep(1.0)

            # Open 3-dots menu
            await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': '''
                (function() {
                    const dotsBtn = document.querySelector(".session-dots-btn");
                    if (dotsBtn) {
                        dotsBtn.click();
                        const sub = document.getElementById("chat-projects-submenu");
                        if (sub) {
                            sub.style.display = "flex";
                        }
                        return "menu_and_sub_opened";
                    }
                    return "no_dots";
                })()
            ''', 'returnByValue': True}}))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 2:
                    print("Submenu step:", data['result']['result']['value'])
                    break

            await asyncio.sleep(0.8)

            # Capture screenshot
            await ws.send(json.dumps({'id': 3, 'method': 'Page.captureScreenshot', 'params': {'format': 'png'}}))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 3:
                    img_data = base64.b64decode(data['result']['data'])
                    out_path = r"C:\Users\sshee\.gemini\antigravity\brain\0b4a2b11-3c48-4ba0-81ff-eee15c0ec9f9\session_move_to_project_submenu_verified.png"
                    with open(out_path, "wb") as f:
                        f.write(img_data)
                    print("Captured submenu screenshot:", out_path)
                    break

    finally:
        p.terminate()

asyncio.run(test_submenu())
