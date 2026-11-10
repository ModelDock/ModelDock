import asyncio
import json
import subprocess
import urllib.request
import websockets
import base64

async def test_edit_and_submit():
    p = subprocess.Popen([
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "--headless=new",
        "--remote-debugging-port=9225",
        "--window-size=1400,900",
        "http://127.0.0.1:7860"
    ])
    await asyncio.sleep(2.5)
    try:
        targets_raw = urllib.request.urlopen("http://127.0.0.1:9225/json").read()
        targets = json.loads(targets_raw)
        target = next(t for t in targets if t.get("type") == "page")
        async with websockets.connect(target['webSocketDebuggerUrl']) as ws:
            # 1. Switch to chat tab
            await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': 'switchTab("chat")'}}))
            await asyncio.sleep(1.0)

            # 2. Select valid model qwen2-0_5b-instruct-q4_k_m
            await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': '''
                (function() {
                    const sel = document.getElementById("chat-model-select");
                    if (sel) {
                        sel.value = "qwen2-0_5b-instruct-q4_k_m";
                    }
                    const input = document.getElementById("user-input");
                    if (input) {
                        input.value = "write python code for adding 2 numbers";
                    }
                    const sendBtn = document.getElementById("btn-send");
                    if (sendBtn) sendBtn.click();
                    return "sent_first_prompt";
                })()
            ''', 'returnByValue': True}}))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 2:
                    print("Step 1:", data['result']['result']['value'])
                    break

            # 3. Wait for assistant to finish answering the first prompt
            print("Waiting for first prompt to generate...")
            await asyncio.sleep(7.0)

            # 4. Click the Edit button on the first user message
            await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': '''
                (function() {
                    const editBtn = document.querySelector(".btn-msg-edit");
                    if (editBtn) {
                        editBtn.click();
                        return "clicked_edit_button";
                    }
                    return "no_edit_button_found";
                })()
            ''', 'returnByValue': True}}))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 3:
                    print("Step 2:", data['result']['result']['value'])
                    break

            await asyncio.sleep(1.0)

            # 5. Type "do same using cobol" and click "Save & Submit"
            await ws.send(json.dumps({'id': 4, 'method': 'Runtime.evaluate', 'params': {'expression': '''
                (function() {
                    const textarea = document.querySelector(".inline-edit-textarea");
                    const submitBtn = document.querySelector(".btn-inline-submit");
                    if (textarea && submitBtn) {
                        textarea.value = "do same using cobol";
                        submitBtn.click();
                        return "clicked_save_and_submit";
                    }
                    return "missing_elements";
                })()
            ''', 'returnByValue': True}}))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 4:
                    print("Step 3:", data['result']['result']['value'])
                    break

            # 6. Wait for model to generate response to the edited prompt
            print("Waiting for model to generate response for edited prompt...")
            await asyncio.sleep(7.0)

            # 7. Check message rows
            await ws.send(json.dumps({'id': 5, 'method': 'Runtime.evaluate', 'params': {'expression': '''
                (function() {
                    return Array.from(document.querySelectorAll(".chat-message-row")).map(r => ({
                        role: r.classList.contains("user-message-row") ? "user" : "assistant",
                        text: r.innerText.substring(0, 150).replace(/\\n/g, " ")
                    }));
                })()
            ''', 'returnByValue': True}}))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 5:
                    msgs = data['result']['result']['value']
                    print("\nMessages in chat after Save & Submit:")
                    for idx, m in enumerate(msgs):
                        print(f"[{idx}] {m['role']}: {m['text']}")
                    break

            # 8. Capture screenshot
            await ws.send(json.dumps({'id': 6, 'method': 'Page.captureScreenshot', 'params': {'format': 'png'}}))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 6:
                    img_data = base64.b64decode(data['result']['data'])
                    out_path = r"C:\Users\sshee\.gemini\antigravity\brain\0b4a2b11-3c48-4ba0-81ff-eee15c0ec9f9\save_and_submit_worked_verified.png"
                    with open(out_path, "wb") as f:
                        f.write(img_data)
                    print(f"\nCaptured verified screenshot to {out_path}")
                    break

    finally:
        p.terminate()

asyncio.run(test_edit_and_submit())
