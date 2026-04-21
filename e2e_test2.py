"""多轮对话测试 - 明确触发追问"""
import sys, io, json, time, requests

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = "http://127.0.0.1:8000"

# === 第一轮 ===
print("=== 第一轮请求 ===")
payload = {"user_input": "帮我打官司", "uploaded_files": [], "session_id": "", "user_response": ""}
start = time.time()
r = requests.post(f"{BASE}/api/legal/analyze", json=payload, timeout=300)
elapsed = time.time() - start
data = r.json()
print(f"耗时: {elapsed:.1f}s")
print(f"status: {data.get('status')}")
sid = data.get("session_id", "")
print(f"session_id: {sid}")

if data.get("status") == "need_info":
    print(f"pending_question: {data.get('pending_question', '')[:300]}")
    print(f"missing_info: {data.get('missing_info')}")

    # === 第二轮 ===
    print("\n=== 第二轮请求 ===")
    payload2 = {"user_input": "", "uploaded_files": [], "session_id": sid, "user_response": "我是农民工，在工地干活受了工伤，老板不给赔医药费"}
    start2 = time.time()
    r2 = requests.post(f"{BASE}/api/legal/analyze", json=payload2, timeout=300)
    elapsed2 = time.time() - start2
    data2 = r2.json()
    print(f"耗时: {elapsed2:.1f}s")
    print(f"status: {data2.get('status')}")

    intent2 = data2.get("intent")
    er2 = data2.get("execution_results", [])
    rc2 = data2.get("report_content")
    rp2 = data2.get("review_passed")
    ue2 = data2.get("user_emotion")

    print(f"intent: {'有值' if intent2 else 'NULL'}")
    if intent2:
        print(f"  {json.dumps(intent2, ensure_ascii=False)[:200]}")
    print(f"execution_results: {len(er2)} 个")
    print(f"report_content: {'有值(' + str(len(rc2)) + '字)' if rc2 else 'NULL'}")
    if rc2:
        print(f"  预览: {rc2[:300]}...")
    print(f"review_passed: {rp2}")
    print(f"user_emotion: {'有值' if ue2 else 'NULL'}")

    issues = []
    if not intent2: issues.append("intent=NULL")
    if not er2: issues.append("execution_results=空")
    if not rc2: issues.append("report_content=NULL")
    if rp2 is None: issues.append("review_passed=NULL")
    if not ue2: issues.append("user_emotion=NULL")
    if issues:
        print(f"\n问题: {', '.join(issues)}")
    else:
        print("\n所有关键字段都有值!")

elif data.get("status") == "completed":
    intent = data.get("intent")
    rc = data.get("report_content")
    rp = data.get("review_passed")
    ue = data.get("user_emotion")
    print("直接 completed（未触发追问）")
    print(f"intent: {'有值' if intent else 'NULL'}")
    print(f"report_content: {'有值(' + str(len(rc)) + '字)' if rc else 'NULL'}")
    print(f"review_passed: {rp}")
    print(f"user_emotion: {'有值' if ue else 'NULL'}")
else:
    print(f"status={data.get('status')}, unexpected")
