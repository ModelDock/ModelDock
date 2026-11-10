import sys
import re
from pathlib import Path

path = Path(r"a:\AI_Project_work\ollama_2nd_copy\core\engine_manager.py")
content = path.read_text(encoding="utf-8")

# 1. Ensure 'import re' at top
if "import re" not in content:
    content = content.replace("import sys\n", "import sys\nimport re\n")

# 2. Update list_installed_models to add multi-part split detection
old_list_models_loop = '''                # Parse header metadata (<2ms)
                meta = parse_gguf_metadata(resolved_path)
                is_active = (resolved_path == str(self.active_model_path)) if self.active_model_path else False
                aliases = self.config.get("model_aliases", {})
                alias = aliases.get(f.stem) or aliases.get(f.name) or ""'''

new_list_models_loop = '''                # Parse header metadata (<2ms)
                meta = parse_gguf_metadata(resolved_path)
                is_active = (resolved_path == str(self.active_model_path)) if self.active_model_path else False
                aliases = self.config.get("model_aliases", {})
                alias = aliases.get(f.stem) or aliases.get(f.name) or ""

                # Detect multi-part split shards (e.g., model-00002-of-00002.gguf)
                is_split = False
                is_incomplete_split = False
                split_warning = ""
                split_match = re.search(r"-(\d{5})-of-(\d{5})\.gguf$", f.name, re.IGNORECASE)
                if split_match:
                    is_split = True
                    part_idx = int(split_match.group(1))
                    total_parts = int(split_match.group(2))
                    prefix = f.name[:f.name.rfind(f"-{split_match.group(1)}-of-")]
                    if part_idx != 1:
                        part1_name = f"{prefix}-00001-of-{split_match.group(2)}.gguf"
                        if not (f.parent / part1_name).is_file():
                            is_incomplete_split = True
                            split_warning = f"Incomplete Split: Shard {part_idx} of {total_parts}. Part 1 ({part1_name}) is missing."
                    else:
                        missing = [i for i in range(1, total_parts + 1) if not (f.parent / f"{prefix}-{i:05d}-of-{split_match.group(2)}.gguf").is_file()]
                        if missing:
                            is_incomplete_split = True
                            split_warning = f"Incomplete Split: Missing shard(s) {missing} of {total_parts}."'''

if old_list_models_loop in content:
    content = content.replace(old_list_models_loop, new_list_models_loop, 1)
else:
    print("Warning: old_list_models_loop not matched exactly")

# Add split fields into models.append dict
old_model_dict_entry = '''                    "author": meta.get("author", "Open Source"),
                    "license": meta.get("license", "Open Source"),
                })'''

new_model_dict_entry = '''                    "author": meta.get("author", "Open Source"),
                    "license": meta.get("license", "Open Source"),
                    "is_split": is_split,
                    "is_incomplete_split": is_incomplete_split,
                    "split_warning": split_warning,
                })'''

if old_model_dict_entry in content:
    content = content.replace(old_model_dict_entry, new_model_dict_entry, 1)
else:
    print("Warning: old_model_dict_entry not matched exactly")

path.write_text(content, encoding="utf-8")
print("Updated list_installed_models with split detection.")
