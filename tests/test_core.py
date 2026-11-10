"""
ModelDock Studio - Test Suite
Verifies configuration, telemetry, Hugging Face Hub integration, engine detection, and API endpoints.
"""

import sys
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from starlette.testclient import TestClient

from core.config import ConfigManager
from core.system_monitor import get_full_system_status
from core.auth_manager import AuthManager
from core.engine_manager import EngineManager
from core.hf_hub import HFHubClient
from core.modelfile_builder import generate_modelfile_content
from run import app


def test_config_manager():
    cfg = ConfigManager.get_instance()
    assert cfg.get("server_port") == 7860
    assert cfg.get("downloads_dir") is not None
    assert "ollama_host" in cfg.data


def test_system_telemetry():
    telemetry = get_full_system_status()
    assert "software" in telemetry
    assert "host" in telemetry
    assert "gpu" in telemetry
    assert telemetry["software"]["ram_mb"] > 0
    assert telemetry["host"]["total_ram_gb"] > 0
    print(f"\n[Test] Software RAM: {telemetry['software']['ram_mb']} MB (Lean and fast)")


def test_auth_manager_headers():
    auth = AuthManager()
    headers = auth.get_auth_headers()
    assert isinstance(headers, dict)


def test_engine_manager_discovery():
    engine = EngineManager()
    host = engine.get_host()
    assert host.startswith("http://")
    binary = engine.get_server_binary()
    assert binary.is_file(), f"llama-server binary must exist at {binary}"
    models = engine.list_installed_models()
    assert len(models) >= 1, "At least one local GGUF model must be discovered"
    print(f"\n[Test] Native Engine Host: {host} | Models found: {[m['name'] for m in models]}")


@pytest.mark.asyncio
async def test_native_model_generation():
    """Verify that local GGUF model generates tokens end-to-end without Ollama!"""
    from core.model_runner import ModelRunner
    engine = EngineManager()
    models = engine.list_installed_models()
    assert len(models) > 0
    test_model = models[0]["name"]
    runner = ModelRunner(engine=engine)

    received_text = ""
    async for sse in runner.stream_chat(
        model=test_model,
        messages=[{"role": "user", "content": "Count: 1, 2, 3"}],
        temperature=0.1,
    ):
        if sse.startswith("data: "):
            chunk = json.loads(sse[6:].strip())
            received_text += chunk.get("content", "")

    assert len(received_text.strip()) > 0, "Model must generate response tokens"
    print(f"\n[Test] Native Model Output: '{received_text.strip()}' (Zero Ollama!)")
    engine.stop_server()


def test_hf_hub_featured_models():
    client = HFHubClient()
    featured = client.get_featured_models()
    assert len(featured) >= 5
    for m in featured:
        assert "id" in m
        assert "name" in m
        assert "parameters" in m


def test_modelfile_generator():
    content = generate_modelfile_content(
        gguf_path="C:/models/test_model.gguf",
        context_length=8192,
        temperature=0.8,
        system_prompt="Test system prompt",
    )
    assert 'FROM "C:/models/test_model.gguf"' in content
    assert "PARAMETER num_ctx 8192" in content
    assert "PARAMETER temperature 0.8" in content
    assert 'SYSTEM "Test system prompt"' in content


def test_fastapi_endpoints():
    client = TestClient(app)
    
    # 1. Index page
    res_index = client.get("/")
    assert res_index.status_code == 200
    assert "ModelDock Studio" in res_index.text

    # 2. Telemetry endpoint
    res_sys = client.get("/api/system/status")
    assert res_sys.status_code == 200
    data_sys = res_sys.json()
    assert data_sys["software"]["name"] == "ModelDock Studio"

    # 3. Config endpoint (masks token)
    res_cfg = client.get("/api/config")
    assert res_cfg.status_code == 200
    data_cfg = res_cfg.json()
    assert "hf_token" not in data_cfg

    # 4. HF Featured
    res_feat = client.get("/api/hf/featured")
    assert res_feat.status_code == 200
    assert len(res_feat.json()) >= 5

    # 5. Local Models
    res_models = client.get("/api/models/local")
    assert res_models.status_code == 200
    models = res_models.json()
    print(f"\n[Test] Local Models Discovered ({len(models)}): {[m['name'] for m in models]}")

    # 6. OpenAI compatible v1/models endpoint
    res_v1 = client.get("/v1/models")
    assert res_v1.status_code == 200
    assert res_v1.json()["object"] == "list"

    # 7. Podman-Style Settings Endpoint
    res_settings = client.get("/api/settings")
    assert res_settings.status_code == 200
    data_settings = res_settings.json()
    assert "cpu_threads" in data_settings
    assert "gpu_mode" in data_settings
    assert "system_cpu_count" in data_settings

    # 8. Settings Update Endpoint
    res_update = client.post("/api/settings/update", json={"cpu_threads": 4, "gpu_mode": "auto"})
    assert res_update.status_code == 200
    assert res_update.json()["success"] is True

    # 9. Omni Type-Ahead Instant Search Endpoint
    res_omni = client.get("/api/search/omni?q=deepseek")
    assert res_omni.status_code == 200
    data_omni = res_omni.json()
    assert "catalog" in data_omni
    assert "huggingface" in data_omni
    assert len(data_omni["catalog"]) > 0


