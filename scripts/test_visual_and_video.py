import urllib.request
import json
import time

def query_chat(model: str, user_prompt: str):
    url = "http://127.0.0.1:7860/api/chat"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": user_prompt}],
        "temperature": 0.7,
        "num_ctx": 4096
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    full = ""
    start = time.time()
    with urllib.request.urlopen(req, timeout=30) as resp:
        for line in resp:
            line_str = line.decode("utf-8").strip()
            if line_str.startswith("data: "):
                data = json.loads(line_str[6:])
                full += data.get("content", "")
    elapsed = time.time() - start
    return full, elapsed

print("--- Test 1: Image Generation with z-image-turbo-Q4_K_M ---")
resp1, t1 = query_chat("z-image-turbo-Q4_K_M", "can you create image for me")
print(f"Elapsed: {t1:.2f}s | Response length: {len(resp1)}")
print("Contains SVG Image Card:", "<svg" in resp1 and "</svg>" in resp1)
print("Contains Error Message:", "Model Load Error" in resp1)
print("Snippet:", resp1[:200] + "...")
print()

print("--- Test 2: Video Generation with z-image-turbo-Q4_K_M ---")
resp2, t2 = query_chat("z-image-turbo-Q4_K_M", "can you create video for me")
print(f"Elapsed: {t2:.2f}s | Response length: {len(resp2)}")
print("Contains AI Video Card:", "ai-video-card" in resp2)
print("Contains 60fps Cinema:", "60fps" in resp2)
print("Contains Error Message:", "Model Load Error" in resp2)
print("Snippet:", resp2[:200] + "...")
