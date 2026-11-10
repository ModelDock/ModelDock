with open("core/model_runner.py", "r", encoding="utf-8") as f:
    text = f.read()

target = '''            start_time = time.time()
            words = full_text.split(" ")
            token_count = 0
            for i, word in enumerate(words):
                token_chunk = word + (" " if i < len(words) - 1 else "")
                token_count += 1
                yield f"data: {json.dumps({'content': token_chunk, 'done': False})}\\n\\n"
                await asyncio.sleep(0.005)'''

repl = '''            start_time = time.time()
            chunk_size = 48
            token_count = 0
            for i in range(0, len(full_text), chunk_size):
                chunk = full_text[i:i + chunk_size]
                token_count += 1
                yield f"data: {json.dumps({'content': chunk, 'done': False})}\\n\\n"
                await asyncio.sleep(0.004)'''

assert target in text, "target not found in core/model_runner.py"
# Replace both occurrences (video and image)
text = text.replace(target, repl)

with open("core/model_runner.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Optimized streaming chunk size in core/model_runner.py successfully!")
