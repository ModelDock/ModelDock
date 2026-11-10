import asyncio
import json
import urllib.request
import websockets
import subprocess

async def inspect():
    p = subprocess.Popen([
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "--headless=new",
        "--remote-debugging-port=9222",
        "http://localhost:7860"
    ])
    await asyncio.sleep(2.0)
    try:
        targets_raw = urllib.request.urlopen("http://localhost:9222/json").read()
        targets = json.loads(targets_raw)
        target = next(t for t in targets if t.get("type") == "page")
        async with websockets.connect(target['webSocketDebuggerUrl']) as ws:
            await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': 'switchTab("downloads")'}}))
            await asyncio.sleep(1.0)
            await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': 'document.getElementById("downloads-list").innerHTML'}}))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 2:
                    print('HTML:\n', data['result']['result']['value'].encode('ascii', 'replace').decode())
                    break
            await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': 'document.querySelector("[data-tab=\'downloads\']").outerHTML'}}))
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get('id') == 3:
                    print('NAV TAB:\n', data['result']['result']['value'])
                    break
    finally:
        p.terminate()

asyncio.run(inspect())
