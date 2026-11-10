import asyncio
import json
import subprocess
import urllib.request
import websockets
import base64
import os

ARTIFACT_DIR = r"C:\Users\sshee\.gemini\antigravity\brain\0b4a2b11-3c48-4ba0-81ff-eee15c0ec9f9"

async def test_ui_multimodal():
    print("Launching Edge headless...")
    p = subprocess.Popen([
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "--headless=new",
        "--remote-debugging-port=9238",
        "--window-size=1400,900",
        "http://127.0.0.1:7860"
    ])
    await asyncio.sleep(2.5)

    try:
        targets_raw = urllib.request.urlopen("http://127.0.0.1:9238/json").read()
        targets = json.loads(targets_raw)
        target = next(t for t in targets if t.get("type") == "page" and "7860" in t.get("url", ""))

        async with websockets.connect(target['webSocketDebuggerUrl']) as ws:
            # 1. Switch to chat tab
            await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': 'switchTab("chat")'}}))
            await asyncio.sleep(0.8)

            # 2. Select z-image-turbo-Q4_K_M model in dropdown
            await ws.send(json.dumps({
                'id': 2,
                'method': 'Runtime.evaluate',
                'params': {
                    'expression': '''
                        (function() {
                            const select = document.getElementById("chat-model-select");
                            if (!select) return "no_select";
                            for (let opt of select.options) {
                                if (opt.value.includes("z-image") || opt.text.includes("Z-Image")) {
                                    select.value = opt.value;
                                    select.dispatchEvent(new Event("change", { bubbles: true }));
                                    return "selected_" + opt.value;
                                }
                            }
                            return "option_not_found";
                        })()
                    ''',
                    'returnByValue': True
                }
            }))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 2:
                    print("Model select result:", data['result']['result']['value'])
                    break

            await asyncio.sleep(0.5)

            # 3. Test Image Generation: "can you create image for me"
            await ws.send(json.dumps({
                'id': 3,
                'method': 'Runtime.evaluate',
                'params': {
                    'expression': '''
                        (function() {
                            createNewSession();
                            const input = document.getElementById("user-input");
                            input.value = "can you create image for me";
                            document.getElementById("btn-send").click();
                            return "image_query_sent";
                        })()
                    ''',
                    'returnByValue': True
                }
            }))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 3:
                    print("Image send result:", data['result']['result']['value'])
                    break

            print("Waiting for Image render...")
            for i in range(15):
                await asyncio.sleep(1.0)
                await ws.send(json.dumps({
                    'id': 100 + i,
                    'method': 'Runtime.evaluate',
                    'params': {
                        'expression': '''
                            (function() {
                                const btnStop = document.getElementById("btn-stop");
                                const isStreaming = btnStop && !btnStop.classList.contains("hidden");
                                const card = document.querySelector(".ai-image-card");
                                const svg = document.querySelector(".ai-image-canvas svg");
                                return {
                                    isStreaming: isStreaming,
                                    cardFound: !!card,
                                    svgFound: !!svg
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
                        print(f"Image status [{i}s]:", status)
                        if not status['isStreaming'] and status['cardFound'] and status['svgFound']:
                            break
                        break
                if not status['isStreaming'] and status['cardFound'] and status['svgFound']:
                    break

            await asyncio.sleep(0.5)

            # 4. Capture screenshot of Image Generation
            await ws.send(json.dumps({'id': 200, 'method': 'Page.captureScreenshot', 'params': {'format': 'png'}}))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 200:
                    img_data = base64.b64decode(data['result']['data'])
                    out_path = os.path.join(ARTIFACT_DIR, "image_generation_verified.png")
                    with open(out_path, "wb") as f:
                        f.write(img_data)
                    print(f"Saved Image Generation screenshot to: {out_path}")
                    break

            # 5. Test Video Generation: "can you create video for me"
            await ws.send(json.dumps({
                'id': 300,
                'method': 'Runtime.evaluate',
                'params': {
                    'expression': '''
                        (function() {
                            createNewSession();
                            const input = document.getElementById("user-input");
                            input.value = "can you create video for me";
                            document.getElementById("btn-send").click();
                            return "video_query_sent";
                        })()
                    ''',
                    'returnByValue': True
                }
            }))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 300:
                    print("Video send result:", data['result']['result']['value'])
                    break

            print("Waiting for Video render...")
            for i in range(15):
                await asyncio.sleep(1.0)
                await ws.send(json.dumps({
                    'id': 400 + i,
                    'method': 'Runtime.evaluate',
                    'params': {
                        'expression': '''
                            (function() {
                                const btnStop = document.getElementById("btn-stop");
                                const isStreaming = btnStop && !btnStop.classList.contains("hidden");
                                const vCard = document.querySelector(".ai-video-card");
                                const vSvg = document.querySelector(".ai-video-viewport svg");
                                return {
                                    isStreaming: isStreaming,
                                    cardFound: !!vCard,
                                    svgFound: !!vSvg
                                };
                            })()
                        ''',
                        'returnByValue': True
                    }
                }))
                while True:
                    msg = await ws.recv()
                    data = json.loads(msg)
                    if data.get('id') == 400 + i:
                        status = data['result']['result']['value']
                        print(f"Video status [{i}s]:", status)
                        if not status['isStreaming'] and status['cardFound'] and status['svgFound']:
                            break
                        break
                if not status['isStreaming'] and status['cardFound'] and status['svgFound']:
                    break

            await asyncio.sleep(0.5)

            # 6. Capture screenshot of Video Generation
            await ws.send(json.dumps({'id': 500, 'method': 'Page.captureScreenshot', 'params': {'format': 'png'}}))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 500:
                    img_data = base64.b64decode(data['result']['data'])
                    out_path = os.path.join(ARTIFACT_DIR, "video_generation_verified.png")
                    with open(out_path, "wb") as f:
                        f.write(img_data)
                    print(f"Saved Video Generation screenshot to: {out_path}")
                    break

    finally:
        p.terminate()
        p.kill()

if __name__ == "__main__":
    asyncio.run(test_ui_multimodal())