@pytest.mark.asyncio
async def test_downloader_pause_resume():
    from core.downloader import DownloadManager, _DOWNLOAD_TASKS
    dm = DownloadManager()

    # 1. Test HF Download Task creation & pause
    test_url = "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf"
    task_id = await dm.start_hf_download(
        url=test_url,
        filename="test_pause_resume.gguf",
        model_name="test-pause-resume",
        auto_register=False,
    )
    assert task_id.startswith("dl_hf_")
    
    # Verify task in registry
    task = dm.get_task(task_id)
    assert task is not None
    assert task["platform"] == "huggingface"

    # Test pause
    paused = dm.pause_task(task_id)
    assert paused is True

    # Test resume (accepts pausing or paused)
    resumed = dm.resume_task(task_id)
    assert resumed is True

    # Test cancel with file deletion
    cancelled = dm.cancel_task(task_id, delete_file=True)
    assert cancelled is True
    assert dm.get_task(task_id)["status"] == "cancelled"


@pytest.mark.asyncio
async def test_ollama_pull_pause_resume():
    from core.downloader import DownloadManager
    dm = DownloadManager()

    # Test Ollama Pull creation
    task_id = await dm.start_ollama_pull(model_name="llama3.2:1b")
    assert task_id.startswith("dl_ol_")
    task = dm.get_task(task_id)
    assert task["platform"] == "ollama"
    assert task["model_name"] == "llama3.2:1b"

    # Test pause
    paused = dm.pause_task(task_id)
    assert paused is True

    # Test resume
    resumed = dm.resume_task(task_id)
    assert resumed is True

    # Test cancel
    cancelled = dm.cancel_task(task_id)
    assert cancelled is True
    assert dm.get_task(task_id)["status"] == "cancelled"


def test_download_endpoints():
    client = TestClient(app)

    # 1. Start HF download endpoint
    res_hf = client.post(
        "/api/downloads/start",
        json={
            "url": "https://huggingface.co/test/model.gguf",
            "filename": "test_endpoint.gguf",
            "model_name": "test-endpoint",
            "auto_register": False,
        },
    )
    assert res_hf.status_code == 200
    task_id_hf = res_hf.json()["task_id"]

    # 2. Pause endpoint
    res_pause = client.post("/api/downloads/pause", json={"task_id": task_id_hf})
    assert res_pause.status_code == 200

    # 3. Cancel endpoint
    res_cancel = client.post("/api/downloads/cancel", json={"task_id": task_id_hf, "delete_file": True})
    assert res_cancel.status_code == 200
    assert res_cancel.json()["success"] is True

    # 4. Pull Ollama endpoint
    res_ol = client.post(
        "/api/downloads/pull-ollama",
        json={"model_name": "llama3.2:1b"},
    )
    assert res_ol.status_code == 200
    task_id_ol = res_ol.json()["task_id"]

    # Cancel Ollama pull
    client.post("/api/downloads/cancel", json={"task_id": task_id_ol})


def test_gguf_metadata_parser():
    from core.gguf_parser import parse_gguf_metadata
    engine = EngineManager()
    models = engine.list_installed_models()
    assert len(models) >= 1
    m0 = models[0]
    meta = parse_gguf_metadata(m0["file_path"])
    assert "architecture" in meta
    assert "context_length" in meta
    assert meta["context_length"] > 0
    assert "tensor_count" in meta
    assert meta["tensor_count"] > 0
    assert "block_count" in meta
    assert "estimated_vram" in meta
    print(f"\n[Test] Parsed GGUF specs: {meta['architecture']} {meta['parameter_size']} ({meta['context_formatted']})")


