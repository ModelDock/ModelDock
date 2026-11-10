"""
ModelDock Studio - Configuration Manager
Ultra-lightweight JSON configuration handler with Hugging Face token discovery and engine defaults.
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional

CONFIG_FILE_PATH = Path(__file__).resolve().parent.parent / "config.json"
DEFAULT_DOWNLOADS_DIR = Path(__file__).resolve().parent.parent / "downloads"


def _discover_hf_token() -> Optional[str]:
    """Look for existing Hugging Face tokens in environment or Hugging Face CLI cache."""
    # 1. Environment variables
    for env_var in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN"):
        token = os.environ.get(env_var)
        if token and token.strip():
            return token.strip()
            
    # 2. Standard Hugging Face cache token location (~/.cache/huggingface/token or ~/.huggingface/token)
    hf_cache_paths = [
        Path.home() / ".cache" / "huggingface" / "token",
        Path.home() / ".huggingface" / "token",
    ]
    for path in hf_cache_paths:
        if path.is_file():
            try:
                token = path.read_text(encoding="utf-8").strip()
                if token:
                    return token
            except Exception:
                pass
    return None


def _discover_ollama_binary() -> Optional[str]:
    """Search for xollama or ollama executable in standard locations."""
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    candidates = [
        os.path.join(local_app_data, "Programs", "xOllama", "xollama.exe"),
        os.path.join(local_app_data, "Programs", "Ollama", "ollama.exe"),
        "C:\\Program Files\\Ollama\\ollama.exe",
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


class ConfigManager:
    _instance = None

    def __init__(self):
        self.config_path = CONFIG_FILE_PATH
        self.data: Dict[str, Any] = self._default_config()
        self.load()

    @classmethod
    def get_instance(cls) -> "ConfigManager":
        if cls._instance is None:
            cls._instance = ConfigManager()
        return cls._instance

    def _default_config(self) -> Dict[str, Any]:
        discovered_token = _discover_hf_token()
        discovered_binary = _discover_ollama_binary()
        
        # Default port check: xollama uses 22434 by default, standard ollama uses 11434
        default_ollama_host = "http://127.0.0.1:22434" if (discovered_binary and "xOllama" in discovered_binary) else "http://127.0.0.1:11434"
        root_dir = Path(__file__).resolve().parent.parent

        import multiprocessing
        total_cores = max(1, multiprocessing.cpu_count())
        recommended_threads = max(2, total_cores // 2)

        return {
            "hf_token": discovered_token or "",
            "hf_user": None,  # Cached HF user profile
            "ollama_host": default_ollama_host,
            "ollama_binary": discovered_binary or "",
            "models_dir": str(root_dir / "models"),
            "downloads_dir": str(DEFAULT_DOWNLOADS_DIR),
            "cpu_threads": recommended_threads,
            "gpu_mode": "auto",  # 'auto', 'cpu', or 'custom'
            "gpu_layers": 99,
            "server_host": "127.0.0.1",
            "server_port": 7860,
            "engine_port": 8089,
            "default_temperature": 0.7,
            "default_context_length": 4096,
            "system_prompt": "You are ModelDock, an intelligent, helpful local AI assistant running privately on local hardware. Your name is ModelDock. When the user asks what your name is or who you are, always state clearly: 'I am ModelDock, your local AI assistant.' Never call yourself generic 'AI' and never call the user ModelDock.",
            "auto_open_browser": True,
            "nav_position": "left",  # 'left' (default vertical dock), 'top' (header), 'right' (dock right), 'bottom'/'down' (bottom dock)
            "user_name": "Local AI User",
            "user_title": "Local AI • Pro",
        }

    def load(self) -> None:
        """Load configuration from disk."""
        if self.config_path.is_file():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self.data.update(loaded)
            except Exception:
                pass
        else:
            self.save()

        # Apply HF token to environment if present
        if self.data.get("hf_token"):
            os.environ["HF_TOKEN"] = self.data["hf_token"]
            os.environ["HUGGING_FACE_HUB_TOKEN"] = self.data["hf_token"]

        # Ensure download directory exists
        downloads_dir = Path(self.data.get("downloads_dir", str(DEFAULT_DOWNLOADS_DIR)))
        try:
            downloads_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    def save(self) -> None:
        """Save configuration to disk."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        if key == "nav_position" and isinstance(value, str):
            val_norm = value.lower().strip()
            if val_norm == "down":
                val_norm = "bottom"
            if val_norm in ["left", "top", "right", "bottom"]:
                value = val_norm
        self.data[key] = value
        if key == "hf_token":
            if value:
                os.environ["HF_TOKEN"] = str(value).strip()
                os.environ["HUGGING_FACE_HUB_TOKEN"] = str(value).strip()
            else:
                os.environ.pop("HF_TOKEN", None)
                os.environ.pop("HUGGING_FACE_HUB_TOKEN", None)
        self.save()

    def update_multiple(self, updates: Dict[str, Any]) -> None:
        for k, v in updates.items():
            self.set(k, v)
