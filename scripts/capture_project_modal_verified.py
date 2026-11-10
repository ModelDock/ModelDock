import asyncio
import json
import subprocess
import urllib.request
import websockets
import base64

async def capture_modal_screenshots():
    p = subprocess.Popen([
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "--headless=new",
        "--remote-debugging-port=9226",
        "--window-size=1400,900",
        "http://127.0.0.1:7860"
    ])
    await asyncio.sleep(2.5)
    try:
        targets_raw = urllib.request.urlopen("http://127.0.0.1:9226/json").read()
        targets = json.loads(targets_raw)
        target = next(t for t in targets if t.get("type") == "page")
        async with websockets.connect(target['webSocketDebuggerUrl']) as ws:
            # 1. Open New Project Modal
            await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': 'openNewProjectModal()'}}))
            await asyncio.sleep(1.2)

            # Capture "Create New Project" Modal
            await ws.send(json.dumps({'id': 2, 'method': 'Page.captureScreenshot', 'params': {'format': 'png'}}))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 2:
                    img_data = base64.b64decode(data['result']['data'])
                    out_path = r"C:\Users\sshee\.gemini\antigravity\brain\0b4a2b11-3c48-4ba0-81ff-eee15c0ec9f9\create_new_project_modal_verified.png"
                    with open(out_path, "wb") as f:
                        f.write(img_data)
                    print("Captured Create New Project modal:", out_path)
                    break

            # 2. Fill fields to simulate "Project Settings: Code & Analysis Workspace"
            await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': '''
                (function() {
                    document.getElementById("modal-project-title").textContent = "Project Settings: Code & Analysis Workspace";
                    document.getElementById("project-form-id").value = "proj_test_123";
                    document.getElementById("project-form-name").value = "Code & Analysis Workspace";
                    document.getElementById("project-form-desc").value = "Project workspace for software engineering & AI development";
                    document.getElementById("project-form-instructions").value = "You are an expert technical AI assistant. Deliver concise, well-architected solutions with unit tests and production standards.";
                    const delBtn = document.getElementById("btn-delete-project");
                    if (delBtn) delBtn.classList.remove("hidden");
                })()
            '''}}))
            await asyncio.sleep(0.8)

            # Capture "Project Settings" Modal
            await ws.send(json.dumps({'id': 4, 'method': 'Page.captureScreenshot', 'params': {'format': 'png'}}))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 4:
                    img_data = base64.b64decode(data['result']['data'])
                    out_path = r"C:\Users\sshee\.gemini\antigravity\brain\0b4a2b11-3c48-4ba0-81ff-eee15c0ec9f9\project_settings_modal_verified.png"
                    with open(out_path, "wb") as f:
                        f.write(img_data)
                    print("Captured Project Settings modal:", out_path)
                    break

    finally:
        p.terminate()

asyncio.run(capture_modal_screenshots())
