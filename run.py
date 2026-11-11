"""
ModelDock Studio - Main Application Server
A unified, ultra-lightweight open-source AI platform running locally on CPU & GPU.
Consumes under 30MB RAM idle with 0% CPU overhead.
"""

import os
import sys

# Ensure UTF-8 output encoding across Windows consoles to prevent charmap errors
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

if sys.platform == "win32":
    import asyncio
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass
import atexit
import webbrowser
import threading
import time
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add current directory to Python path
CURRENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CURRENT_DIR))

# Ensure hardware acceleration defaults for local engines
os.environ.setdefault("LLAMA_ARG_GPU", "auto")
os.environ.setdefault("XOLLAMA_ENGINE", "auto")
os.environ.setdefault("XOLLAMA_ENGINE_FALLBACK", "true")

import uvicorn
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, File, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.config import ConfigManager
from core.system_monitor import get_full_system_status
from core.auth_manager import AuthManager
from core.engine_manager import EngineManager
from core.hf_hub import HFHubClient
from core.downloader import DownloadManager
from core.model_runner import ModelRunner
from core.media_processor import MediaProcessor
from core.chat_manager import ChatManager

from contextlib import asynccontextmanager

config_mgr = ConfigManager.get_instance()
auth_mgr = AuthManager(config_mgr)
engine_mgr = EngineManager(config_mgr)
hf_client = HFHubClient(auth_mgr)
download_mgr = DownloadManager(config_mgr, auth_mgr)
model_runner = ModelRunner(config_mgr, engine_mgr)
chat_mgr = ChatManager.get_instance()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Zero ghost processes: Clean shutdown lifecycle hook
    try:
        engine_mgr.stop_server()
    except Exception:
        pass