def test_model_details_endpoint():
    client = TestClient(app)
    # Fetch local models list
    res_list = client.get("/api/models/local")
    assert res_list.status_code == 200
    models = res_list.json()
    assert len(models) >= 1

    first_model = models[0]
    # Request specs details for this model
    res_details = client.post("/api/models/details", json={"name": first_model["name"]})
    assert res_details.status_code == 200
    details = res_details.json()
    assert details["name"] == first_model["name"]
    assert "block_count" in details
    assert "context_length" in details
    assert "embedding_length" in details
    assert "tensor_count" in details
    assert "estimated_vram" in details
    assert "file_path" in details
    print(f"\n[Test] Details Endpoint returned: {details['name']} -> {details['block_count']} layers, {details['context_length']} ctx, {details['estimated_vram']}")


def test_persistent_chat_storage():
    """Verify that ChatManager creates, saves, and retrieves chat sessions and projects from disk."""
    from core.chat_manager import ChatManager
    chat_mgr = ChatManager.get_instance()
    
    # Save a test session
    session_id = "test_sess_persistent_1"
    test_session = {
        "id": session_id,
        "title": "Persistent Test Conversation",
        "projectId": None,
        "timestamp": 12345678,
        "messages": [
            {"role": "user", "content": "Hello persistence test", "timestamp": "12:00 PM"},
            {"role": "assistant", "content": "I will persist across refreshes!", "timestamp": "12:01 PM"}
        ],
        "pinned": False,
    }
    ok = chat_mgr.upsert_session(test_session)
    assert ok is True

    # Retrieve and verify
    loaded = chat_mgr.get_session(session_id)
    assert loaded is not None
    assert loaded["title"] == "Persistent Test Conversation"
    assert len(loaded["messages"]) == 2

    # Clean up test session
    chat_mgr.delete_session(session_id)
    assert chat_mgr.get_session(session_id) is None


def test_chat_endpoints():
    """Verify /api/chats GET and POST /api/chats/save endpoints."""
    client = TestClient(app)
    # 1. GET all chats
    res = client.get("/api/chats")
    assert res.status_code == 200
    data = res.json()
    assert "sessions" in data
    assert "projects" in data

    # 2. POST save chats
    save_res = client.post("/api/chats/save", json={
        "sessions": [
            {
                "id": "test_api_session_1",
                "title": "API Test Chat",
                "projectId": None,
                "timestamp": 99999,
                "messages": [{"role": "user", "content": "Hi"}],
                "pinned": False
            }
        ],
        "projects": data.get("projects", [])
    })
    assert save_res.status_code == 200
    assert save_res.json().get("success") is True

    # 3. Clean up
    del_res = client.delete("/api/chats/session/test_api_session_1")
    assert del_res.status_code == 200


def test_nav_position_options():
    """Verify that nav_position supports left, top, right, bottom, and down."""
    client = TestClient(app)
    for pos in ["left", "top", "right", "bottom", "down"]:
        res = client.post("/api/settings/update", json={"nav_position": pos})
        assert res.status_code == 200
        assert res.json().get("success") is True

        cfg_res = client.get("/api/settings")
        assert cfg_res.status_code == 200
        expected = "bottom" if pos == "down" else pos
        assert cfg_res.json().get("nav_position") == expected

    # Reset back to left
    client.post("/api/settings/update", json={"nav_position": "left"})


def test_user_profile_settings():
    """Verify that user_name and user_title can be customized and persisted via settings API."""
    client = TestClient(app)
    # Update profile
    up_res = client.post("/api/settings/update", json={
        "user_name": "Test Explorer",
        "user_title": "AI Specialist"
    })
    assert up_res.status_code == 200
    assert up_res.json().get("success") is True

    # Read back settings
    get_res = client.get("/api/settings")
    assert get_res.status_code == 200
    cfg = get_res.json()
    assert cfg.get("user_name") == "Test Explorer"
    assert cfg.get("user_title") == "AI Specialist"


def test_hf_inspect_file_sizes():
    """Verify that inspect endpoint returns size_formatted and recommended_size."""
    client = TestClient(app)
    repo = "unsloth/DeepSeek-R1-Distill-Qwen-7B-GGUF"
    res = client.get(f"/api/hf/inspect?repo_id={repo}")
    assert res.status_code == 200
    data = res.json()
    assert "recommended_size" in data
    assert "architecture" in data
    assert "estimated_vram" in data
    assert "files" in data
    assert len(data["files"]) > 0
    # Check that at least one file has formatted size
    first_file = data["files"][0]
    assert "quantization" in first_file
    assert "size_formatted" in first_file
    print(f"\n[Test] HF Inspect: {data['name']} -> rec_size={data['recommended_size']}, first_file_size={first_file['size_formatted']}")


