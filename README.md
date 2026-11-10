# ⚓ ModelDock

<p align="center">
  <strong>Universal Local AI Docking Station & Native Windows Platform</strong><br>
  Run any open-source AI model locally on CPU & GPU. Connects Hugging Face Hub and Ollama under one roof with resumable downloads, hardware acceleration, and ultra-low RAM usage.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Windows_10%20%7C%2011-0078D6?logo=windows&logoColor=white" alt="Platform Windows" />
  <img src="https://img.shields.io/badge/Engine-Standalone_llama.cpp_(Zero_Daemon)-10b981?logo=cplusplus&logoColor=white" alt="Native Engine" />
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/RAM_Footprint-~35_MB-f59e0b" alt="Low RAM Footprint" />
  <img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="License Apache 2.0" />
</p>

---

## 🌟 Why ModelDock?

Most local AI software bundles heavy Chromium or Electron runtimes, consuming **600 MB to 1.5 GB of RAM** before you even load a model. Other tools force you into isolated ecosystems (either strictly Ollama or manual GGUF files).

**ModelDock bridges everything together into a unified, high-performance local docking station:**
- Run models from **both Hugging Face Hub and Ollama** in one place.
- **True Pause & Resume** for multi-gigabyte weight downloads.
- Uses **~95% less RAM (~35 MB)** by running native Windows WebView2 and an async backend.
- Bundles a native standalone `llama.cpp` inference engine—**zero external Ollama daemon required**.

---

## ✨ Features

- 🖥️ **Native Windows Desktop Experience:**  
  Installs cleanly with a custom desktop icon, Windows Start Menu shortcut, and standard Windows *Add/Remove Programs* registration.
- ⚡ **Ultra-Low Memory Footprint (~35 MB RAM):**  
  0.0% CPU when idle and leaves almost 100% of your system RAM and GPU VRAM free for model weights and inference.
- 🛡️ **Zero Daemon Dependency (Standalone Engine):**  
  Bundles native `llama.cpp` high-performance inference binaries (`bin/llama-server.exe`). Runs out-of-the-box without installing external services.
- ⏸️ **Resumable Downloads (True Pause & Resume):**
  - **Hugging Face Hub:** Streams GGUF weights via HTTP `Range` headers. Pause anytime without losing downloaded megabytes.
  - **Layered Pulls:** Layered chunk download resume with byte-level verification.
- 🤗 **Hugging Face Hub & Gated Models:**  
  Directly search HF models, inspect quantization tiers (`Q4_K_M`, `Q5_K_M`, `Q8_0`), and authenticate with your HF Access Token to download gated weights (Meta Llama 3.1/3.2, Mistral, Google Gemma 2).
- 💬 **Real-Time Streaming Chat & Playground:**  
  Token-by-token streaming, live performance metrics (tokens/second, TTFT, token counts), system prompt configuration, and syntax-highlighted code blocks with 1-click copy.
- 📁 **1-Click Local `.GGUF` Import:**  
  Already have models stored on your drive? Point ModelDock to any `.gguf` file to dock it instantly into your local catalog.
- 🌐 **OpenAI-Compatible Local API (`/v1`):**  
  Drop-in compatibility with **Cursor, VS Code Continue, OpenWebUI, Cline, LangChain, and AutoGen**.

---

## 🚀 Quick Start (1-Click Run)

### Method 1: Desktop Application (Recommended)
Double-click **`Launch-Desktop.bat`** (or run `Install.bat` to install shortcuts to your Desktop & Start Menu).

### Method 2: Web / Browser Interface
Double-click **`run.bat`** or run:
```bash
python run.py
```
ModelDock will launch and open your default browser at:  
👉 **`http://localhost:7860`**

---

## 💻 1-Click Installation into Windows

To permanently register ModelDock as an installed Windows app:
1. Double-click **`Install.bat`**.
2. The installer will:
   - Check and configure your Python dependencies.
   - Install to `%LocalAppData%\Programs\ModelDock`.
   - Add shortcuts to your **Desktop** and **Start Menu**.
   - Register ModelDock in Windows **Settings → Installed Apps**.

### Uninstallation
To remove, go to **Windows Settings → Installed Apps → ModelDock → Uninstall** or run `Uninstall.bat`.

---

## 🧠 Hardware Acceleration

ModelDock automatically detects your hardware and configures the optimal backend:
- **NVIDIA RTX GPUs (CUDA):** Automatically offloads transformer matrix layers to VRAM for high-speed token generation.
- **CPU Multi-Threading:** Automated multi-core fallback if no dedicated GPU is detected.

---

## 📖 How It Works

### 1. Download Any Model (Hugging Face or Ollama)
Navigate to the **Hub** tab:
- **Hugging Face:** Search any repository (e.g. `meta-llama/Llama-3.2-3B-Instruct`), choose your GGUF quantization (e.g. `Q4_K_M`), and hit **Download**.
- **Ollama Models:** Enter any model tag (e.g., `mistral:latest`, `qwen2.5:7b`) to pull.
- Use the **Pause** and **Resume** buttons anytime in the Downloads tab.

### 2. Connect Your Hugging Face Token (Optional)
To access gated models like official Llama 3:
1. Open **Settings → Auth & Keys**.
2. Paste your Access Token (`hf_...`) from [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens).
3. Click **Verify & Save**.

### 3. Connect External Tools (OpenAI-Compatible API)
You can use ModelDock as a local backend for developer tools:
- **Base URL:** `http://localhost:7860/v1`
- **API Key:** `none` (or any dummy value)
- **Model:** Enter any loaded model name

Example with Python:
```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:7860/v1",
    api_key="none"
)

response = client.chat.completions.create(
    model="local-model",
    messages=[{"role": "user", "content": "Explain quantum computing in one sentence."}]
)

print(response.choices[0].message.content)
```

---

## 🗂️ Repository Structure

```text
ModelDock/
├── run.bat                     # 1-Click Windows Launcher
├── Launch-Desktop.bat          # Native Desktop Window Launcher
├── Install.bat                 # Windows App Installer
├── run.py                      # FastAPI server & OpenAI-compatible routes
├── desktop_app.py              # Microsoft Edge WebView2 native app wrapper
├── config.json                 # Persistent local configuration
├── bin/                        # Bundled native llama.cpp standalone binaries
├── core/
│   ├── auth_manager.py         # Hugging Face auth & gated model access
│   ├── downloader.py           # Resumable chunked downloader (HF & Ollama)
│   ├── engine_manager.py       # Standalone native engine controller
│   ├── gguf_parser.py          # Native GGUF metadata & architecture parser
│   ├── hf_hub.py               # Hugging Face Hub live search & inspector
│   ├── model_runner.py         # Streaming inference & generation metrics
│   └── system_monitor.py       # Real-time RAM, CPU & GPU VRAM telemetry
├── static/
│   ├── index.html              # Clean dark-mode dashboard
│   ├── css/style.css           # Glassmorphic UI stylesheet
│   └── js/                     # Modular frontend controllers
└── tests/
    └── test_core.py            # Automated test suite
```

---

## 🧪 Running Tests

Validate your local environment and API routes with pytest:
```bash
python -m pytest -v tests/test_core.py
```

---

## 📄 License

This project is licensed under the [Apache 2.0 License](LICENSE).
