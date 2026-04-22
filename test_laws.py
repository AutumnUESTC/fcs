import requests, json, traceback

BASE = 'http://127.0.0.1:5000'

print("=" * 60)
print("模拟前端: 法规搜索 -> 输入'公司法'")
print("=" * 60)

# 1. 登录
r = requests.post(f'{BASE}/api/auth/login', json={'username': 'testuser_v3', 'password': 'TestPass123!'})
token = r.json()['data']['token']
h = {'Authorization': f'Bearer {token}'}
print(f"[1] Login: {r.status_code}")

# 2. 发送消息 (和前端 chat.js 完全一致)
try:
    r2 = requests.post(f'{BASE}/api/messages', json={
        'conversation_id': 'conv_laws_test',
        'content': '[法规查询] 公司法',   # 前端会加 [法规查询] 前缀
        'role': 'user'
    }, headers=h, timeout=120)
    
    print(f"[2] POST /api/messages")
    print(f"    HTTP Status: {r2.status_code}")
    print(f"    Content-Type: {r2.headers.get('content-type')}")
    
    body = r2.text[:3000]
    if body.startswith('{'):
        resp = r2.json()
        code = resp.get('code')
        msg = resp.get('message')
        data = resp.get('data', {})
        answer = data.get('answer', '')[:500] if 'answer' in data else 'NO ANSWER KEY'
        status = data.get('status', 'N/A')
        print(f"    Response code: {code}")
        print(f"    Response message: {msg}")
        print(f"    Status: {status}")
        print(f"    Answer preview: {answer}")
    else:
        print(f"    Body (非JSON):")
        print(f"    {body}")
        
except Exception as e:
    print(f"    EXCEPTION: {type(e).__name__}: {e}")
    traceback.print_exc()

print("\nDone.")
