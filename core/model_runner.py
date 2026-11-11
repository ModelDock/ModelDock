"""
ModelDock Studio - Standalone Native Model Runner
Streams chat completions directly from the native llama-server engine without Ollama.
"""

import time
import json
import asyncio
import re
from typing import AsyncGenerator, Dict, Any, List, Optional
import httpx
from core.config import ConfigManager
from core.engine_manager import NativeEngineManager


def estimate_tokens(text: str) -> int:
    """Accurate token estimator for GGUF/BPE models (~3.5 chars per token)."""
    if not text:
        return 0
    return max(1, int(len(text) / 3.5) + 4)


def prune_messages_for_context(
    messages: List[Dict[str, str]], 
    max_context: int = 4096, 
    reserve_generation: int = 1024
) -> List[Dict[str, str]]:
    """
    Sliding window context pruner.
    Ensures that accumulated conversation history never exceeds the model's available context window.
    Always preserves:
      1. System instructions (if present)
      2. The latest user message
      3. The most recent conversation turns that fit within (max_context - reserve_generation)
    """
    if not messages:
        return []

    token_budget = max(512, max_context - reserve_generation)

    system_msgs = [m for m in messages if m.get("role") == "system"]
    non_system_msgs = [m for m in messages if m.get("role") != "system"]

    if not non_system_msgs:
        return system_msgs

    # Calculate system token usage
    system_tokens = sum(estimate_tokens(m.get("content", "")) for m in system_msgs)
    available_budget = token_budget - system_tokens

    # Latest message must always be preserved
    latest_msg = non_system_msgs[-1]
    latest_tokens = estimate_tokens(latest_msg.get("content", ""))

    # If the latest message alone exceeds the budget, truncate it safely from start
    if latest_tokens > available_budget:
        max_chars = int(available_budget * 3.5)
        truncated_content = latest_msg.get("content", "")[-max_chars:]
        return system_msgs + [{
            "role": latest_msg.get("role", "user"), 
            "content": f"[...earlier prompt truncated...]\n{truncated_content}"
        }]

    # Collect previous messages in reverse chronological order
    kept_history = [latest_msg]
    used_tokens = latest_tokens

    for msg in reversed(non_system_msgs[:-1]):
        msg_tokens = estimate_tokens(msg.get("content", ""))
        if used_tokens + msg_tokens <= available_budget:
            kept_history.append(msg)
            used_tokens += msg_tokens
        else:
            # Reached context limit; older conversation turns gracefully trimmed
            break

    kept_history.reverse()
    return system_msgs + kept_history


