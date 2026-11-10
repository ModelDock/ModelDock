import re
from pathlib import Path

path = Path(r"a:\AI_Project_work\ollama_2nd_copy\core\engine_manager.py")
content = path.read_text(encoding="utf-8")

# Helper function to extract error from llama_server.log
extract_error_method = """    def _extract_engine_error(self, log_path: Path) -> str:
        \"\"\"Parse llama-server log to extract clean, human-readable error.\"\"\"
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
            m = re.search(r"unknown model architecture:\\s*['\\\"]?([^'\\\"\\n\\r]+)", log_content, re.IGNORECASE)
            arch = m.group(1).strip() if m else "unsupported"
            return f"Unsupported architecture ('{arch}'). llama-server natively executes Language Models (LLMs). Image/diffusion architectures require diffusion pipelines."
        if "failed to allocate" in log_lower or "out of memory" in log_lower:
            return "Out of Memory: Insufficient RAM/VRAM to load model weights. Try running in CPU mode (0 GPU layers) or choosing a smaller quantization."

        # Search for explicit error lines
        error_lines = [line.strip() for line in log_content.splitlines() if "error" in line.lower() or "failed" in line.lower()]
        if error_lines:
            raw = error_lines[-1]
            cleaned = re.sub(r"^\\d+\\.\\d+\\.\\d+\\.\\d+\\s+[IEW]\\s+([a-zA-Z0-9_]+:\\s*)?", "", raw).strip()
            return f"Engine initialization error: {cleaned}"

        return "Native engine exited unexpectedly during startup."

    def stop_server(self) -> None:"""

if "def _extract_engine_error" not in content:
    content = content.replace("    def stop_server(self) -> None:", extract_error_method, 1)

# In stop_server, close _server_log if open
old_stop_server = """    def stop_server(self) -> None:
        \"\"\"Cleanly terminate any active llama-server process.\"\"\"
        self.is_fallback_mode = False
        if self.active_process:"""

new_stop_server = """    def stop_server(self) -> None:
        \"\"\"Cleanly terminate any active llama-server process.\"\"\"
        self.is_fallback_mode = False
        if hasattr(self, "_server_log") and self._server_log:
            try:
                self._server_log.flush()
                self._server_log.close()
            except Exception:
                pass
            self._server_log = None

        if self.active_process:"""

content = content.replace(old_stop_server, new_stop_server, 1)

# Now replace start_model body from cmd execution onwards
old_start_model_body = """        cmd = [
            str(binary),
            "-m", str(target.resolve()),
            "--port", str(self.port),
            "--host", "127.0.0.1",
            "-c", str(context_length),
            "-t", str(cpu_threads),
            "-ngl", str(ngl),
            "--no-warmup",
        ]

        try:
            self.active_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            time.sleep(0.15)
            poll_res = self.active_process.poll()
            if poll_res is not None and poll_res != 0:
                # Binary blocked by OS policy or exited immediately; activate safe in-process runtime
                self.is_fallback_mode = True
                self.active_model_path = str(target.resolve())
                self.active_model_name = target.stem
                return {
                    "success": True,
                    "model_name": target.stem,
                    "host": "embedded://in-process",
                    "mode": "embedded",
                    "message": f"Successfully loaded '{target.stem}' into Native Engine (In-Process Safe).",
                }

            self.active_model_path = str(target.resolve())
            self.active_model_name = target.stem

            # Wait up to 5 seconds for server /health endpoint to become ready
            start_time = time.time()
            while time.time() - start_time < 5.0:
                if self.is_server_running():
                    return {
                        "success": True,
                        "model_name": target.stem,
                        "host": self.host,
                        "message": f"Successfully loaded '{target.stem}' into Native Engine.",
                    }
                time.sleep(0.2)

            self.is_fallback_mode = True
            return {
                "success": True,
                "model_name": target.stem,
                "host": "embedded://in-process",
                "mode": "embedded",
                "message": f"Successfully loaded '{target.stem}' into Native Engine (In-Process Safe).",
            }
        except OSError:
            # Handles WinError 4551 (Smart App Control / WDAC policy block)
            self.is_fallback_mode = True
            self.active_model_path = str(target.resolve())
            self.active_model_name = target.stem
            return {
                "success": True,
                "model_name": target.stem,
                "host": "embedded://in-process",
                "mode": "embedded",
                "message": f"Successfully loaded '{target.stem}' into Native Engine (In-Process Safe).",
            }
        except Exception as e:
            self.stop_server()
            return {"success": False, "error": f"Failed to start native server: {str(e)}"}"""

new_start_model_body = """        # Pre-check: Incomplete split shard detection
        split_match = re.search(r"-(\\d{5})-of-(\\d{5})\\.gguf$", target.name, re.IGNORECASE)
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
            return {"success": False, "error": f"Failed to start native server: {str(e)}"}"""

if old_start_model_body in content:
    content = content.replace(old_start_model_body, new_start_model_body, 1)
    print("Replaced start_model body successfully.")
else:
    print("Warning: old_start_model_body did not match.")

path.write_text(content, encoding="utf-8")
print("Engine manager updated successfully.")
