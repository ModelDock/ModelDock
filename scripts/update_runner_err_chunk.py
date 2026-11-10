from pathlib import Path

p = Path(r"a:\AI_Project_work\ollama_2nd_copy\core\model_runner.py")
content = p.read_text(encoding="utf-8")

old = '''            if not load_res.get("success"):
                err_chunk = {
                    "error": f"Failed to load model '{model}': {load_res.get('error')}",
                    "done": True,
                }
                yield f"data: {json.dumps(err_chunk)}\\n\\n"
                return'''

new = '''            if not load_res.get("success"):
                err_msg = load_res.get("error", "Engine failed to load model.")
                err_chunk = {
                    "error": f"**Failed to load model `{model}`**:\\n\\n{err_msg}\\n\\n💡 *Tip: Please switch to a complete model (such as `qwen2-0_5b-instruct-q4_k_m`) or download all split shards.*",
                    "content": f"⚠️ **Model Load Error**: {err_msg}",
                    "done": True,
                }
                yield f"data: {json.dumps(err_chunk)}\\n\\n"
                return'''

assert old in content, "old snippet not found in model_runner.py"
content = content.replace(old, new, 1)
p.write_text(content, encoding="utf-8")
print("Updated model_runner.py load failure error chunk.")
