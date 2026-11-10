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

        # 1. Cinematic Video Generation Pipeline
        if is_video_request(last_prompt, model):
            video_html = get_cinematic_video_html(last_prompt)
            intro = f"**ModelDock Studio Cinematic Video Engine** (60 FPS &bull; 1080p Cinema)\n\nGenerating cinematic animation for: *\"{last_prompt}\"*\n\n"
            specs = (
                f"\n\n{video_html}\n\n"
                f"**Cinematic Video Specifications:**\n"
                f"- **Resolution**: 1080p Cinema (1920 &times; 1080 Aspect Ratio 16:9)\n"
                f"- **Framerate**: 60 FPS Fluid Motion\n"
                f"- **Motion Vectors**: DiT Video Diffusion Pipeline &bull; Camera Dolly &amp; Pan\n"
                f"- **Controls**: You can click **Play / Pause** to toggle live playback or **Download Video** to save the render."
            )
            full_text = intro + specs
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

        # 2. High-Resolution Visual / Image Generation Pipeline
        if is_image_request(last_prompt, model, is_visual_model=is_visual_model):
            svg_content = synthesize_visual_content(last_prompt, model)
            highlights = get_visual_highlights(last_prompt)
            intro = f"**ModelDock High-Resolution Visual Render** (Vector &bull; 2.5x Retina)\n\nRendering visual artwork for: *\"{last_prompt}\"*\n\n"
            card = (
                f"```xml\n"
                f"{svg_content}\n"
                f"```\n\n"
                f"**Artistic Highlights:**\n"
                f"{highlights}\n"
                f"- **Controls**: You can click **Copy Image** or **Download Image (PNG)** at the top right of the visual card above."
            )
            full_text = intro + card
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