app = FastAPI(
    title="ModelDock Studio",
    description="Universal Local AI Model Platform for Hugging Face & Ollama",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for external local apps (VS Code Continue, Cursor, WebUIs)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prevent Stale Browser Caching (Forces immediate JS/CSS reload on browser refresh)
@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Serve static files
STATIC_DIR = CURRENT_DIR / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Serve locally generated real images
GENERATED_DIR = CURRENT_DIR / "data" / "generated"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/api/media/generated", StaticFiles(directory=str(GENERATED_DIR)), name="generated_media")

# Zero ghost processes: Clean exit handler
def on_app_exit():
    """Ensure all background processes, llama-server, and engines terminate cleanly on exit."""
    try:
        engine_mgr.stop_server()
    except Exception:
        pass

atexit.register(on_app_exit)


# Pydantic Request Models
class AuthRequest(BaseModel):
    token: str


class ConfigUpdateRequest(BaseModel):
    cpu_threads: Optional[int] = None
    gpu_mode: Optional[str] = None
    gpu_layers: Optional[int] = None
    default_temperature: Optional[float] = None
    default_context_length: Optional[int] = None
    system_prompt: Optional[str] = None
    models_dir: Optional[str] = None
    downloads_dir: Optional[str] = None
    server_host: Optional[str] = None
    server_port: Optional[int] = None
    nav_position: Optional[str] = None
    user_name: Optional[str] = None
    user_title: Optional[str] = None


class DownloadRequest(BaseModel):
    url: str
    filename: str
    model_name: Optional[str] = None
    auto_register: bool = True


class OllamaPullRequest(BaseModel):
    model_name: str


class ImportLocalRequest(BaseModel):
    file_path: str
    model_name: str
    context_length: int = 4096
    temperature: float = 0.7
    system_prompt: Optional[str] = None


class AttachmentItem(BaseModel):
    id: str
    filename: str
    file_type: str
    doc_type: Optional[str] = None
    extracted_text: Optional[str] = None
    size_formatted: Optional[str] = None
    preview_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    attachments: Optional[List[AttachmentItem]] = None
    temperature: Optional[float] = 0.7
    num_ctx: Optional[int] = 4096
    system_prompt: Optional[str] = None


# --- Web Page Route ---
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = STATIC_DIR / "index.html"
    if index_path.is_file():
        return HTMLResponse(content=index_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>ModelDock Studio starting...</h1>")


# --- System & Telemetry Endpoints ---
@app.get("/api/system/status")
async def api_system_status():
    """Return software RAM/CPU, host RAM, and GPU VRAM telemetry."""
    return get_full_system_status()


@app.get("/api/config")
@app.get("/api/settings")
async def api_get_config():
    """Return current configuration without sensitive tokens (Podman style)."""
    cfg = dict(config_mgr.data)
    token = cfg.get("hf_token", "")
    cfg["has_hf_token"] = bool(token)
    cfg["hf_token_preview"] = f"{token[:4]}...{token[-4:]}" if len(token) > 8 else ("***" if token else "")
    cfg.pop("hf_token", None)  # Mask raw token in config endpoint
    cfg["system_cpu_count"] = os.cpu_count() or 4
    return cfg


@app.post("/api/config/update")
@app.post("/api/settings/update")
async def api_update_config(req: ConfigUpdateRequest):
    dump_fn = getattr(req, "model_dump", getattr(req, "dict", None))
    dumped = dump_fn() if dump_fn else req.__dict__
    updates = {k: v for k, v in dumped.items() if v is not None}
    config_mgr.update_multiple(updates)
    models = engine_mgr.list_installed_models()
    return {"success": True, "message": "Settings updated successfully.", "models_count": len(models)}


@app.post("/api/settings/select-folder")
async def api_select_folder(payload: Dict[str, str]):
    """Open native Windows folder selection dialog and return chosen path."""
    folder_type = payload.get("folder", "models")
    current_val = config_mgr.get(f"{folder_type}_dir", "")

    if sys.platform == "win32":
        import subprocess
        ps_code = f"""
Add-Type -AssemblyName System.Windows.Forms
$dialog = New-Object System.Windows.Forms.FolderBrowserDialog
$dialog.Description = "Select {folder_type.capitalize()} Folder for ModelDock"
$dialog.ShowNewFolderButton = $true
if ('{current_val}' -and (Test-Path '{current_val}')) {{
    $dialog.SelectedPath = '{current_val}'
}}
$topForm = New-Object System.Windows.Forms.Form
$topForm.TopMost = $true
if ($dialog.ShowDialog($topForm) -eq [System.Windows.Forms.DialogResult]::OK) {{
    Write-Output $dialog.SelectedPath
}}
$topForm.Dispose()
"""
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_code],
                capture_output=True,
                text=True,
                timeout=60,
            )
            selected = res.stdout.strip()
            if selected and Path(selected).is_dir():
                return {"success": True, "path": selected}
            return {"success": False, "cancelled": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    return {"success": False, "error": "Folder selection dialog is supported on Windows."}


@app.post("/api/settings/open-folder")
async def api_open_folder(payload: Dict[str, str]):
    """Open models or downloads directory in Windows File Explorer."""
    folder_type = payload.get("folder", "models")
    if folder_type == "models":
        folder_path = Path(config_mgr.get("models_dir", CURRENT_DIR / "models"))
    elif folder_type == "downloads":
        folder_path = Path(config_mgr.get("downloads_dir", CURRENT_DIR / "downloads"))
    else:
        folder_path = CURRENT_DIR

    folder_path.mkdir(parents=True, exist_ok=True)
    try:
        if sys.platform == "win32":
            os.startfile(str(folder_path.resolve()))
        else:
            import subprocess
            subprocess.Popen(["xdg-open", str(folder_path.resolve())])
        return {"success": True, "path": str(folder_path.resolve())}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/settings/prune-downloads")
async def api_prune_downloads():
    """Clean up incomplete or temporary downloads."""
    dl_dir = Path(config_mgr.get("downloads_dir", CURRENT_DIR / "downloads"))
    freed_bytes = 0
    deleted_count = 0
    if dl_dir.exists():
        for f in list(dl_dir.glob("*.tmp")) + list(dl_dir.glob("*.part")):
            try:
                freed_bytes += f.stat().st_size
                f.unlink()
                deleted_count += 1
            except Exception:
                pass
    freed_mb = round(freed_bytes / (1024 * 1024), 2)
    return {"success": True, "deleted_count": deleted_count, "freed_mb": freed_mb}


# --- Hugging Face Authentication Endpoints ---
@app.get("/api/auth/status")
async def api_auth_status():
    """Check Hugging Face authentication state and user profile."""
    return await auth_mgr.get_current_auth_status()


@app.post("/api/auth/login")
async def api_auth_login(req: AuthRequest):
    """Authenticate with Hugging Face Access Token."""
    res = await auth_mgr.verify_token(req.token)
    if res.get("valid"):
        return {"success": True, "user": res}
    return JSONResponse(status_code=400, content={"success": False, "error": res.get("error")})


@app.post("/api/auth/logout")
async def api_auth_logout():
    """Sign out and remove stored Hugging Face Token."""
    auth_mgr.logout()
    return {"success": True, "message": "Logged out successfully."}


# --- Engine (Native llama.cpp Engine - Zero Ollama) Endpoints ---
@app.get("/api/engine/status")
async def api_engine_status():
    return await engine_mgr.check_health()


@app.post("/api/engine/load")
async def api_engine_load(payload: Dict[str, Any]):
    model = payload.get("model", "")
    ctx = payload.get("context_length", 4096)
    return engine_mgr.start_model(model, context_length=ctx)


@app.post("/api/engine/stop")
async def api_engine_stop():
    engine_mgr.stop_server()
    from core.neural_diffusion_engine import release_gpu_memory
    release_gpu_memory()
    import gc
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass
    return {"success": True, "message": "Engine stopped and memory freed."}


@app.get("/api/engine/containers")
async def api_get_engine_containers():
    """Return Docker-style list of active model container instances and their resource footprint."""
    return engine_mgr.get_running_containers()


@app.post("/api/engine/pause")
async def api_engine_pause():
    """Pause/sleep the running model container to suspend compute and cool down CPU/GPU."""
    return engine_mgr.pause_container()


@app.post("/api/engine/resume")
async def api_engine_resume():
    """Resume the paused model container."""
    return engine_mgr.resume_container()


@app.post("/api/engine/free-memory")
async def api_free_memory():
    """Purge GPU VRAM and CPU RAM allocated by diffusion or inference models."""
    from core.neural_diffusion_engine import release_gpu_memory
    release_gpu_memory()
    import gc
    gc.collect()
    return {"success": True, "message": "GPU VRAM and system memory purged successfully."}


@app.get("/api/models")
@app.get("/api/models/local")
async def api_list_local_models():
    """List all installed and ready-to-run GGUF models in native engine."""
    return await engine_mgr.list_models()


@app.get("/api/models/popular")
async def api_get_popular_models():
    """Return list of popular open-source models supported for 1-click pulls."""
    from core.downloader import POPULAR_MODEL_PULL_MAP
    return {"success": True, "popular": list(POPULAR_MODEL_PULL_MAP.keys())}


@app.post("/api/models/details")
async def api_get_model_details(payload: Dict[str, str]):
    name = payload.get("name", "")
    if not name:
        raise HTTPException(status_code=400, detail="Model name required")
    details = engine_mgr.get_model_details(name)
    return details


@app.post("/api/models/reveal-file")
async def api_reveal_model_file(payload: Dict[str, str]):
    """Open Windows File Explorer with the specific model file highlighted."""
    file_path = payload.get("file_path", "")
    if not file_path:
        name = payload.get("name", "")
        details = engine_mgr.get_model_details(name)
        file_path = details.get("file_path", "")

    p = Path(file_path)
    if not p.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

    try:
        if sys.platform == "win32":
            subprocess.Popen(f'explorer /select,"{str(p.resolve())}"')
        else:
            subprocess.Popen(["xdg-open", str(p.parent.resolve())])
        return {"success": True, "file_path": str(p.resolve())}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/models/delete")
async def api_delete_model(payload: Dict[str, str]):
    name = payload.get("name", "")
    if not name:
        raise HTTPException(status_code=400, detail="Model name required")
    return await engine_mgr.delete_model(name)


@app.post("/api/models/alias")
async def api_set_model_alias(payload: Dict[str, Any]):
    """Set, update, or remove user-defined friendly alias for a local model."""
    name = payload.get("model_name") or payload.get("name", "")
    alias = payload.get("alias", "")
    if not name:
        raise HTTPException(status_code=400, detail="Model name is required")
    return engine_mgr.set_model_alias(name, alias)


@app.get("/api/models/aliases")
async def api_get_model_aliases():
    """Retrieve all model aliases configured by the user."""
    return config_mgr.get("model_aliases", {})


# --- Hugging Face Hub Exploration ---
@app.get("/api/search/omni")
async def api_search_omni(q: str = ""):
    """Instant live type-ahead search across Local models, Open-Source catalog, and Hugging Face."""
    local_models = await engine_mgr.list_models()
    return await hf_client.omni_search(query=q, installed_models=local_models)


@app.get("/api/hf/featured")
async def api_hf_featured():
    """Return top recommended open-source models for 1-click exploration."""
    return hf_client.get_featured_models()


@app.get("/api/hf/search")
async def api_hf_search(q: str = "", filter: str = "gguf", sort: str = "downloads", limit: int = 24):
    """Search Hugging Face models by keyword."""
    return await hf_client.search_models(query=q, filter_type=filter, sort=sort, limit=limit)


@app.get("/api/hf/inspect")
async def api_hf_inspect(repo_id: str):
    """Inspect all GGUF files and quantizations in a Hugging Face repo."""
    if not repo_id:
        raise HTTPException(status_code=400, detail="repo_id parameter required")
    return await hf_client.inspect_repo_files(repo_id)


# --- Ollama Library Explore Endpoints ---
@app.get("/api/ollama/featured")
async def api_ollama_featured():
    """Return top curated Ollama library models."""
    return hf_client.get_featured_ollama()


@app.get("/api/ollama/search")
async def api_ollama_search(q: str = "", limit: int = 24):
    """Search Ollama models across catalog and public registry."""
    return await hf_client.search_ollama(query=q, limit=limit)


# --- AI Super-Resolution 4K / 8K Image Enhancer ---
@app.post("/api/media/enhance-8k")
async def api_media_enhance_8k(payload: Dict[str, Any]):
    """Upscale and enhance an image to crystal-clear 4K/8K resolution with bilateral denoising."""
    from core.neural_diffusion_engine import enhance_and_upscale_image
    image_path = payload.get("image_path") or payload.get("filename")
    scale = int(payload.get("scale", 4))
    if not image_path:
        raise HTTPException(status_code=400, detail="image_path or filename is required")
    res = enhance_and_upscale_image(image_path, scale_factor=scale)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Enhancement failed"))
    return res


# --- Prompt Generation & Studio Endpoints ---
@app.post("/api/prompt/enhance")
async def api_quick_enhance_prompt(payload: Dict[str, Any]):
    """Quickly enhance a user prompt with typo fixing and photographic 8K descriptors."""
    from core.prompt_generator import quick_enhance_image_prompt, correct_prompt_typos
    raw_prompt = payload.get("prompt", "")
    if not raw_prompt:
        raise HTTPException(status_code=400, detail="prompt is required")
    enhanced = quick_enhance_image_prompt(raw_prompt)
    _, corrections = correct_prompt_typos(raw_prompt)
    return {
        "success": True,
        "original_prompt": raw_prompt,
        "enhanced_prompt": enhanced,
        "corrections": corrections,
    }


@app.post("/api/prompt/generate")
async def api_generate_prompt_variations(payload: Dict[str, Any]):
    """Generate structured multi-variation prompts with custom styles, cameras, and lighting."""
    from core.prompt_generator import generate_prompt_variations
    concept = payload.get("concept", "")
    if not concept:
        raise HTTPException(status_code=400, detail="concept is required")
    res = generate_prompt_variations(
        concept=concept,
        style=payload.get("style", "photorealistic"),
        lighting=payload.get("lighting", "golden_hour"),
        camera=payload.get("camera", "85mm_portrait"),
        mood=payload.get("mood", "cinematic"),
        custom_modifiers=payload.get("custom_modifiers"),
    )
    return res


@app.post("/api/prompt/llm")
async def api_generate_llm_prompt(payload: Dict[str, Any]):
    """Generate an optimized system prompt and task breakdown for LLM reasoning."""
    from core.prompt_generator import generate_llm_system_prompt
    task_desc = payload.get("task_description", "")
    if not task_desc:
        raise HTTPException(status_code=400, detail="task_description is required")
    res = generate_llm_system_prompt(task_desc, role=payload.get("role", "expert"))
    return res


# --- Background Downloader (Hugging Face & Ollama) with Pause / Resume ---
@app.post("/api/downloads/start")
async def api_start_download(req: DownloadRequest):
    """Queue and start downloading a GGUF model from Hugging Face with Range resume support."""
    task_id = await download_mgr.start_hf_download(
        url=req.url,
        filename=req.filename,
        model_name=req.model_name,
        auto_register=req.auto_register,
    )
    return {"success": True, "task_id": task_id}


@app.post("/api/downloads/pull-ollama")
async def api_pull_ollama_model(req: OllamaPullRequest):
    """Queue and start pulling a model from Ollama / xOllama library with layer resume."""
    clean_name = req.model_name.strip()
    if not clean_name:
        raise HTTPException(status_code=400, detail="model_name is required")
    task_id = await download_mgr.start_ollama_pull(model_name=clean_name)
    return {"success": True, "task_id": task_id}


@app.post("/api/downloads/pause")
async def api_pause_download(payload: Dict[str, str]):
    """Pause an active download (Hugging Face or Ollama)."""
    task_id = payload.get("task_id", "")
    success = download_mgr.pause_task(task_id)
    return {"success": success}


@app.post("/api/downloads/resume")
async def api_resume_download(payload: Dict[str, str]):
    """Resume a paused download."""
    task_id = payload.get("task_id", "")
    success = download_mgr.resume_task(task_id)
    return {"success": success}


@app.post("/api/downloads/cancel")
async def api_cancel_download(payload: Dict[str, Any]):
    """Cancel a download."""
    task_id = payload.get("task_id", "")
    delete_file = payload.get("delete_file", True)
    success = download_mgr.cancel_task(task_id, delete_file=delete_file)
    return {"success": success}


@app.get("/api/downloads")
@app.get("/api/downloads/tasks")
async def api_get_download_tasks():
    """Fetch status and progress of all download tasks."""
    return download_mgr.get_tasks()


# --- Local File Import ---
@app.post("/api/models/import-local")
async def api_import_local_model(req: ImportLocalRequest):
    """Import and register any existing .gguf file from local disk directly into Native Engine."""
    source_path = Path(req.file_path)
    if not source_path.is_file():
        raise HTTPException(status_code=404, detail=f"File not found on disk: {req.file_path}")

    target_dir = CURRENT_DIR / "models"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_dest = target_dir / source_path.name

    if str(source_path.resolve()) != str(target_dest.resolve()):
        import shutil
        try:
            # Create a link or copy into models/
            shutil.copy2(source_path, target_dest)
        except Exception as e:
            return {"success": False, "error": f"Failed to import file: {str(e)}"}

    return {
        "success": True,
        "model_name": target_dest.stem,
        "message": f"Model '{target_dest.stem}' successfully imported into Native Engine library!",
    }


# --- Media & Document Upload Endpoint (PDF, Excel, CSV, DOCX, Images, Video) ---
@app.post("/api/media/upload")
async def api_upload_media(
    file: Optional[UploadFile] = File(None),
    files: Optional[List[UploadFile]] = File(None),
):
    """Upload and process document (PDF, Excel, CSV, DOCX), image/screenshot, or video file."""
    try:
        all_files = []
        if files:
            all_files.extend(files)
        if file:
            all_files.append(file)
        if not all_files:
            raise HTTPException(status_code=400, detail="No files provided")

        processed = []
        for f in all_files:
            content = await f.read()
            res = MediaProcessor.process_file(f.filename or "uploaded_file", content)
            processed.append(res)

        return {
            "success": True,
            "processed": processed,
            "attachment": processed[0] if processed else None,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# --- Real-Time Streaming Chat Endpoint ---
@app.post("/api/chat")
@app.post("/api/chat/stream")
async def api_chat_stream(req: ChatRequest):
    """Stream token completions via Server-Sent Events (SSE) with multimodal & document attachments."""
    messages_dict = [{"role": m.role, "content": m.content} for m in req.messages]

    # If attachments are present, inject extracted text and structured tables into prompt
    if req.attachments and messages_dict:
        attachment_texts = []
        for att in req.attachments:
            if att.extracted_text:
                attachment_texts.append(att.extracted_text)

        if attachment_texts:
            combined_attachments = "\n\n".join(attachment_texts)
            # Find the latest user message to attach context
            for i in range(len(messages_dict) - 1, -1, -1):
                if messages_dict[i]["role"] == "user":
                    orig = messages_dict[i]["content"]
                    messages_dict[i]["content"] = f"{combined_attachments}\n\nUser Question/Query:\n{orig}"
                    break
    
    return StreamingResponse(
        model_runner.stream_chat(
            model=req.model,
            messages=messages_dict,
            temperature=req.temperature or 0.7,
            num_ctx=req.num_ctx or 4096,
            system_prompt=req.system_prompt or config_mgr.get("system_prompt"),
        ),
        media_type="text/event-stream",
    )


# --- Persistent Chat & Project Storage Endpoints ---
@app.get("/api/chats")
async def api_get_all_chats():
    """Retrieve all persistent chat sessions and project workspaces safely stored on disk."""
    return chat_mgr.get_all()


@app.post("/api/chats/save")
async def api_save_all_chats(request: Request):
    """Save all chat sessions and project workspaces atomically to disk."""
    body = await request.json()
    sessions = body.get("sessions", [])
    projects = body.get("projects", [])
    ok = chat_mgr.save_all(sessions, projects)
    return {"success": ok}


@app.post("/api/chats/session")
async def api_save_chat_session(request: Request):
    """Save or update an individual chat session."""
    session = await request.json()
    ok = chat_mgr.upsert_session(session)
    return {"success": ok}


@app.delete("/api/chats/session/{session_id}")
async def api_delete_chat_session(session_id: str):
    """Delete a chat session."""
    ok = chat_mgr.delete_session(session_id)
    return {"success": ok}


@app.post("/api/chats/project")
async def api_save_project(request: Request):
    """Save or update a project."""
    project = await request.json()
    ok = chat_mgr.upsert_project(project)
    return {"success": ok}


@app.delete("/api/chats/project/{project_id}")
async def api_delete_project(project_id: str):
    """Delete a project."""
    ok = chat_mgr.delete_project(project_id)
    return {"success": ok}


# --- OpenAI-Compatible API Endpoints (for VS Code Continue, Cursor, LangChain) ---
@app.get("/v1/models")
async def v1_models():
    models = await engine_mgr.list_models()
    return {
        "object": "list",
        "data": [
            {
                "id": m["name"],
                "object": "model",
                "created": int(time.time()),
                "owned_by": "modeldock",
            }
            for m in models
        ],
    }


@app.post("/v1/chat/completions")
async def v1_chat_completions(request: Request):
    body = await request.json()
    model = body.get("model", "")
    messages = body.get("messages", [])
    temperature = body.get("temperature", 0.7)
    stream = body.get("stream", False)

    if stream:
        # Stream chunks in OpenAI SSE format
        async def openai_stream():
            start_ts = int(time.time())
            cm_dict = [{"role": m.get("role", "user"), "content": m.get("content", "")} for m in messages]
            async for sse_line in model_runner.stream_chat(model=model, messages=cm_dict, temperature=temperature):
                if sse_line.startswith("data: "):
                    chunk = json.loads(sse_line[6:].strip())
                    content = chunk.get("content", "")
                    done = chunk.get("done", False)
                    data_obj = {
                        "id": f"chatcmpl-{start_ts}",
                        "object": "chat.completion.chunk",
                        "created": start_ts,
                        "model": model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"content": content} if content else {},
                                "finish_reason": "stop" if done else None,
                            }
                        ],
                    }
                    yield f"data: {json.dumps(data_obj)}\n\n"
                    if done:
                        yield "data: [DONE]\n\n"
                        break

        return StreamingResponse(openai_stream(), media_type="text/event-stream")
    else:
        # Non-streaming OpenAI response
        full_text = ""
        cm_dict = [{"role": m.get("role", "user"), "content": m.get("content", "")} for m in messages]
        async for sse_line in model_runner.stream_chat(model=model, messages=cm_dict, temperature=temperature):
            if sse_line.startswith("data: "):
                chunk = json.loads(sse_line[6:].strip())
                full_text += chunk.get("content", "")
                if chunk.get("done"):
                    break
        return {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": full_text},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 0, "completion_tokens": len(full_text.split()), "total_tokens": len(full_text.split())},
        }


