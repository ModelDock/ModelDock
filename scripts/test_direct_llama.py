import sys, os
sys.path.insert(0, os.path.abspath("."))
import urllib.request
import json
from core.engine_manager import EngineManager

em = EngineManager()
host = em.get_host()

prompt = (
    "You are ModelDock, an intelligent, helpful local AI assistant running privately on local hardware. "
    "Your name is ModelDock. "
    "When the user asks what your name is or who you are, always state clearly: 'I am ModelDock, your local AI assistant.' "
    "Never call yourself generic 'AI' and never call the user ModelDock."
)

for query in ["Hii, what is your name", "who are you"]:
    payload = {
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": query}
        ],
        "stream": False,
        "temperature": 0.3
    }

    req = urllib.request.Request(
        f"{host}/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        print(f"Query: {query}")
        print("Response:", res["choices"][0]["message"]["content"])
        print("-" * 40)
