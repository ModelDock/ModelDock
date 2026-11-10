import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_URL = "http://127.0.0.1:7860"

def test_endpoint(name, path, method="GET", data=None, headers=None):
    url = f"{BASE_URL}{path}"
    req_headers = headers or {}
    req_data = None
    if data:
        if isinstance(data, dict):
            req_data = json.dumps(data).encode("utf-8")
            req_headers["Content-Type"] = "application/json"
        elif isinstance(data, bytes):
            req_data = data

    req = urllib.request.Request(url, data=req_data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read()
            status = resp.status
            content_type = resp.headers.get("Content-Type", "")
            return {
                "name": name,
                "url": url,
                "status": status,
                "ok": 200 <= status < 300,
                "size": len(body),
                "content_type": content_type,
                "body_preview": body[:120].decode("utf-8", errors="replace"),
                "json": json.loads(body) if "application/json" in content_type else None,
            }
    except urllib.error.HTTPError as e:
        return {"name": name, "url": url, "status": e.code, "ok": False, "error": str(e)}
    except Exception as e:
        return {"name": name, "url": url, "status": 0, "ok": False, "error": str(e)}

results = []

# 1. Web UI & Root
results.append(test_endpoint("Root HTML (/)", "/"))
results.append(test_endpoint("Static HTML (/static/index.html)", "/static/index.html"))

# 2. Static Assets
results.append(test_endpoint("Vector Logo SVG (/static/logo.svg)", "/static/logo.svg"))
results.append(test_endpoint("Fallback Logo PNG (/static/logo.png)", "/static/logo.png"))
results.append(test_endpoint("Stylesheet CSS (/static/css/style.css)", "/static/css/style.css"))
results.append(test_endpoint("App Controller JS (/static/js/app.js)", "/static/js/app.js"))
results.append(test_endpoint("Chat Playground JS (/static/js/chat.js)", "/static/js/chat.js"))
results.append(test_endpoint("Explore Hub JS (/static/js/hf_hub.js)", "/static/js/hf_hub.js"))
results.append(test_endpoint("Settings Manager JS (/static/js/settings.js)", "/static/js/settings.js"))

# 3. System Telemetry & Monitor
results.append(test_endpoint("System Telemetry (/api/system/status)", "/api/system/status"))

# 4. Model Library & Downloads
results.append(test_endpoint("Local Model Library (/api/models)", "/api/models"))
results.append(test_endpoint("Popular Pulls (/api/models/popular)", "/api/models/popular"))
results.append(test_endpoint("Active Downloads (/api/downloads)", "/api/downloads"))

# 5. Explore Hub Search
results.append(test_endpoint("Featured Models (/api/hf/featured)", "/api/hf/featured"))
results.append(test_endpoint("Search Models (/api/hf/search?q=qwen)", "/api/hf/search?q=qwen"))

# 6. Auth Status
results.append(test_endpoint("Auth Status (/api/auth/status)", "/api/auth/status"))

# 7. Settings Configuration & Navigation Switcher
results.append(test_endpoint("Get Settings (/api/settings)", "/api/settings"))
results.append(test_endpoint("Update Nav Position (POST /api/settings/update)", "/api/settings/update", method="POST", data={"nav_position": "left"}))
results.append(test_endpoint("Persistent Chat Storage (GET /api/chats)", "/api/chats"))

# 8. Multimodal Upload
boundary = "----WebKitFormBoundaryOmniTest12345"
multipart_body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="files"; filename="sample_data.csv"\r\n'
    f"Content-Type: text/csv\r\n\r\n"
    f"id,name,role,score\n1,Alice,AI Engineer,98\n2,Bob,Researcher,95\r\n"
    f"--{boundary}--\r\n"
).encode("utf-8")

results.append(test_endpoint(
    "Multimodal CSV Upload (POST /api/media/upload)",
    "/api/media/upload",
    method="POST",
    data=multipart_body,
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
))

print("\n" + "=" * 75)
print("       ModelDock Studio - Comprehensive Feature Audit Results")
print("=" * 75)

all_passed = True
for r in results:
    status_icon = "[PASS]" if r.get("ok") else "[FAIL]"
    size_str = f"({r.get('size')} bytes)" if r.get("size") else ""
    print(f" {status_icon} [{r.get('status')}] {r['name']:<42} {size_str}")
    if not r.get("ok"):
        all_passed = False
        print(f"    ERROR: {r.get('error')}")

print("=" * 75)
if all_passed:
    print("ALL FEATURES & ENDPOINTS OPERATIONAL (100% PASS)")
else:
    print("SOME ENDPOINTS FAILED")
print("=" * 75 + "\n")
