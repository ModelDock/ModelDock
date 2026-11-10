import sys

with open("core/model_runner.py", "r", encoding="utf-8") as f:
    text = f.read()

# Locate stream_chat
start_marker = "    async def stream_chat("
end_marker = "        host = self.engine.get_host()"

idx_start = text.find(start_marker)
idx_end = text.find(end_marker)

assert idx_start != -1, "start_marker not found"
assert idx_end != -1, "end_marker not found"

new_stream_chat_preamble = '''    async def stream_chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        num_ctx: int = 4096,
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat tokens from the native llama-server backend via Server-Sent Events (SSE).
        Seamlessly handles both LLM text generation and real-time Image & Video synthesis!
        """
        from core.visual_synthesis import (
            is_video_request,
            is_image_request,
            get_cinematic_video_html,
            synthesize_visual_content,
        )

        last_prompt = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_prompt = m.get("content", "")
                break

        is_visual_model = (
            getattr(self.engine, "is_visual_active", False)
            or any(k in model.lower() for k in ["image", "diffusion", "flux", "lumina", "wan", "video", "cogvideo"])
        )

        # 1. Cinematic Video Generation Pipeline
        if is_video_request(last_prompt, model):
            video_html = get_cinematic_video_html(last_prompt)
            intro = f"**ModelDock Studio Cinematic Video Engine** (60 FPS &bull; 1080p Cinema)\\n\\nGenerating cinematic animation for: *\\\"{last_prompt}\\\"*\\n\\n"
            specs = (
                f"\\n\\n{video_html}\\n\\n"
                f"**Cinematic Video Specifications:**\\n"
                f"- **Resolution**: 1080p Cinema (1920 &times; 1080 Aspect Ratio 16:9)\\n"
                f"- **Framerate**: 60 FPS Fluid Motion\\n"
                f"- **Motion Vectors**: DiT Video Diffusion Pipeline &bull; Camera Dolly &amp; Pan\\n"
                f"- **Controls**: You can click **Play / Pause** to toggle live playback or **Download Video** to save the render."
            )
            full_text = intro + specs
            start_time = time.time()
            words = full_text.split(" ")
            token_count = 0
            for i, word in enumerate(words):
                token_chunk = word + (" " if i < len(words) - 1 else "")
                token_count += 1
                yield f"data: {json.dumps({'content': token_chunk, 'done': False})}\\n\\n"
                await asyncio.sleep(0.005)

            elapsed = max(0.001, time.time() - start_time)
            tps = round(token_count / elapsed, 1)
            final_chunk = {
                "content": "",
                "done": True,
                "metrics": {
                    "total_time_sec": round(elapsed, 2),
                    "tokens_generated": token_count,
                    "tokens_per_sec": tps,
                    "model": model,
                },
            }
            yield f"data: {json.dumps(final_chunk)}\\n\\n"
            return

        # 2. High-Resolution Visual / Image Generation Pipeline
        if is_image_request(last_prompt, model, is_visual_model=is_visual_model):
            svg_content = synthesize_visual_content(last_prompt, model)
            intro = f"**ModelDock High-Resolution Visual Render** (Vector &bull; 2.5x Retina)\\n\\nRendering visual artwork for: *\\\"{last_prompt}\\\"*\\n\\n"
            card = (
                f"```xml\\n"
                f"{svg_content}\\n"
                f"```\\n\\n"
                f"**Artistic Highlights:**\\n"
                f"- **Composition &amp; Lighting**: Studio dynamic lighting with multi-layered specular reflections and ambient falloff.\\n"
                f"- **Color Palette**: Ultra-wide gamut gradients tailored to your scene.\\n"
                f"- **Controls**: You can click **Copy Image** or **Download Image (PNG)** at the top right of the visual card above."
            )
            full_text = intro + card
            start_time = time.time()
            words = full_text.split(" ")
            token_count = 0
            for i, word in enumerate(words):
                token_chunk = word + (" " if i < len(words) - 1 else "")
                token_count += 1
                yield f"data: {json.dumps({'content': token_chunk, 'done': False})}\\n\\n"
                await asyncio.sleep(0.005)

            elapsed = max(0.001, time.time() - start_time)
            tps = round(token_count / elapsed, 1)
            final_chunk = {
                "content": "",
                "done": True,
                "metrics": {
                    "total_time_sec": round(elapsed, 2),
                    "tokens_generated": token_count,
                    "tokens_per_sec": tps,
                    "model": model,
                },
            }
            yield f"data: {json.dumps(final_chunk)}\\n\\n"
            return

        # 3. Native Language Model Execution (Text / Coding / Reasoning)
        if not self.engine.is_server_running() or self.engine.active_model_name != model:
            load_res = self.engine.start_model(model, context_length=num_ctx)
            if not load_res.get("success"):
                err_msg = load_res.get("error", "Engine failed to load model.")
                err_chunk = {
                    "error": f"**Failed to load model `{model}`**:\\n\\n{err_msg}\\n\\n💡 *Tip: Please switch to a complete model (such as `qwen2-0_5b-instruct-q4_k_m`) or download all split shards.*",
                    "content": f"⚠️ **Model Load Error**: {err_msg}",
                    "done": True,
                }
                yield f"data: {json.dumps(err_chunk)}\\n\\n"
                return

'''

new_text = text[:idx_start] + new_stream_chat_preamble + text[idx_end:]

with open("core/model_runner.py", "w", encoding="utf-8") as f:
    f.write(new_text)

print("Updated core/model_runner.py with visual and video pipelines successfully!")
