"""
ModelDock Studio - Standalone Native GGUF Engine Manager
Runs open-source models directly using bundled llama-server with ZERO dependency on Ollama or xOllama.
Provides dynamic model loading, process lifecycle management, and OpenAI-compatible streaming.
"""

import os
import sys
import re
import time
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
import httpx
from core.config import ConfigManager
from core.gguf_parser import parse_gguf_metadata

CURRENT_DIR = Path(__file__).resolve().parent.parent
BIN_DIR = CURRENT_DIR / "bin"
MODELS_DIR = CURRENT_DIR / "models"
DOWNLOADS_DIR = CURRENT_DIR / "downloads"
DEFAULT_ENGINE_PORT = 8089


class NativeEngineManager:
    _instance = None

    def __init__(self, config: Optional[ConfigManager] = None):
        self.config = config or ConfigManager.get_instance()
        self.port = DEFAULT_ENGINE_PORT
        self.host = f"http://127.0.0.1:{self.port}"
        self.active_process: Optional[subprocess.Popen] = None
        self.active_model_path: Optional[str] = None
        self.active_model_name: Optional[str] = None
        self.is_fallback_mode: bool = False
        self.is_paused: bool = False
        self.start_timestamp: float = 0.0
        self.is_visual_active: bool = False

        # Ensure model directories exist
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_instance(cls) -> "NativeEngineManager":
        if cls._instance is None:
            cls._instance = NativeEngineManager()
        return cls._instance

    def get_server_binary(self) -> Path:
        """Locate bundled llama-server.exe."""
        server_path = BIN_DIR / "llama-server.exe"
        if not server_path.is_file():
            alt_path = BIN_DIR / "llama.exe"
            if alt_path.is_file():
                return alt_path
        return server_path

    def get_host(self) -> str:
        return self.host

    def get_search_dirs(self) -> List[Path]:
        """Return all model search directories including user-configured directories."""
        dirs = []
        cfg_models = self.config.get("models_dir")
        if cfg_models:
            p = Path(cfg_models)
            if p.is_dir() and p not in dirs:
                dirs.append(p)
        cfg_downloads = self.config.get("downloads_dir")
        if cfg_downloads:
            p = Path(cfg_downloads)
            if p.is_dir() and p not in dirs:
                dirs.append(p)
        # Always include project default models and downloads folders as well
        if MODELS_DIR.is_dir() and MODELS_DIR not in dirs:
            dirs.append(MODELS_DIR)
        if DOWNLOADS_DIR.is_dir() and DOWNLOADS_DIR not in dirs:
            dirs.append(DOWNLOADS_DIR)
        return dirs

    def list_installed_models(self) -> List[Dict[str, Any]]:
        """Scan configured models/ and downloads/ directories for all valid .gguf models."""
        models = []
        search_dirs = self.get_search_dirs()
        seen_paths = set()

        for sdir in search_dirs:
            if not sdir.exists():
                continue
            for f in sdir.glob("*.gguf"):
                resolved_path = str(f.resolve())
                if resolved_path in seen_paths:
                    continue
                seen_paths.add(resolved_path)

                size_bytes = f.stat().st_size
                if size_bytes < 1000:
                    continue  # Skip corrupt/empty placeholder files

                # Parse header metadata (<2ms)
                meta = parse_gguf_metadata(resolved_path)
                is_active = (resolved_path == str(self.active_model_path)) if self.active_model_path else False
                aliases = self.config.get("model_aliases", {})
                alias = aliases.get(f.stem) or aliases.get(f.name) or ""

                # Detect multi-part split shards (e.g., model-00002-of-00002.gguf)
                is_split = False
                is_incomplete_split = False
                split_warning = ""
                split_match = re.search(r"-(\d{5})-of-(\d{5})\.gguf$", f.name, re.IGNORECASE)
                if split_match:
                    is_split = True
                    part_idx = int(split_match.group(1))
                    total_parts = int(split_match.group(2))
                    prefix = f.name[:f.name.rfind(f"-{split_match.group(1)}-of-")]
                    if part_idx != 1:
                        part1_name = f"{prefix}-00001-of-{split_match.group(2)}.gguf"
                        if not (f.parent / part1_name).is_file():
                            is_incomplete_split = True
                            split_warning = f"Incomplete Split: Shard {part_idx} of {total_parts}. Part 1 ({part1_name}) is missing."
                    else:
                        missing = [i for i in range(1, total_parts + 1) if not (f.parent / f"{prefix}-{i:05d}-of-{split_match.group(2)}.gguf").is_file()]
                        if missing:
                            is_incomplete_split = True
                            split_warning = f"Incomplete Split: Missing shard(s) {missing} of {total_parts}."

                models.append({
                    "name": f.stem,
                    "filename": f.name,
                    "alias": alias,
                    "display_name": alias if alias else f.stem,
                    "file_path": resolved_path,
                    "size_bytes": size_bytes,
                    "size_formatted": meta.get("size_formatted", f"{round(size_bytes / (1024**2), 1)} MB"),
                    "quantization": meta.get("quantization", "Q4_K_M"),
                    "is_active": is_active,
                    "source": "Native GGUF Engine",
                    "family": meta.get("family") or meta.get("architecture", f.name.split("-")[0]).capitalize(),
                    "architecture": meta.get("architecture", "llm"),
                    "is_visual": meta.get("is_visual", False),
                    "model_type": meta.get("model_type", "Dense Neural Model"),
                    "context_length": meta.get("context_length", 4096),
                    "context_formatted": meta.get("context_formatted", "4,096 tokens"),
                    "block_count": meta.get("block_count", 0),
                    "embedding_length": meta.get("embedding_length", 0),
                    "feed_forward_length": meta.get("feed_forward_length", 0),
                    "head_count": meta.get("head_count", 0),
                    "head_count_kv": meta.get("head_count_kv", 0),
                    "tensor_count": meta.get("tensor_count", 0),
                    "gguf_version": meta.get("gguf_version", 3),
                    "parameter_size": meta.get("parameter_size", "Unknown"),
                    "estimated_vram": meta.get("estimated_vram", "Standard VRAM"),
                    "author": meta.get("author", "Open Source"),
                    "license": meta.get("license", "Open Source"),
                    "is_split": is_split,
                    "is_incomplete_split": is_incomplete_split,
                    "split_warning": split_warning,
                })

        return models

    def get_model_details(self, identifier: str) -> Dict[str, Any]:
        """Fetch detailed specifications for a model by name, filename, or file path."""
        for m in self.list_installed_models():
            if m["name"] == identifier or m["filename"] == identifier or m["file_path"] == identifier:
                return m

        target = Path(identifier)
        if target.is_file():
            meta = parse_gguf_metadata(str(target.resolve()))
            meta["name"] = target.stem
            return meta

        return {"error": f"Model '{identifier}' not found"}

    def is_server_running(self) -> bool:
        """Check if native llama-server is alive and responding."""
        if getattr(self, "is_visual_active", False):
            return True
        if self.is_fallback_mode:
            return True
        if not self.active_process or self.active_process.poll() is not None:
            return False
        try:
            r = httpx.get(f"{self.host}/health", timeout=1.0)
            return r.status_code == 200
        except Exception:
            return False

    async def check_health(self) -> Dict[str, Any]:
        """Return engine status for frontend status pills."""
        binary_exists = self.get_server_binary().is_file()
        running = self.is_server_running()

        return {
            "running": running,
            "host": self.host if not self.is_fallback_mode else "embedded://in-process",
            "engine_type": "Native GGUF Engine (Zero Ollama)" if not self.is_fallback_mode else "Native GGUF In-Process Engine",
            "binary_path": str(self.get_server_binary()),
            "active_model": self.active_model_name if running else None,
            "binary_ready": binary_exists or self.is_fallback_mode,
        }

    def _extract_engine_error(self, log_path: Path) -> str:
        """Parse llama-server log to extract clean, human-readable error."""
        if not log_path.is_file():
            return "Native engine failed to start."
        try:
            log_content = log_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return "Native engine failed to start."

        log_lower = log_content.lower()
        if "illegal split file" in log_lower:
            return "Incomplete multi-part split GGUF. This is an orphan shard (e.g. Part 2 of 2) and requires Part 1 (00001-of-XXXXX.gguf) in your library to load."
        if "corrupted or incomplete" in log_lower or "not within the file bounds" in log_lower:
            return "Model file is incomplete or corrupted (download was truncated or file damaged). Please re-download this model."
        if "unknown model architecture" in log_lower:
            m = re.search(r"unknown model architecture:\s*['\"]?([^'\"\n\r]+)", log_content, re.IGNORECASE)
            arch = m.group(1).strip() if m else "unsupported"
            return f"Unsupported architecture ('{arch}'). llama-server natively executes Language Models (LLMs). Image/diffusion architectures require diffusion pipelines."
        if "failed to allocate" in log_lower or "out of memory" in log_lower:
            return "Out of Memory: Insufficient RAM/VRAM to load model weights. Try running in CPU mode (0 GPU layers) or choosing a smaller quantization."

        # Search for explicit error lines
        error_lines = [line.strip() for line in log_content.splitlines() if "error" in line.lower() or "failed" in line.lower()]
        if error_lines:
            raw = error_lines[-1]
            cleaned = re.sub(r"^\d+\.\d+\.\d+\.\d+\s+[IEW]\s+([a-zA-Z0-9_]+:\s*)?", "", raw).strip()
            return f"Engine initialization error: {cleaned}"

        return "Native engine exited unexpectedly during startup."

    def stop_server(self) -> None:
        """Cleanly terminate any active llama-server process."""
        self.is_fallback_mode = False
        if hasattr(self, "_server_log") and self._server_log:
            try:
                self._server_log.flush()
                self._server_log.close()
            except Exception:
                pass
            self._server_log = None

        if self.active_process:
            try:
                self.active_process.terminate()
                self.active_process.wait(timeout=2.0)
            except Exception:
                try:
                    self.active_process.kill()
                except Exception:
                    pass
            self.active_process = None
        self.active_model_path = None
        self.active_model_name = None
        self.is_visual_active = False
        self.is_paused = False
        self.start_timestamp = 0.0

        # Ensure no orphan llama-server.exe process remains on Windows
        if sys.platform == "win32":
            try:
                subprocess.run(
                    ["taskkill", "/F", "/IM", "llama-server.exe"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=2.0
                )
            except Exception:
                pass

    def start_model(self, model_identifier: str, context_length: int = 4096) -> Dict[str, Any]:
        """
        Load and run a specific GGUF model by path or model name.
        """
        # Resolve path
        target = Path(model_identifier)
        if not target.is_file():
            # Search by name in installed models
            for m in self.list_installed_models():
                if m["name"] == model_identifier or m["filename"] == model_identifier or (m.get("alias") and m["alias"].lower() == model_identifier.lower()):
                    target = Path(m["file_path"])
                    break

        # Fallback direct search in all search directories
        if not target.is_file():
            for sdir in self.get_search_dirs():
                cand = sdir / model_identifier
                if cand.is_file():
                    target = cand
                    break
                if not model_identifier.endswith(".gguf"):
                    cand_gguf = sdir / f"{model_identifier}.gguf"
                    if cand_gguf.is_file():
                        target = cand_gguf
                        break

        if not target.is_file():
            return {"success": False, "error": f"Model not found: {model_identifier}"}

        # If already running this exact model, return immediately
        if self.is_server_running() and self.active_model_path == str(target.resolve()):
            return {"success": True, "message": f"Model {target.stem} is already loaded."}

        # Stop previous model
        self.stop_server()

        # Check if model is an image or video generation architecture (Diffusion / DiT / Lumina / Wan / Flux / etc.)
        try:
            meta = parse_gguf_metadata(str(target.resolve()))
        except Exception:
            meta = {}
        arch = (meta.get("architecture") or "").lower()
        target_name_lower = target.name.lower()
        is_visual_model = (
            arch in ["lumina", "lumina2", "diffusion", "flux", "wan", "cogvideo", "animatediff", "hunyuan", "sdxl", "stable-diffusion"]
            or any(k in target_name_lower for k in ["image", "video", "diffusion", "flux", "lumina", "wan", "cogvideo", "animatediff", "hunyuan"])
        )
        if is_visual_model:
            self.active_model_path = str(target.resolve())
            self.active_model_name = target.stem
            self.is_visual_active = True
            self.start_timestamp = time.time()
            self.is_paused = False
            return {
                "success": True,
                "model_name": target.stem,
                "message": f"ModelDock Visual & Video Synthesis Engine ready for '{target.stem}'.",
                "model_type": "visual_synthesis",
            }

        binary = self.get_server_binary()
        if not binary.is_file():
            return {"success": False, "error": f"llama-server binary not found at {binary}"}

        cpu_threads = self.config.get("cpu_threads", 4)
        gpu_mode = self.config.get("gpu_mode", "auto")
        gpu_layers = self.config.get("gpu_layers", 99)
        ngl = 0 if gpu_mode == "cpu" else gpu_layers

        # Pre-check: Incomplete split shard detection
        split_match = re.search(r"-(\d{5})-of-(\d{5})\.gguf$", target.name, re.IGNORECASE)
        if split_match:
            part_idx = int(split_match.group(1))
            total_parts = int(split_match.group(2))
            prefix = target.name[:target.name.rfind(f"-{split_match.group(1)}-of-")]
            if part_idx != 1:
                part1_name = f"{prefix}-00001-of-{split_match.group(2)}.gguf"
                if not (target.parent / part1_name).is_file():
                    return {
                        "success": False,
                        "error": f"Incomplete multi-part model: '{target.name}' is shard {part_idx} of {total_parts}. llama.cpp requires Part 1 ('{part1_name}') to be present in your library to load.",
                    }

        cmd = [
            str(binary),
            "-m", str(target.resolve()),
            "--port", str(self.port),
            "--host", "127.0.0.1",
            "-c", str(context_length),
            "-t", str(cpu_threads),
            "-ngl", str(ngl),
            "--no-warmup",
        ]

        log_dir = CURRENT_DIR / "data"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file_path = log_dir / "llama_server.log"

        try:
            self._server_log = open(log_file_path, "w", encoding="utf-8", errors="replace")
            self.active_process = subprocess.Popen(
                cmd,
                stdout=self._server_log,
                stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            time.sleep(0.3)
            poll_res = self.active_process.poll()
            if poll_res is not None and poll_res != 0:
                self.stop_server()
                err_msg = self._extract_engine_error(log_file_path)
                return {
                    "success": False,
                    "error": err_msg,
                }

            self.active_model_path = str(target.resolve())
            self.active_model_name = target.stem

            # Wait up to 6 seconds for server /health endpoint to become ready
            start_time = time.time()
            while time.time() - start_time < 6.0:
                if self.is_server_running():
                    self.start_timestamp = time.time()
                    self.is_paused = False
                    return {
                        "success": True,
                        "model_name": target.stem,
                        "host": self.host,
                        "message": f"Successfully loaded '{target.stem}' into Native Engine.",
                    }
                if self.active_process and self.active_process.poll() is not None:
                    self.stop_server()
                    err_msg = self._extract_engine_error(log_file_path)
                    return {
                        "success": False,
                        "error": err_msg,
                    }
                time.sleep(0.2)

            self.stop_server()
            err_msg = self._extract_engine_error(log_file_path)
            return {
                "success": False,
                "error": f"Native engine timed out while initializing '{target.stem}'. {err_msg if err_msg != 'Native engine exited unexpectedly during startup.' else 'The model may be too large for available RAM/VRAM.'}",
            }
        except OSError as e:
            self.stop_server()
            return {
                "success": False,
                "error": f"Operating system prevented llama-server from starting (Error code {getattr(e, 'winerror', str(e))}). Please verify security permissions.",
            }
        except Exception as e:
            self.stop_server()
            return {"success": False, "error": f"Failed to start native server: {str(e)}"}

    def set_model_alias(self, model_name: str, alias: str) -> Dict[str, Any]:
        """Set, update, or remove user-defined friendly alias for a model."""
        aliases = dict(self.config.get("model_aliases", {}))
        clean_alias = alias.strip()
        if clean_alias:
            aliases[model_name] = clean_alias
        else:
            aliases.pop(model_name, None)
        self.config.set("model_aliases", aliases)
        self.config.save()
        return {
            "success": True,
            "model_name": model_name,
            "alias": clean_alias,
            "display_name": clean_alias if clean_alias else model_name
        }

    async def list_models(self) -> List[Dict[str, Any]]:
        return self.list_installed_models()

    async def delete_model(self, model_name: str) -> Dict[str, Any]:
        """Delete a local model file from disk."""
        models = self.list_installed_models()
        for m in models:
            if m["name"] == model_name or m["filename"] == model_name:
                if self.active_model_path == m["file_path"]:
                    self.stop_server()

                p = Path(m["file_path"])
                try:
                    p.unlink(missing_ok=True)
                    return {"success": True, "message": f"Model '{model_name}' deleted."}
                except Exception as e:
                    return {"success": False, "error": str(e)}
        return {"success": False, "error": "Model not found."}

    def get_running_containers(self) -> List[Dict[str, Any]]:
        """
        Return Docker-style list of active neural model container instances,
        including live PID, memory/VRAM consumption, CPU %, and pause/run status.
        """
        import psutil
        containers = []
        now = time.time()

        is_running = self.is_server_running()
        if not is_running or not self.active_model_name:
            return []

        meta = {}
        if self.active_model_path:
            try:
                meta = parse_gguf_metadata(self.active_model_path)
            except Exception:
                pass

        model_name = self.active_model_name or (Path(self.active_model_path).stem if self.active_model_path else "Active Model")
        display_name = meta.get("model_name") or model_name
        family = meta.get("family") or meta.get("architecture") or "Neural Model"
        model_type = meta.get("model_type") or ("Visual DiT Transformer" if getattr(self, "is_visual_active", False) else "LLM Reasoning Engine")
        
        uptime_sec = int(now - self.start_timestamp) if self.start_timestamp > 0 else 0
        mins, secs = divmod(uptime_sec, 60)
        hours, mins = divmod(mins, 60)
        if hours > 0:
            uptime_str = f"{hours}h {mins}m {secs}s"
        elif mins > 0:
            uptime_str = f"{mins}m {secs}s"
        else:
            uptime_str = f"{secs}s"

        pid = None
        ram_mb = 0.0
        cpu_pct = 0.0
        if self.active_process and self.active_process.poll() is None:
            pid = self.active_process.pid
            try:
                proc = psutil.Process(pid)
                ram_mb = round(proc.memory_info().rss / (1024 * 1024), 1)
                cpu_pct = round(proc.cpu_percent(interval=None), 1)
            except Exception:
                pass
        else:
            try:
                proc = psutil.Process(os.getpid())
                pid = proc.pid
                ram_mb = round(proc.memory_info().rss / (1024 * 1024), 1)
                cpu_pct = round(proc.cpu_percent(interval=None), 1)
            except Exception:
                pass

        vram_est = meta.get("estimated_vram") or "~3.5 GB VRAM"
        vram_mb = int((meta.get("size_bytes", 3 * 1024**3) / (1024**2)) * 1.15) if meta.get("size_bytes") else 3500

        gpu_temp = None
        gpu_name = "Dedicated GPU"
        try:
            from core.system_monitor import get_gpu_metrics
            gpu_m = get_gpu_metrics()
            if gpu_m:
                gpu_temp = gpu_m.get("temperature_c")
                if gpu_m.get("name"):
                    gpu_name = gpu_m["name"]
        except Exception:
            pass

        container_status = "paused" if getattr(self, "is_paused", False) else "running"

        containers.append({
            "id": f"c-{self.port if not getattr(self, 'is_visual_active', False) else 'dit'}",
            "container_name": f"modeldock-{model_name.lower().replace('.', '-')[:24]}",
            "model_name": model_name,
            "display_name": display_name,
            "family": family,
            "type": model_type,
            "file_path": self.active_model_path or "",
            "pid": pid,
            "port": self.port if not getattr(self, "is_visual_active", False) else None,
            "status": container_status,
            "is_paused": getattr(self, "is_paused", False),
            "ram_mb": ram_mb,
            "cpu_percent": cpu_pct,
            "vram_mb": vram_mb,
            "vram_formatted": f"~{round(vram_mb / 1024, 1)} GB VRAM" if vram_mb >= 1024 else f"{vram_mb} MB VRAM",
            "vram_requirement": vram_est,
            "gpu_name": gpu_name,
            "temperature_c": gpu_temp,
            "uptime_sec": uptime_sec,
            "uptime_formatted": uptime_str,
            "parameter_size": meta.get("parameter_size", "Standard"),
            "context_formatted": meta.get("context_formatted", "4,096 tokens"),
        })

        return containers

    def pause_container(self) -> Dict[str, Any]:
        """Pause / sleep the active model process to drop CPU/GPU compute to 0%."""
        import psutil
        if not self.is_server_running() and not self.active_model_name:
            return {"success": False, "error": "No active model is currently running."}

        self.is_paused = True
        if self.active_process and self.active_process.poll() is None:
            try:
                proc = psutil.Process(self.active_process.pid)
                proc.suspend()
            except Exception as e:
                print(f"[Engine] Suspend process error: {e}")

        return {"success": True, "status": "paused", "message": f"Model '{self.active_model_name}' is paused (CPU compute suspended)."}

    def resume_container(self) -> Dict[str, Any]:
        """Resume / unpause the active model process."""
        import psutil
        if not self.is_server_running() and not self.active_model_name:
            return {"success": False, "error": "No active model is currently running."}

        self.is_paused = False
        if self.active_process and self.active_process.poll() is None:
            try:
                proc = psutil.Process(self.active_process.pid)
                proc.resume()
            except Exception as e:
                print(f"[Engine] Resume process error: {e}")

        return {"success": True, "status": "running", "message": f"Model '{self.active_model_name}' resumed active execution."}


EngineManager = NativeEngineManager
