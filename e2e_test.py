"""端到端测试 - 单轮+多轮"""
import sys, io, json, time, requests

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = "http://127.0.0.1:8000"
TIMEOUT = 600  # 10分钟

def check_fields(data, label=""):
    """检查响应关键字段"""
    issues = []
    if not data.get("intent"): issues.append("intent=NULL")
    if not data.get("execution_results"): issues.append("execution_results=空")
    if not data.get("report_content"): issues.append("report_content=NULL")
    if data.get("review_passed") is None: issues.append("review_passed=NULL")
    if not data.get("user_emotion"): issues.append("user_emotion=NULL")
    if issues:
        print(f"  [{label}] 问题: {', '.join(issues)}")
        return False
    else:
        print(f"  [{label}] 所有字段有值!")
        return True

# === 测试1: 单轮直接完成 ===
print("=== 测试1: 单轮对话 ===")
p1 = {"user_input": "商业秘密被泄露，能申请禁令吗", "uploaded_files": [], "session_id": "", "user_response": ""}
t1 = time.time()
r1 = requests.post(f"{BASE}/api/legal/analyze", json=p1, timeout=TIMEOUT)
e1 = time.time() - t1
d1 = r1.json()
print(f"  耗时: {e1:.1f}s, status: {d1.get('status')}")
ok1 = check_fields(d1, "单轮")

# === 测试2: 多轮对话 ===
print("\n=== 测试2: 多轮对话 ===")
p2a = {"user_input": "我需要法律援助", "uploaded_files": [], "session_id": "", "user_response": ""}
t2a = time.time()
r2a = requests.post(f"{BASE}/api/legal/analyze", json=p2a, timeout=TIMEOUT)
e2a = time.time() - t2a
d2a = r2a.json()
sid = d2a.get("session_id", "")
print(f"  第一轮 耗时: {e2a:.1f}s, status: {d2a.get('status')}")

if d2a.get("status") == "need_info":
    print(f"  追问: {d2a.get('pending_question', '')[:150]}...")
    # 第二轮
    p2b = {"user_input": "", "uploaded_files": [], "session_id": sid, "user_response": "我是农民工，在工地干活受了工伤，老板不给赔医药费"}
    t2b = time.time()
    r2b = requests.post(f"{BASE}/api/legal/analyze", json=p2b, timeout=TIMEOUT)
    e2b = time.time() - t2b
    d2b = r2b.json()
    print(f"  第二轮 耗时: {e2b:.1f}s, status: {d2b.get('status')}")
    ok2 = check_fields(d2b, "多轮第二轮")
elif d2a.get("status") == "completed":
    print("  直接completed（未触发追问）")
    ok2 = check_fields(d2a, "多轮(直接完成)")
else:
    print(f"  非预期status: {d2a.get('status')}")
    ok2 = False

print(f"\n=== 测试结果 ===")
print(f"  单轮: {'PASS' if ok1 else 'FAIL'}")
print(f"  多轮: {'PASS' if ok2 else 'FAIL'}")
