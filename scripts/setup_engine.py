import httpx
import zipfile
from pathlib import Path

BIN_DIR = Path(__file__).resolve().parent.parent / "bin"
BIN_DIR.mkdir(parents=True, exist_ok=True)

print("Fetching latest releases from ggml-org/llama.cpp...")
r = httpx.get("https://api.github.com/repos/ggml-org/llama.cpp/releases?per_page=10", follow_redirects=True)
releases = r.json()

target_release = None
for rel in releases:
    tag = rel.get("tag_name", "")
    if tag.startswith("b"):
        target_release = rel
        break

if not target_release:
    print("Could not find a build release starting with 'b'.")
    exit(1)

tag = target_release.get("tag_name")
print(f"Target release: {tag}")

assets = target_release.get("assets", [])
win_cpu_asset = None
win_cuda_asset = None
win_cudart_asset = None

for a in assets:
    name = a["name"].lower()
    if "bin-win-cpu-x64.zip" in name:
        win_cpu_asset = a
    elif "bin-win-cuda-12.4-x64.zip" in name:
        win_cuda_asset = a
    elif "cudart-llama-bin-win-cuda-12.4-x64.zip" in name:
        win_cudart_asset = a

print(f"CPU asset: {win_cpu_asset['name'] if win_cpu_asset else 'None'}")
print(f"CUDA asset: {win_cuda_asset['name'] if win_cuda_asset else 'None'}")
print(f"CUDART asset: {win_cudart_asset['name'] if win_cudart_asset else 'None'}")

# Download CPU asset first for 100% universal compatibility
chosen_assets = []
if win_cpu_asset:
    chosen_assets.append(win_cpu_asset)
if win_cuda_asset and win_cudart_asset:
    chosen_assets.extend([win_cudart_asset, win_cuda_asset])

for asset in chosen_assets:
    zip_path = BIN_DIR / asset["name"]
    print(f"Downloading {asset['name']} ({asset['size'] / 1024 / 1024:.1f} MB)...")
    with httpx.stream("GET", asset["browser_download_url"], follow_redirects=True) as stream:
        with open(zip_path, "wb") as f:
            for chunk in stream.iter_bytes(chunk_size=1024 * 1024):
                f.write(chunk)
    print("Extracting...")
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(BIN_DIR)
    zip_path.unlink()

print("\nEngine extraction complete!")
for p in BIN_DIR.glob("*.exe"):
    print(" - Found executable:", p.name)
