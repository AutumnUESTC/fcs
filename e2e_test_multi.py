#!/usr/bin/env python3
"""多场景 E2E 测试"""
import sys, io, json, time, requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = "http://127.0.0.1:8000/api/legal/analyze"
TIMEOUT = 600

def test_case(name, payload):
    print(f"\n{'='*60}")
    print(f"测试: {name}")
    print(f"输入: user_input={payload.get('user_input','')[:50]}, session_id={payload.get('session_id','')[:8]}")
    start = time.time()
    try:
        r = requests.post(BASE, json=payload, timeout=TIMEOUT)
        elapsed = time.time() - start
        data = r.json()
        print(f"耗时: {elapsed:.1f}s | status: {data.get('status')} | success: {data.get('success')}")
        
        if data.get('status') == 'completed':
            intent = data.get('intent')
            report = data.get('report_content', '')
            review = data.get('review_passed')
            emotion = data.get('user_emotion')
            exec_results = data.get('execution_results', [])
            
            null_fields = []
            if not intent: null_fields.append('intent')
            if not report: null_fields.append('report_content')
            if review is None: null_fields.append('review_passed')
            if not emotion: null_fields.append('user_emotion')
            
            print(f"  intent: {json.dumps(intent, ensure_ascii=False)[:100] if intent else 'NULL'}")
            print(f"  report: {(report or '')[:120]}...")
            print(f"  review_passed: {review}")
            print(f"  emotion: {json.dumps(emotion, ensure_ascii=False) if emotion else 'NULL'}")
            print(f"  exec_results: {len(exec_results)} 条")
            print(f"  steps: {len(data.get('steps', []))} 个节点")
            if null_fields:
                print(f"  ⚠️ 空字段: {null_fields}")
            else:
                print(f"  ✅ 所有关键字段有值")
            return data
            
        elif data.get('status') == 'need_info':
            print(f"  pending_question: {data.get('pending_question', '')[:100]}")
            print(f"  missing_info: {data.get('missing_info')}")
            return data
            
        else:
            print(f"  ❌ 意外状态: {data.get('status')}")
            print(f"  详情: {json.dumps(data, ensure_ascii=False)[:300]}")
            return data
            
    except requests.exceptions.Timeout:
        print(f"  ❌ 超时 (>{TIMEOUT}s)")
    except Exception as e:
        print(f"  ❌ 失败: {e}")
    return None

# ========== 场景1: 劳动纠纷 ==========
result1 = test_case("劳动纠纷", {
    "user_input": "公司拖欠我三个月工资，我想申请劳动仲裁",
    "uploaded_files": [],
    "session_id": "",
    "user_response": ""
})

time.sleep(2)

# ========== 场景2: 合同问题 ==========
result2 = test_case("合同审查", {
    "user_input": "房东违约不退押金，租房合同到期了",
    "uploaded_files": [],
    "session_id": "",
    "user_response": ""
})

time.sleep(2)

# ========== 场景3: 多轮对话续传（如果能触发 need_info）==========
# 先发一个容易触发追问的请求
result3 = test_case("多轮-第一轮", {
    "user_input": "我要打官司",
    "uploaded_files": [],
    "session_id": "",
    "user_response": ""
})

# 如果触发了 need_info，发第二轮
if result3 and result3.get('status') == 'need_info':
    session_id = result3.get('session_id', '')
    time.sleep(2)
    test_case("多轮-第二轮(续传)", {
        "user_input": "",
        "uploaded_files": [],
        "session_id": session_id,
        "user_response": "是因为交通事故对方全责但不赔偿，我受了轻伤，医疗费花了2万"
    })
else:
    print(f"\n--- 多轮对话：LLM 未触发 need_info，跳过续传测试 ---")

print(f"\n{'='*60}")
print("测试完成")
