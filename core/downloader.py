"""
ModelDock Studio - Unified Resumable Model Downloader
Supports both Hugging Face Hub (HTTP Range chunked resume) and Ollama/xOllama models (layer-blob resume).
Provides true Pause, Resume, and Cancel functionality for all open-source models.
"""

import os
import time
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
import httpx
from core.config import ConfigManager
from core.auth_manager import AuthManager
from core.engine_manager import EngineManager

CURRENT_DIR = Path(__file__).resolve().parent.parent

# In-memory registry of active, paused, and completed download tasks
_DOWNLOAD_TASKS: Dict[str, Dict[str, Any]] = {}
_ABORT_EVENTS: Dict[str, asyncio.Event] = {}

POPULAR_MODEL_PULL_MAP: Dict[str, Dict[str, str]] = {
    "llama3.2:1b": {
        "url": "https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF/resolve/main/Llama-3.2-1B-Instruct-Q4_K_M.gguf",
        "filename": "Llama-3.2-1B-Instruct-Q4_K_M.gguf",
        "model_name": "llama3.2-1b-instruct",
    },
    "llama3.2:3b": {
        "url": "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        "filename": "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        "model_name": "llama3.2-3b-instruct",
    },
    "deepseek-r1:1.5b": {
        "url": "https://huggingface.co/unsloth/DeepSeek-R1-Distill-Qwen-1.5B-GGUF/resolve/main/DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf",
        "filename": "DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf",
        "model_name": "deepseek-r1-1.5b",
    },
    "deepseek-r1:7b": {
        "url": "https://huggingface.co/unsloth/DeepSeek-R1-Distill-Qwen-7B-GGUF/resolve/main/DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf",
        "filename": "DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf",
        "model_name": "deepseek-r1-7b",
    },
    "qwen2.5-coder:7b": {
        "url": "https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF/resolve/main/qwen2.5-coder-7b-instruct-q4_k_m.gguf",
        "filename": "qwen2.5-coder-7b-instruct-q4_k_m.gguf",
        "model_name": "qwen2.5-coder-7b",
    },
    "qwen2.5:0.5b": {
        "url": "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf",
        "filename": "qwen2.5-0.5b-instruct-q4_k_m.gguf",
        "model_name": "qwen2.5-0.5b",
    },
    "qwen2.5:1.5b": {
        "url": "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf",
        "filename": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
        "model_name": "qwen2.5-1.5b",
    },
    "qwen2.5:7b": {
        "url": "https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf",
        "filename": "qwen2.5-7b-instruct-q4_k_m.gguf",
        "model_name": "qwen2.5-7b",
    },
    "mistral:7b": {
        "url": "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
        "filename": "mistral-7b-instruct-v0.2.Q4_K_M.gguf",
        "model_name": "mistral-7b",
    },
    "mistral": {
        "url": "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
        "filename": "mistral-7b-instruct-v0.2.Q4_K_M.gguf",
        "model_name": "mistral-7b",
    },
    "phi4": {
        "url": "https://huggingface.co/microsoft/phi-4-gguf/resolve/main/phi-4-q4_k_m.gguf",
        "filename": "phi-4-q4_k_m.gguf",
        "model_name": "phi-4",
    },
}


