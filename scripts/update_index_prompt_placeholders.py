with open('static/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    'placeholder="You are an intelligent, helpful, and concise local AI assistant."',
    'placeholder="You are ModelDock, an intelligent, helpful, and concise local AI assistant."'
)

with open('static/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print('Updated static/index.html placeholders successfully')