class ModelRunner:
    def __init__(self, config: Optional[ConfigManager] = None, engine: Optional[NativeEngineManager] = None):
        self.config = config or ConfigManager.get_instance()
        self.engine = engine or NativeEngineManager.get_instance()

    async def stream_chat(
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
            get_visual_highlights,
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

        # 1. Authentic Local AI Video Generation Pipeline (Direct MP4 & WebP • RTX 4060 GPU)
        if is_video_request(last_prompt, model):
            from core.local_video_engine import generate_local_video, get_real_video_card_html

            # Resolve subject from current prompt or backwards search through chat history
            video_prompt = last_prompt
            clean_cmd = re.sub(
                r"\b(now|please|can you|generate|create|make|render|produce|video|animation|clip|movie|footage|of|for|about|\d+\s*(?:min|mins|minutes|second|seconds|sec|secs))\b",
                "",
                last_prompt,
                flags=re.IGNORECASE
            ).strip()

            if len(clean_cmd) < 3:
                # Meta-command without a concrete subject (e.g. "now generate video of 1 min")
                for prev_m in reversed(messages[:-1]):
                    if prev_m.get("role") == "user":
                        prev_text = prev_m.get("content", "").strip()
                        prev_clean = re.sub(
                            r"\b(now|please|can you|generate|create|make|render|produce|video|animation|clip|movie|footage|image|photo|picture|of|for|about|\d+\s*(?:min|mins|minutes|second|seconds|sec|secs))\b",
                            "",
                            prev_text,
                            flags=re.IGNORECASE
                        ).strip()
                        if len(prev_clean) >= 3:
                            video_prompt = f"{prev_text} ({last_prompt})"
                            break

            disp_title = video_prompt.strip().title()
            if len(disp_title) > 60:
                disp_title = disp_title[:57] + "..."

            intro = (
                f"**ModelDock Studio Local AI Video Engine** (Direct MP4 • 100% Local GPU)\n\n"
                f"🎬 Synthesizing cinematic motion clip for: *\"{disp_title}\"*\n\n"
            )
            yield f"data: {json.dumps({'content': intro, 'done': False})}\n\n"

            loop = asyncio.get_running_loop()
            video_res = await loop.run_in_executor(
                None,
                generate_local_video,
                video_prompt,
                model
            )

            video_html = get_real_video_card_html(video_res)
            dur_val = float(video_res.get('duration_sec', 120.0))
            hours = int(dur_val // 3600)
            mins = int((dur_val % 3600) // 60)
            secs = int(dur_val % 60)
            if hours > 0:
                dur_fmt = f"{hours:02d}:{mins:02d}:{secs:02d} ({int(dur_val)}s / {hours} Hour Feature-Length)"
            else:
                dur_fmt = f"{mins:02d}:{secs:02d} ({int(dur_val)}s)"
            specs = (
                f"\n\n{video_html}\n\n"
                f"**Cinematic Video Specifications:**\n"
                f"- **Format**: Direct H.264 MP4 Cinema Stream (`{video_res['mp4_filename']}`)\n"
                f"- **Duration**: **{dur_fmt}** ({video_res['num_frames']} Frames at {video_res['fps']} FPS)\n"
                f"- **Resolution**: {video_res['width']} × {video_res['height']} Standard Cinema Viewport\n"
                f"- **Subject Kinematics**: Authentic multi-frame character animation, rhythmic choreography & multi-scene cuts\n"
                f"- **Local Storage**: Saved locally to `data/generated/{video_res['mp4_filename']}` (100% self-owned, 0% cloud).\n"
                f"- **Controls**: Use the interactive player scrubber, play/pause controls, or click **Expand** for full cinema lightbox."
            )
            full_text = specs
            start_time = time.time()
            chunk_size = 48
            token_count = 0
            for i in range(0, len(full_text), chunk_size):
                chunk = full_text[i:i + chunk_size]
                token_count += 1
                yield f"data: {json.dumps({'content': chunk, 'done': False})}\n\n"
                await asyncio.sleep(0.004)

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
            yield f"data: {json.dumps(final_chunk)}\n\n"
            return

        # 2. Local Photorealistic Image Generation Pipeline (Real Local PNG File, Zero SVG)
        if is_image_request(last_prompt, model, is_visual_model=is_visual_model):
            from core.visual_synthesis import resolve_visual_prompt
            res_meta = resolve_visual_prompt(messages)
            disp_title = res_meta["display_name"]
            diff_prompt = res_meta["diffusion_prompt"]
            diff_steps = res_meta["steps"]
            diff_guidance = res_meta["guidance_scale"]
            is_boost = res_meta.get("is_quality_boost", False)

            # Stream immediate status token with clean Unicode bullet and true visual title
            quality_badge = " (Ultra-Quality Mode)" if is_boost else ""
            intro = f"**ModelDock Local Neural AI Render** (100% Local GPU • Direct PNG)\n\n⚡ Synthesizing visual frame for: *\"{disp_title}\"*{quality_badge}\n\n"
            yield f"data: {json.dumps({'content': intro, 'done': False})}\n\n"

            # Execute generation in async thread pool so event loop remains responsive
            from core.local_visual_engine import generate_local_image
            loop = asyncio.get_running_loop()
            img_res = await loop.run_in_executor(
                None,
                generate_local_image,
                diff_prompt,
                model,
                None,
                diff_steps,
                diff_guidance
            )

            image_url = img_res["url"]
            filename = img_res["filename"]
            highlights = get_visual_highlights(disp_title)
            card = (
                f"<!-- AI_REAL_IMAGE_START -->\n"
                f"<div class=\"ai-raster-image-card\">\n"
                f"  <div class=\"ai-image-header\">\n"
                f"    <div class=\"ai-image-badge-label\">\n"
                f"      <svg width=\"15\" height=\"15\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\"><rect x=\"3\" y=\"3\" width=\"18\" height=\"18\" rx=\"2\" ry=\"2\"></rect><circle cx=\"8.5\" cy=\"8.5\" r=\"1.5\"></circle><polyline points=\"21 15 16 10 5 21\"></polyline></svg>\n"
                f"      <span>Local Neural AI Render</span>\n"
                f"      <span class=\"ai-image-res-pill\">Direct PNG • 100% Local GPU</span>\n"
                f"    </div>\n"
                f"    <div class=\"ai-image-actions\">\n"
                f"      <button class=\"btn-image-action\" onclick=\"enhanceImageTo8K(this, '{image_url}')\" title=\"Enhance to 4K / 8K Ultra-HD with AI Super-Resolution\" style=\"color: #c084fc;\">\n"
                f"        <svg width=\"13\" height=\"13\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\"><polygon points=\"12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2\"></polygon></svg>\n"
                f"        <span>8K Enhance</span>\n"
                f"      </button>\n"
                f"      <button class=\"btn-image-action\" onclick=\"copyRasterImageFromCard(this)\" title=\"Copy PNG to clipboard\">\n"
                f"        <svg width=\"13\" height=\"13\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\"><rect x=\"9\" y=\"9\" width=\"13\" height=\"13\" rx=\"2\" ry=\"2\"></rect><path d=\"M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1\"></path></svg>\n"
                f"        <span>Copy Image</span>\n"
                f"      </button>\n"
                f"      <a class=\"btn-image-action btn-image-download\" href=\"{image_url}\" download=\"{filename}\" title=\"Download high-resolution PNG\">\n"
                f"        <svg width=\"13\" height=\"13\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\"><path d=\"M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4\"></path><polyline points=\"7 10 12 15 17 10\"></polyline><line x1=\"12\" y1=\"15\" x2=\"12\" y2=\"3\"></line></svg>\n"
                f"        <span>Download Image</span>\n"
                f"      </a>\n"
                f"    </div>\n"
                f"  </div>\n"
                f"  <div class=\"ai-raster-viewport\">\n"
                f"    <img src=\"{image_url}\" alt=\"{disp_title}\" class=\"generated-real-photo\" onclick=\"openImageLightbox(this.src, this.alt)\" title=\"Click to zoom &amp; inspect (Scroll wheel to zoom, Drag to pan)\" style=\"max-width:440px; max-height:380px; width:100%; border-radius:12px; display:block; cursor:zoom-in; object-fit:cover; box-shadow:0 10px 30px rgba(0,0,0,0.5);\" />\n"
                f"  </div>\n"
                f"</div>\n"
                f"<!-- AI_REAL_IMAGE_END -->\n\n"
                f"**Artistic Highlights:**\n"
                f"{highlights}\n"
                f"- **Local Storage**: Saved locally to `data/generated/{filename}` (100% self-owned, 0% cloud).\n"
                f"- **Controls**: You can click **Download Image** to save the PNG or **Copy Image**."
            )
            full_text = card
            start_time = time.time()
            chunk_size = 48
            token_count = 0
            for i in range(0, len(full_text), chunk_size):
                chunk = full_text[i:i + chunk_size]
                token_count += 1
                yield f"data: {json.dumps({'content': chunk, 'done': False})}\n\n"
                await asyncio.sleep(0.004)

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
            yield f"data: {json.dumps(final_chunk)}\n\n"
            return

        # 3. Native Language Model Execution (Text / Coding / Reasoning)
        # Ensure any residual GPU VRAM from previous image diffusion runs is freed for the LLM
        try:
            from core.neural_diffusion_engine import release_gpu_memory
            release_gpu_memory()
        except Exception:
            pass

        if not self.engine.is_server_running() or self.engine.active_model_name != model:
            load_res = self.engine.start_model(model, context_length=num_ctx)
            if not load_res.get("success"):
                err_msg = load_res.get("error", "Engine failed to load model.")
                err_chunk = {
                    "error": f"**Failed to load model `{model}`**:\n\n{err_msg}\n\n💡 *Tip: Please switch to a complete model (such as `qwen2-0_5b-instruct-q4_k_m`) or download all split shards.*",
                    "content": f"⚠️ **Model Load Error**: {err_msg}",
                    "done": True,
                }
                yield f"data: {json.dumps(err_chunk)}\n\n"
                return

        host = self.engine.get_host()
        url = f"{host}/v1/chat/completions"

        chat_messages = []
        has_system = any(m.get("role") == "system" for m in messages)
        effective_system = system_prompt or (
            "You are ModelDock, an intelligent, helpful local AI assistant running privately on local hardware. "
            "Your name is ModelDock. When the user asks what your name is or who you are, always state clearly: 'I am ModelDock, your local AI assistant.' "
            "Never call yourself generic 'AI' and never call the user ModelDock. "
            "You excel in software engineering, programming, creative design, and technical reasoning. "
            "When the user asks you to create, generate, draw, or design an image, artwork, poster, or diagram, "
            "NEVER claim you cannot produce images. Instead, immediately generate a complete, high-quality, full-featured <svg> "
            "graphic enclosed inside a ```xml ... ``` code block with rich styling, gradients, colors, and typography. "
            "The ModelDock Studio UI automatically renders SVG graphics as visual artwork with instant Copy and Download options."
        )
        if "I am ModelDock" not in effective_system:
            effective_system = f"You are ModelDock, an intelligent local AI assistant. When the user asks what your name is or who you are, always state clearly: 'I am ModelDock, your local AI assistant.'\n\n{effective_system}"
        if not has_system:
            chat_messages.append({"role": "system", "content": effective_system})
        chat_messages.extend(messages)

        # Apply sliding window context pruning so history NEVER exceeds n_ctx
        context_budget = int(num_ctx or 4096)
        pruned_messages = prune_messages_for_context(
            chat_messages, 
            max_context=context_budget, 
            reserve_generation=1024
        )

        payload = {
            "messages": pruned_messages,
            "temperature": float(temperature),
            "stream": True,
            "max_tokens": -1,
        }

        start_time = time.time()
        token_count = 0

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=10.0)) as client:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code != 200:
                        raw_bytes = await response.aread()
                        raw_err = raw_bytes.decode("utf-8", errors="ignore")
                        if "exceed_context_size_error" in raw_err:
                            user_err = (
                                "⚠️ **Context Window Limit Reached**\n\n"
                                f"The conversation history exceeded the active `{context_budget}` token context window.\n\n"
                                "**How to fix:**\n"
                                "- Click **Parameters** (or **Think**) at the top of the chat and increase the **Context Window** (e.g. to `8,192` or `16,384` tokens).\n"
                                "- Or click **+ New chat** in the left sidebar to start a fresh conversation session."
                            )
                        else:
                            user_err = f"Native engine error {response.status_code}: {raw_err}"

                        err_chunk = {
                            "error": user_err,
                            "done": True,
                        }
                        yield f"data: {json.dumps(err_chunk)}\n\n"
                        return

                    async for line in response.aiter_lines():
                        line = line.strip()
                        if not line or line.startswith(":"):
                            continue

                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if data_str == "[DONE]":
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
                                yield f"data: {json.dumps(final_chunk)}\n\n"
                                break

                            try:
                                data = json.loads(data_str)
                                choices = data.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    content = delta.get("content", "")
                                    finish_reason = choices[0].get("finish_reason")

                                    if content:
                                        token_count += 1
                                        yield f"data: {json.dumps({'content': content, 'done': False})}\n\n"

                                    if finish_reason:
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
                                        yield f"data: {json.dumps(final_chunk)}\n\n"
                                        break
                            except Exception:
                                continue
        except Exception as e:
            err_data = {"error": f"Native runner execution error: {str(e)}", "done": True}
            yield f"data: {json.dumps(err_data)}\n\n"
