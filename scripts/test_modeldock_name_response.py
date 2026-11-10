import urllib.request
import json
import time

url = "http://127.0.0.1:7860/api/chat"
payload = {
    "model": "qwen2-0_5b-instruct-q4_k_m",
    "messages": [
        {"role": "user", "content": "Hii, what is your name"}
    ],
    "temperature": 0.7,
    "num_ctx": 4096
}

req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

print("Sending request to /api/chat...")
start = time.time()
full_response = ""
with urllib.request.urlopen(req, timeout=30) as resp:
    for line in resp:
        line_str = line.decode("utf-8").strip()
        if line_str.startswith("data: "):
            chunk_data = line_str[6:].strip()
            if chunk_data and chunk_data != "[DONE]":
                try:
                    parsed = json.loads(chunk_data)
                    token = parsed.get("token", "")
                    full_response += token
                except Exception:
                    pass

elapsed = time.time() - start
print(f"Elapsed: {elapsed:.2f}s")
print("Response from model:")
print("=" * 50)
print(full_response)
print("=" * 50)
