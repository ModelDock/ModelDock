import asyncio
import json
import subprocess
import urllib.request
import websockets
import base64
import os

ARTIFACT_DIR = r"C:\Users\sshee\.gemini\antigravity\brain\0b4a2b11-3c48-4ba0-81ff-eee15c0ec9f9"

async def test_chat_name():
    print("Launching Edge headless...")
    p = subprocess.Popen([
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "--headless=new",
        "--remote-debugging-port=9235",
        "--window-size=1400,900",
        "http://127.0.0.1:7860"
    ])
    await asyncio.sleep(2.5)

    try:
        targets_raw = urllib.request.urlopen("http://127.0.0.1:9235/json").read()
        targets = json.loads(targets_raw)
        target = next(t for t in targets if t.get("type") == "page" and "7860" in t.get("url", ""))

        async with websockets.connect(target['webSocketDebuggerUrl']) as ws:
            # 1. Switch to chat tab & create new session
            await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': 'switchTab("chat")'}}))
            await asyncio.sleep(0.8)

            # 2. Type "Hii, what is your name" into user input and send
            await ws.send(json.dumps({
                'id': 2,
                'method': 'Runtime.evaluate',
                'params': {
                    'expression': '''
                        (function() {
                            if (typeof createNewSession === "function") {
                                createNewSession();
                            }
                            const input = document.getElementById("user-input");
                            if (!input) return "no_input";
                            input.value = "Hii, what is your name";
                            const btnSend = document.getElementById("btn-send");
                            if (btnSend) {
                                btnSend.click();
                                return "sent";
                            }
                            return "no_send_btn";
                        })()
                    ''',
                    'returnByValue': True
                }
            }))

            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 2:
                    print("Send result:", data['result']['result']['value'])
                    break

            # 3. Wait for model response to stream and complete
            print("Waiting for ModelDock response stream...")
            for i in range(20):
                await asyncio.sleep(1.0)
                await ws.send(json.dumps({
                    'id': 100 + i,
                    'method': 'Runtime.evaluate',
                    'params': {
                        'expression': '''
                            (function() {
                                const btnSend = document.getElementById("btn-send");
                                const btnStop = document.getElementById("btn-stop");
                                const msgs = document.querySelectorAll(".chat-message-ai");
                                const lastMsg = msgs.length > 0 ? msgs[msgs.length - 1].innerText : "";
                                const isStreaming = btnStop && !btnStop.classList.contains("hidden");
                                return {
                                    isStreaming: isStreaming,
                                    msgCount: msgs.length,
                                    lastMsgSnippet: lastMsg.substring(0, 120)
                                };
                            })()
                        ''',
                        'returnByValue': True
                    }
                }))
                while True:
                    msg = await ws.recv()
                    data = json.loads(msg)
                    if data.get('id') == 100 + i:
                        status = data['result']['result']['value']
                        print(f"Status [{i}s]:", status)
                        if not status['isStreaming'] and status['msgCount'] > 0 and len(status['lastMsgSnippet']) > 10:
                            break
                        break
                if not status['isStreaming'] and status['msgCount'] > 0 and len(status['lastMsgSnippet']) > 10:
                    break

            await asyncio.sleep(0.5)

            # 4. Capture screenshot
            await ws.send(json.dumps({'id': 200, 'method': 'Page.captureScreenshot', 'params': {'format': 'png'}}))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 200:
                    img_data = base64.b64decode(data['result']['data'])
                    out_path = os.path.join(ARTIFACT_DIR, "modeldock_identity_response_verified.png")
                    with open(out_path, "wb") as f:
                        f.write(img_data)
                    print(f"Saved verified screenshot to: {out_path}")
                    break

    finally:
        p.terminate()
        p.kill()

if __name__ == "__main__":
    asyncio.run(test_chat_name())
