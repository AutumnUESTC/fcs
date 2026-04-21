#!/usr/bin/env python3
"""第二轮续传测试"""
import sys, io, json, time, requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

session_id = "b442550d-8d83-4460-9758-9b9e9d67d731"
payload = {
    "user_input": "",
    "uploaded_files": [],
    "session_id": session_id,
    "user_response": "我被人骗了5万块钱，是网络诈骗，我想追回损失并起诉对方"
}

print(f"=== 第二轮续传 (session: {session_id[:8]}...) ===")
print(f"用户回复: {payload['user_response']}")

start = time.time()
try:
    r = requests.post('http://127.0.0.1:8000/api/legal/analyze', json=payload, timeout=600)
    elapsed = time.time() - start
    data = r.json()
    print(f"\n耗时: {elapsed:.1f}s")
    print(f"success: {data.get('success')}")
    print(f"status: {data.get('status')}")
    print(f"session_id: {data.get('session_id')}")

    # 关键字段
    intent = data.get('intent')
    report = data.get('report_content')
    review = data.get('review_passed')
    emotion = data.get('user_emotion')
    exec_results = data.get('execution_results')
    review_issues = data.get('review_issues')

    print(f"\n--- 关键字段 ---")
    print(f"intent: {json.dumps(intent, ensure_ascii=False) if intent else 'NULL'}")
    print(f"report_content: {(report or 'NULL')[:300]}...")
    print(f"review_passed: {review}")
    print(f"review_issues: {review_issues}")
    print(f"user_emotion: {json.dumps(emotion, ensure_ascii=False) if emotion else 'NULL'}")
    print(f"execution_results: {json.dumps(exec_results, ensure_ascii=False)[:200] if exec_results else 'NULL'}")

    # steps
    steps = data.get('steps', [])
    print(f"\n--- 步骤 ({len(steps)}) ---")
    for s in steps:
        print(f"  {s.get('node')}: {json.dumps(s.get('snapshot', {}), ensure_ascii=False)[:150]}")

    # 检查所有关键字段是否非空
    null_fields = []
    if not intent: null_fields.append('intent')
    if not report: null_fields.append('report_content')
    if review is None: null_fields.append('review_passed')
    if not emotion: null_fields.append('user_emotion')

    if null_fields:
        print(f"\n⚠️  仍有空字段: {null_fields}")
    else:
        print(f"\n✅ 所有关键字段都有值！")

except requests.exceptions.Timeout:
    print(f"超时！(>{600}s)")
except Exception as e:
    print(f"失败: {e}")
