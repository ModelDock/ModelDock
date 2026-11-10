with open('core/engine_manager.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update list_installed_models to include alias and display_name
target_meta = """                # Parse header metadata (<2ms)
                meta = parse_gguf_metadata(resolved_path)
                is_active = (resolved_path == str(self.active_model_path)) if self.active_model_path else False

                models.append({
                    "name": f.stem,
                    "filename": f.name,"""

replacement_meta = """                # Parse header metadata (<2ms)
                meta = parse_gguf_metadata(resolved_path)
                is_active = (resolved_path == str(self.active_model_path)) if self.active_model_path else False
                aliases = self.config.get("model_aliases", {})
                alias = aliases.get(f.stem) or aliases.get(f.name) or ""

                models.append({
                    "name": f.stem,
                    "filename": f.name,
                    "alias": alias,
                    "display_name": alias if alias else f.stem,"""

target_meta_norm = target_meta.replace("\r\n", "\n")
replacement_meta_norm = replacement_meta.replace("\r\n", "\n")
text_norm = text.replace("\r\n", "\n")

if target_meta_norm not in text_norm:
    raise ValueError("target_meta not found")

text_norm = text_norm.replace(target_meta_norm, replacement_meta_norm, 1)

# 2. Update start_model resolution to support alias
target_start = """            for m in self.list_installed_models():
                if m["name"] == model_identifier or m["filename"] == model_identifier:
                    target = Path(m["file_path"])
                    break"""

replacement_start = """            for m in self.list_installed_models():
                if m["name"] == model_identifier or m["filename"] == model_identifier or (m.get("alias") and m["alias"].lower() == model_identifier.lower()):
                    target = Path(m["file_path"])
                    break"""

target_start_norm = target_start.replace("\r\n", "\n")
replacement_start_norm = replacement_start.replace("\r\n", "\n")

if target_start_norm not in text_norm:
    raise ValueError("target_start not found")

text_norm = text_norm.replace(target_start_norm, replacement_start_norm, 1)

# 3. Add set_model_alias method to EngineManager
method_code = """    def set_model_alias(self, model_name: str, alias: str) -> Dict[str, Any]:
        \"\"\"Set, update, or remove user-defined friendly alias for a model.\"\"\"
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

    async def list_models(self) -> List[Dict[str, Any]]:"""

target_list = """    async def list_models(self) -> List[Dict[str, Any]]:"""

if target_list not in text_norm:
    raise ValueError("target_list not found")

text_norm = text_norm.replace(target_list, method_code, 1)

with open('core/engine_manager.py', 'w', encoding='utf-8', newline='') as f:
    f.write(text_norm.replace('\n', '\r\n'))

print("Updated core/engine_manager.py with alias support!")
