with open("core/engine_manager.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update is_server_running
target1 = '''    def is_server_running(self) -> bool:
        """Check if native llama-server is alive and responding."""
        if self.is_fallback_mode:
            return True'''

repl1 = '''    def is_server_running(self) -> bool:
        """Check if native llama-server is alive and responding."""
        if getattr(self, "is_visual_active", False):
            return True
        if self.is_fallback_mode:
            return True'''

# 2. Update stop_server
target2 = '''            self.active_process = None
            self.active_model_path = None
            self.active_model_name = None'''

repl2 = '''            self.active_process = None
            self.active_model_path = None
            self.active_model_name = None
        self.is_visual_active = False'''

# 3. Update start_model
target3 = '''        # Stop previous model
        self.stop_server()

        binary = self.get_server_binary()'''

repl3 = '''        # Stop previous model
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
            return {
                "success": True,
                "model_name": target.stem,
                "message": f"ModelDock Visual & Video Synthesis Engine ready for '{target.stem}'.",
                "model_type": "visual_synthesis",
            }

        binary = self.get_server_binary()'''

assert target1 in code, "target1 not found in core/engine_manager.py"
assert target2 in code, "target2 not found in core/engine_manager.py"
assert target3 in code, "target3 not found in core/engine_manager.py"

code = code.replace(target1, repl1, 1)
code = code.replace(target2, repl2, 1)
code = code.replace(target3, repl3, 1)

with open("core/engine_manager.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Updated core/engine_manager.py successfully!")
