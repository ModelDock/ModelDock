import httpx
from pathlib import Path

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

url = "https://huggingface.co/HuggingFaceTB/SmolLM-135M-Instruct-GGUF/resolve/main/smollm-135m-instruct-q4_k_m.gguf"
dest = MODELS_DIR / "smollm-135m-instruct-q4_k_m.gguf"

if not dest.is_file() or dest.stat().st_size < 1000000:
    print(f"Downloading test model {dest.name} (~90 MB)...")
    with httpx.stream("GET", url, follow_redirects=True) as stream:
        total = int(stream.headers.get("content-length", 0))
        downloaded = 0
        with open(dest, "wb") as f:
            for chunk in stream.iter_bytes(chunk_size=1024 * 1024):
                f.write(chunk)
                downloaded += len(chunk)
                if downloaded % (10 * 1024 * 1024) < 1024 * 1024:
                    print(f"Progress: {downloaded / 1024 / 1024:.1f} MB / {total / 1024 / 1024:.1f} MB")
    print("Download complete:", dest)
else:
    print("Model already exists:", dest)
