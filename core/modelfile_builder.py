"""
ModelDock Studio - Modelfile Builder & Engine Registration
Converts downloaded Hugging Face GGUF models and local GGUF files into runnable Ollama/xOllama models.
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
import httpx
from core.config import ConfigManager
from core.engine_manager import EngineManager


def generate_modelfile_content(
    gguf_path: str,
    context_length: int = 4096,
    temperature: float = 0.7,
    system_prompt: Optional[str] = None,
) -> str:
    """Generate a clean, standardized Ollama Modelfile for a GGUF file."""
    # Ensure forward slashes for cross-platform compatibility
    normalized_path = Path(gguf_path).resolve().as_posix()
    
    lines = [
        f'FROM "{normalized_path}"',
        f"PARAMETER num_ctx {context_length}",
        f"PARAMETER temperature {temperature}",
        "PARAMETER stop <|im_end|>",
        "PARAMETER stop <|endoftext|>",
    ]

    if system_prompt and system_prompt.strip():
        # Escape quotes in system prompt
        escaped_prompt = system_prompt.strip().replace('"', '\\"')
        lines.append(f'SYSTEM "{escaped_prompt}"')

    return "\n".join(lines) + "\n"


async def register_gguf_into_ollama(
    model_name: str,
    gguf_path: str,
    context_length: int = 4096,
    temperature: float = 0.7,
    system_prompt: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Registers a local GGUF file as a named model in Ollama/xOllama.
    First tries the REST API /api/create; if that fails or times out, uses the CLI xollama create.
    """
    config = ConfigManager.get_instance()
    engine = EngineManager(config)
    host = engine.get_host()
    modelfile_str = generate_modelfile_content(
        gguf_path=gguf_path,
        context_length=context_length,
        temperature=temperature,
        system_prompt=system_prompt,
    )

    clean_model_name = model_name.strip().lower().replace(" ", "-")

    # 1. Try REST API /api/create
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{host}/api/create",
                json={
                    "name": clean_model_name,
                    "modelfile": modelfile_str,
                    "stream": False,
                },
            )
            if resp.status_code == 200:
                return {
                    "success": True,
                    "model_name": clean_model_name,
                    "message": f"Successfully registered '{clean_model_name}' into {host}",
                }
    except Exception:
        pass

    # 2. Try CLI fallback (xollama create or ollama create)
    binary = config.get("ollama_binary")
    if binary and os.path.isfile(binary):
        try:
            # Write temporary Modelfile
            temp_modelfile = Path(gguf_path).parent / f"Modelfile_{clean_model_name}"
            temp_modelfile.write_text(modelfile_str, encoding="utf-8")

            res = subprocess.run(
                [binary, "create", clean_model_name, "-f", str(temp_modelfile)],
                capture_output=True,
                text=True,
                timeout=60.0,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            try:
                temp_modelfile.unlink(missing_ok=True)
            except Exception:
                pass

            if res.returncode == 0:
                return {
                    "success": True,
                    "model_name": clean_model_name,
                    "message": f"Successfully registered '{clean_model_name}' via CLI.",
                }
            else:
                return {
                    "success": False,
                    "error": f"CLI registration error: {res.stderr or res.stdout}",
                }
        except Exception as e:
            return {"success": False, "error": f"CLI execution failed: {str(e)}"}

    return {
        "success": False,
        "error": "Could not connect to Ollama REST API and binary CLI was unavailable.",
    }
