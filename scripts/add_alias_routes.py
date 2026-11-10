with open('run.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = """@app.post("/api/models/delete")
async def api_delete_model(payload: Dict[str, str]):
    name = payload.get("name", "")
    if not name:
        raise HTTPException(status_code=400, detail="Model name required")
    return await engine_mgr.delete_model(name)"""

replacement = """@app.post("/api/models/delete")
async def api_delete_model(payload: Dict[str, str]):
    name = payload.get("name", "")
    if not name:
        raise HTTPException(status_code=400, detail="Model name required")
    return await engine_mgr.delete_model(name)


@app.post("/api/models/alias")
async def api_set_model_alias(payload: Dict[str, Any]):
    \"\"\"Set, update, or remove user-defined friendly alias for a local model.\"\"\"
    name = payload.get("model_name") or payload.get("name", "")
    alias = payload.get("alias", "")
    if not name:
        raise HTTPException(status_code=400, detail="Model name is required")
    return engine_mgr.set_model_alias(name, alias)


@app.get("/api/models/aliases")
async def api_get_model_aliases():
    \"\"\"Retrieve all model aliases configured by the user.\"\"\"
    return config_mgr.get("model_aliases", {})"""

target_norm = target.replace("\r\n", "\n")
replacement_norm = replacement.replace("\r\n", "\n")
text_norm = text.replace("\r\n", "\n")

if target_norm not in text_norm:
    raise ValueError("target not found")

text_norm = text_norm.replace(target_norm, replacement_norm, 1)

with open('run.py', 'w', encoding='utf-8', newline='') as f:
    f.write(text_norm.replace('\n', '\r\n'))

print("Added alias routes to run.py successfully!")