class DownloadManager:
    def __init__(
        self,
        config: Optional[ConfigManager] = None,
        auth: Optional[AuthManager] = None,
        engine: Optional[EngineManager] = None,
    ):
        self.config = config or ConfigManager.get_instance()
        self.auth = auth or AuthManager()
        self.engine = engine or EngineManager(self.config)

    def get_tasks(self) -> Dict[str, Dict[str, Any]]:
        # Return tasks without internal asyncio events
        result = {}
        for tid, t in _DOWNLOAD_TASKS.items():
            task_copy = dict(t)
            task_copy.pop("_abort_event", None)
            result[tid] = task_copy
        return result

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        t = _DOWNLOAD_TASKS.get(task_id)
        if t:
            copy_t = dict(t)
            copy_t.pop("_abort_event", None)
            return copy_t
        return None

    def pause_task(self, task_id: str) -> bool:
        """Pause an ongoing download (Hugging Face or Ollama)."""
        task = _DOWNLOAD_TASKS.get(task_id)
        if not task or task.get("status") not in ["downloading", "queued"]:
            return False

        task["status"] = "pausing"
        event = _ABORT_EVENTS.get(task_id)
        if event:
            event.set()
        return True

    def resume_task(self, task_id: str) -> bool:
        """Resume a paused download seamlessly."""
        task = _DOWNLOAD_TASKS.get(task_id)
        if not task or task.get("status") not in ["paused", "pausing"]:
            return False

        task["status"] = "queued"
        task["error"] = None
        event = asyncio.Event()
        _ABORT_EVENTS[task_id] = event

        platform = task.get("platform", "huggingface")
        if platform == "huggingface":
            asyncio.create_task(self._hf_download_worker(task_id))
        elif platform == "ollama":
            asyncio.create_task(self._ollama_pull_worker(task_id))
        return True

    def cancel_task(self, task_id: str, delete_file: bool = True) -> bool:
        """Cancel a download and optionally delete temporary files."""
        task = _DOWNLOAD_TASKS.get(task_id)
        if not task:
            return False

        task["status"] = "cancelled"
        event = _ABORT_EVENTS.get(task_id)
        if event:
            event.set()

        if delete_file and task.get("file_path"):
            p = Path(task["file_path"])
            if p.is_file():
                try:
                    p.unlink(missing_ok=True)
                except Exception:
                    pass
        return True

    async def start_hf_download(
        self,
        url: str,
        filename: str,
        model_name: Optional[str] = None,
        auto_register: bool = True,
    ) -> str:
        """
        Start downloading a GGUF model from Hugging Face with HTTP Range resume support.
        """
        task_id = f"dl_hf_{int(time.time() * 1000)}"
        clean_name = filename.replace("/", "_").replace("\\", "_")
        target_dir = Path(self.config.get("downloads_dir"))
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / clean_name

        existing_bytes = target_path.stat().st_size if target_path.is_file() else 0

        task_info = {
            "task_id": task_id,
            "platform": "huggingface",
            "url": url,
            "filename": clean_name,
            "file_path": str(target_path),
            "model_name": model_name or clean_name.replace(".gguf", "").lower(),
            "auto_register": auto_register,
            "status": "queued",
            "progress_percent": 0.0,
            "downloaded_bytes": existing_bytes,
            "total_bytes": 0,
            "speed_mb_s": 0.0,
            "eta_seconds": 0,
            "error": None,
            "started_at": time.time(),
            "completed_at": None,
        }
        _DOWNLOAD_TASKS[task_id] = task_info
        _ABORT_EVENTS[task_id] = asyncio.Event()

        asyncio.create_task(self._hf_download_worker(task_id))
        return task_id

    async def start_ollama_pull(self, model_name: str) -> str:
        """
        Pull an open-source model natively into models/ using fast chunked GGUF download with resume support.
        """
        task_id = f"dl_ol_{int(time.time() * 1000)}"
        clean_model = model_name.strip().lower()

        mapped = POPULAR_MODEL_PULL_MAP.get(clean_model)
        if mapped:
            target_url = mapped["url"]
            filename = mapped["filename"]
            reg_name = mapped["model_name"]
        else:
            filename = f"{clean_model.replace(':', '-')}-q4_k_m.gguf"
            target_url = f"https://huggingface.co/bartowski/{clean_model.split(':')[0]}-GGUF/resolve/main/{filename}"
            reg_name = clean_model.replace(":", "-")

        models_dir = Path(self.config.get("models_dir", CURRENT_DIR / "models"))
        models_dir.mkdir(parents=True, exist_ok=True)
        target_path = models_dir / filename

        task_info = {
            "task_id": task_id,
            "platform": "ollama",
            "url": target_url,
            "filename": filename,
            "file_path": str(target_path),
            "model_name": clean_model,
            "auto_register": True,
            "status": "queued",
            "progress_percent": 0.0,
            "downloaded_bytes": 0,
            "total_bytes": 0,
            "speed_mb_s": 0.0,
            "eta_seconds": 0,
            "current_layer": f"Connecting to {filename}...",
            "error": None,
            "started_at": time.time(),
            "completed_at": None,
        }
        _DOWNLOAD_TASKS[task_id] = task_info
        _ABORT_EVENTS[task_id] = asyncio.Event()

        asyncio.create_task(self._hf_download_worker(task_id))
        return task_id

    async def _hf_download_worker(self, task_id: str) -> None:
        """Worker executing Hugging Face chunked download with Range support."""
        task = _DOWNLOAD_TASKS[task_id]
        abort_event = _ABORT_EVENTS[task_id]
        task["status"] = "downloading"

        url = task["url"]
        target_path = Path(task["file_path"])
        existing_bytes = target_path.stat().st_size if target_path.is_file() else 0

        headers = {
            "User-Agent": "ModelDock-Studio/1.0",
        }
        headers.update(self.auth.get_auth_headers())

        # If resuming from existing bytes, ask for Range
        if existing_bytes > 0:
            headers["Range"] = f"bytes={existing_bytes}-"

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(connect=15.0, read=60.0, write=60.0, pool=60.0),
                follow_redirects=True,
            ) as client:
                async with client.stream("GET", url, headers=headers) as response:
                    if response.status_code in [401, 403]:
                        task["status"] = "failed"
                        task["error"] = "Hugging Face Access Denied. Verify your HF Token in 'Auth & Keys'."
                        return
                    elif response.status_code not in [200, 206]:
                        task["status"] = "failed"
                        task["error"] = f"HTTP {response.status_code}: {response.reason_phrase}"
                        return

                    # Parse Total File Size
                    content_range = response.headers.get("content-range")
                    if content_range and "/" in content_range:
                        try:
                            total_bytes = int(content_range.split("/")[1])
                        except Exception:
                            total_bytes = task.get("total_bytes", 0)
                    else:
                        content_length = response.headers.get("content-length")
                        cl = int(content_length) if content_length else 0
                        total_bytes = cl + existing_bytes if response.status_code == 206 else cl

                    task["total_bytes"] = total_bytes

                    # Open file: "ab" if resuming (206), "wb" if fresh (200)
                    mode = "ab" if (response.status_code == 206 and existing_bytes > 0) else "wb"
                    if mode == "wb":
                        existing_bytes = 0
                        task["downloaded_bytes"] = 0

                    downloaded = existing_bytes
                    start_time = time.time()
                    last_update_time = start_time
                    bytes_in_interval = 0

                    with open(target_path, mode) as f:
                        async for chunk in response.aiter_bytes(chunk_size=1024 * 1024):  # 1MB chunks
                            # Check for pause / cancel
                            if abort_event.is_set():
                                if task["status"] == "pausing":
                                    task["status"] = "paused"
                                    task["speed_mb_s"] = 0.0
                                f.flush()
                                return

                            f.write(chunk)
                            downloaded += len(chunk)
                            bytes_in_interval += len(chunk)

                            now = time.time()
                            if now - last_update_time >= 0.4:
                                dt = now - last_update_time
                                speed = (bytes_in_interval / dt) / (1024 * 1024)
                                pct = round((downloaded / total_bytes * 100), 1) if total_bytes > 0 else 0.0
                                rem_bytes = max(0, total_bytes - downloaded)
                                eta = int(rem_bytes / (speed * 1024 * 1024)) if speed > 0 and total_bytes > 0 else 0

                                task["downloaded_bytes"] = downloaded
                                task["progress_percent"] = min(100.0, pct)
                                task["speed_mb_s"] = round(speed, 2)
                                task["eta_seconds"] = eta

                                last_update_time = now
                                bytes_in_interval = 0

            # Completed
            task["downloaded_bytes"] = downloaded
            task["progress_percent"] = 100.0
            task["speed_mb_s"] = 0.0
            task["eta_seconds"] = 0
            task["status"] = "completed"
            task["completed_at"] = time.time()

            if task.get("auto_register"):
                await self._auto_register_model(task)

        except Exception as e:
            if not abort_event.is_set():
                task["status"] = "failed"
                task["error"] = f"Download error: {str(e)}"

    async def _ollama_pull_worker(self, task_id: str) -> None:
        """Worker executing Ollama model pull with layer progress and pause/resume."""
        task = _DOWNLOAD_TASKS[task_id]
        abort_event = _ABORT_EVENTS[task_id]
        task["status"] = "downloading"

        model_name = task["model_name"]
        host = self.engine.get_host()
        url = f"{host}/api/pull"

        start_time = time.time()
        last_update_time = start_time
        bytes_prev = task.get("downloaded_bytes", 0)

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(connect=15.0, read=120.0, write=15.0, pool=15.0)) as client:
                async with client.stream("POST", url, json={"name": model_name, "stream": True}) as response:
                    if response.status_code != 200:
                        task["status"] = "failed"
                        task["error"] = f"Ollama engine returned status {response.status_code}: {await response.aread()}"
                        return

                    async for line in response.aiter_lines():
                        if abort_event.is_set():
                            if task["status"] == "pausing":
                                task["status"] = "paused"
                                task["speed_mb_s"] = 0.0
                            return

                        if not line.strip():
                            continue

                        try:
                            data = json.loads(line)
                            status_str = data.get("status", "")
                            completed = data.get("completed", 0)
                            total = data.get("total", 0)

                            if total > 0:
                                task["total_bytes"] = total
                                task["downloaded_bytes"] = completed
                                pct = round((completed / total * 100), 1)
                                task["progress_percent"] = pct

                                now = time.time()
                                if now - last_update_time >= 0.5:
                                    dt = now - last_update_time
                                    bytes_diff = max(0, completed - bytes_prev)
                                    speed = (bytes_diff / dt) / (1024 * 1024)
                                    rem_bytes = max(0, total - completed)
                                    eta = int(rem_bytes / (speed * 1024 * 1024)) if speed > 0 else 0

                                    task["speed_mb_s"] = round(speed, 2)
                                    task["eta_seconds"] = eta
                                    last_update_time = now
                                    bytes_prev = completed

                            task["current_layer"] = status_str

                            if status_str == "success":
                                task["status"] = "ready"
                                task["progress_percent"] = 100.0
                                task["speed_mb_s"] = 0.0
                                task["message"] = f"Model '{model_name}' successfully pulled and ready to run!"
                                task["completed_at"] = time.time()
                                return

                        except Exception:
                            continue

            # Stream finished
            task["status"] = "ready"
            task["progress_percent"] = 100.0
            task["message"] = f"Model '{model_name}' ready in Ollama library."
            task["completed_at"] = time.time()

        except Exception as e:
            if not abort_event.is_set():
                task["status"] = "failed"
                task["error"] = f"Ollama pull error: {str(e)}"

    async def _auto_register_model(self, task: Dict[str, Any]) -> None:
        """Mark downloaded GGUF model as ready in the native engine library."""
        model_name = task.get("model_name")
        file_path = task.get("file_path")
        if model_name and file_path and os.path.isfile(file_path):
            task["status"] = "ready"
            task["message"] = f"Model '{model_name}' downloaded and ready to run in Native Engine!"