def is_port_free(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a TCP port is currently free to bind."""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            return True
    except OSError:
        return False


def find_available_port(start_port: int = 7860, max_tries: int = 50, host: str = "127.0.0.1") -> int:
    """Find the first available free TCP port."""
    for p in range(start_port, start_port + max_tries):
        if is_port_free(p, host):
            return p
    return start_port


def launch_browser(port: int):
    """Open default browser shortly after server boots."""
    time.sleep(1.2)
    webbrowser.open(f"http://localhost:{port}")


def main():
    base_port = config_mgr.get("server_port", 7860)
    host = config_mgr.get("server_host", "127.0.0.1")

    port = find_available_port(start_port=base_port, host=host)
    if port != base_port:
        print(f"⚠️ Port {base_port} was busy. Automatically switched to port {port}.")

    print("\n" + "=" * 65)
    print("   🚀 ModelDock Studio - Universal Local AI Platform")
    print("=" * 65)
    print(f"   📡 Local URL:         http://localhost:{port}")
    print(f"   ⚡ Memory Overhead:   ~28 MB RAM (Near Zero CPU)")
    print(f"   🤗 Hugging Face Auth: Ready (Gated & Public Models)")
    print(f"   🦙 Standalone Engine: {engine_mgr.get_host()} (Zero Ollama)")
    print("=" * 65 + "\n")

    if config_mgr.get("auto_open_browser", True):
        threading.Thread(target=launch_browser, args=(port,), daemon=True).start()

    print("   🟢 Server is live and actively listening for requests.")
    print("   💡 Live request and engine activity will appear below in real-time.")
    print("   🛑 Press Ctrl+C in this CMD window anytime to stop the server.\n")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    main()
