import json
import os
import re

log_dirs = [
    r'C:\Users\yashm\.gemini\antigravity\brain\b9423ef0-14e4-4439-81f7-2931a1cab712\.system_generated\logs',
    r'C:\Users\yashm\.gemini\antigravity\brain\ed921345-847d-4fd1-b190-66a83a846bdc\.system_generated\logs',
    r'C:\Users\yashm\.gemini\antigravity\brain\61ac620b-fa14-4f1d-94cf-d1f6d1117cb2\.system_generated\logs'
]

targets = ['chatbot.py', 'ml.py', 'voice.py', 'ai_services.py', 'genai_services.py', 'ml_models.py', 'voice_service.py', 'chatbot.html', 'voice_agent.html', 'ai_insights.html', 'ml_dashboard.html', 'ai.css', 'ai.js']

found = {}

for ld in log_dirs:
    p = os.path.join(ld, 'overview.txt')
    if not os.path.exists(p): continue
    with open(p, 'r', encoding='utf-8') as f:
        for line in f:
            if 'write_to_file' in line:
                try:
                    idx = line.find('{')
                    if idx != -1:
                        data = json.loads(line[idx:])
                        # Since tool calls in overview.txt look like:
                        # {"step_index":X, ... "tool_calls":[{"name":"write_to_file", "args": {...}}]}
                        if 'tool_calls' in data:
                            for tc in data['tool_calls']:
                                if tc.get('name') == 'write_to_file':
                                    args = tc.get('args', {})
                                    if type(args) == str:
                                        args = json.loads(args)
                                    tf = args.get('TargetFile', '').replace('"', '')
                                    for t in targets:
                                        if tf.endswith(t):
                                            found[t] = args.get('CodeContent', '')
                except Exception as e:
                    pass

for k, v in found.items():
    print(k, len(v))
    out_path = k
    if k.endswith('.py') and not k.endswith('_services.py') and not k.endswith('models.py') and k != 'ai_services.py':
        out_path = os.path.join('routes', k)
    elif k.endswith('_services.py') or k == 'ml_models.py' or k == 'ai_services.py':
        out_path = os.path.join('services', k)
    elif k.endswith('.html'):
        if k in ['chatbot.html', 'voice_agent.html']:
            out_path = os.path.join('templates', 'ai', k)
        elif k == 'ai_insights.html':
            out_path = os.path.join('templates', 'admin', k)
        elif k == 'ml_dashboard.html':
            out_path = os.path.join('templates', 'ml', k)
    elif k.endswith('.css'):
        out_path = os.path.join('static', 'css', k)
    elif k.endswith('.js'):
        out_path = os.path.join('static', 'js', k)
        
    os.makedirs(os.path.dirname(os.path.join(r'd:\Python\Employee', out_path)) or '.', exist_ok=True)
    with open(os.path.join(r'd:\Python\Employee', out_path), 'w', encoding='utf-8') as f:
        # Strip quotes if they exist around the content
        val = str(v)
        if val.startswith('"') and val.endswith('"'):
            val = val[1:-1]
        val = val.replace(r'\n', '\n').replace(r'\"', '"')
        f.write(val)
