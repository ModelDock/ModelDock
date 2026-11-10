import asyncio
import httpx
from core.engine_manager import EngineManager

async def test():
    em = EngineManager()
    res = em.start_model('qwen2-0_5b-instruct-q4_k_m')
    print('Started:', res)
    host = em.get_host()
    url = f'{host}/v1/chat/completions'
    
    prompts = [
        'write python code for me for adding 2 value using class and function',
        'using only function now',
        'without class do that'
    ]
    messages = [{'role': 'system', 'content': 'You are a helpful programming assistant. Provide concise, accurate code.'}]
    
    async with httpx.AsyncClient(timeout=30) as client:
        for p in prompts:
            messages.append({'role': 'user', 'content': p})
            payload = {'messages': messages, 'temperature': 0.3, 'max_tokens': 150, 'stream': False}
            r = await client.post(url, json=payload)
            ans = r.json()['choices'][0]['message']['content']
            print(f'=== PROMPT: "{p}" ===')
            print(ans.strip())
            print()
            messages.append({'role': 'assistant', 'content': ans})
            
    em.stop_server()

if __name__ == "__main__":
    asyncio.run(test())