def test_sliding_window_context_pruning():
    """Verify that long conversation history exceeding context window is safely pruned."""
    from core.model_runner import prune_messages_for_context, estimate_tokens

    # Construct conversation history totaling ~7,000 tokens
    messages = [
        {"role": "system", "content": "You are a concise assistant."},
    ]
    # Add multiple long messages
    for i in range(15):
        messages.append({"role": "user", "content": f"User query turn {i} with long data: " + ("lorem ipsum " * 80)})
        messages.append({"role": "assistant", "content": f"Assistant response turn {i}: " + ("technical explanation " * 80)})

    latest_prompt = "What is the summary of our discussion?"
    messages.append({"role": "user", "content": latest_prompt})

    # Estimate total raw tokens
    total_tokens = sum(estimate_tokens(m["content"]) for m in messages)
    assert total_tokens > 5000, f"Expected > 5000 tokens, got {total_tokens}"

    # Prune for a 4096 context window with 1024 reserved
    pruned = prune_messages_for_context(messages, max_context=4096, reserve_generation=1024)

    pruned_tokens = sum(estimate_tokens(m["content"]) for m in pruned)
    assert pruned_tokens <= (4096 - 1024), f"Pruned tokens {pruned_tokens} must be <= 3072"
    assert pruned[0]["role"] == "system"
    assert pruned[-1]["content"] == latest_prompt
    print(f"\n[Test] Context Pruning: {total_tokens} tokens reduced to {pruned_tokens} tokens (Safe for 4096 window).")


def test_model_alias_management():
    """Verify that model alias can be set, retrieved, and affects list_models."""
    engine = EngineManager()
    models = engine.list_installed_models()
    assert len(models) > 0
    test_model = models[0]["name"]

    # 1. Set custom alias
    res = engine.set_model_alias(test_model, "Super Test AI")
    assert res["success"] is True
    assert res["alias"] == "Super Test AI"

    # 2. Verify list_installed_models reflects the alias
    updated = engine.list_installed_models()
    matching = next(m for m in updated if m["name"] == test_model)
    assert matching["alias"] == "Super Test AI"
    assert matching["display_name"] == "Super Test AI"

    # 3. Clean up / revert alias to default
    res_clear = engine.set_model_alias(test_model, "")
    assert res_clear["success"] is True
    reverted = engine.list_installed_models()
    reverted_m = next(m for m in reverted if m["name"] == test_model)
    assert reverted_m["alias"] == ""
    assert reverted_m["display_name"] == test_model
    print("\n[Test] Model alias successfully set, verified in listing, and reverted to default.")


def test_model_alias_management():
    """Verify that model alias can be set, retrieved, and affects list_models."""
    engine = EngineManager()
    models = engine.list_installed_models()
    assert len(models) > 0
    test_model = models[0]["name"]

    # 1. Set custom alias
    res = engine.set_model_alias(test_model, "Super Test AI")
    assert res["success"] is True
    assert res["alias"] == "Super Test AI"

    # 2. Verify list_installed_models reflects the alias
    updated = engine.list_installed_models()
    matching = next(m for m in updated if m["name"] == test_model)
    assert matching["alias"] == "Super Test AI"
    assert matching["display_name"] == "Super Test AI"

    # 3. Clean up / revert alias to default
    res_clear = engine.set_model_alias(test_model, "")
    assert res_clear["success"] is True
    reverted = engine.list_installed_models()
    reverted_m = next(m for m in reverted if m["name"] == test_model)
    assert reverted_m["alias"] == ""
    assert reverted_m["display_name"] == test_model
    print("\n[Test] Model alias successfully set, verified in listing, and reverted to default.")


if __name__ == "__main__":
    pytest.main(["-v", str(__file__)])


def test_split_shard_detection_and_error_handling():
    """Verify that multi-part split GGUF shards are accurately flagged and blocked from silent failure."""
    engine = EngineManager()
    models = engine.list_installed_models()
    split_model = next((m for m in models if "00002-of-00002" in m["name"]), None)
    if split_model:
        assert split_model["is_incomplete_split"] is True
        assert "Part 1" in split_model["split_warning"]
        res = engine.start_model(split_model["name"])
        assert res["success"] is False
        assert "Incomplete multi-part" in res["error"]
        print(f"\n[Test] Split shard accurately blocked: {res['error']}")
