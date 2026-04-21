import sys, io, json, requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

r = requests.post('http://127.0.0.1:8000/api/legal/analyze', json={
    'user_input': '我要打官司',
    'uploaded_files': [],
    'session_id': '',
    'user_response': ''
}, timeout=600)

d = r.json()
print(json.dumps(d, ensure_ascii=False, indent=2)[:2000])
