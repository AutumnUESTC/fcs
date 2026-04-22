#!/usr/bin/env python3
"""curl API test - saves request/response JSON to log folder"""
import sys, io, json, time, requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = "http://127.0.0.1:8000/api/legal/analyze"
LOG_DIR = "d:/program/fcs/logs/curl"
TIMESTAMP = time.strftime("%Y%m%d_%H%M%S")
test_index = [1]

import os
os.makedirs(LOG_DIR, exist_ok=True)

def invoke_analyze(name, input_text, session_id="", user_response="", uploaded_files=None):
    if uploaded_files is None:
        uploaded_files = []

    payload = {
        "user_input": input_text,
        "uploaded_files": uploaded_files,
        "session_id": session_id,
        "user_response": user_response,
    }

    idx = test_index[0]
    input_file = f"{LOG_DIR}/test{idx}_{TIMESTAMP}_input.json"
    output_file = f"{LOG_DIR}/test{idx}_{TIMESTAMP}_output.json"

    with open(input_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"\n========== Test {idx}: {name} ==========")
    print(f"Input file : {input_file}")
    print(f"Calling API...")

    try:
        r = requests.post(BASE, json=payload, timeout=600)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(r.text)

        data = r.json()
        print(f"Status code: {r.status_code}")
        print(f"Output file: {output_file}")
        print(f"Response status: {data.get('status')}")
        if data.get('session_id'):
            print(f"session_id: {data.get('session_id')}")
        if data.get('pending_question'):
            print(f"Question: {data.get('pending_question')[:80]}")
        if data.get('user_emotion'):
            print(f"Emotion: {data.get('user_emotion')}")

        test_index[0] += 1
        return data
    except Exception as e:
        error_file = f"{LOG_DIR}/test{idx}_{TIMESTAMP}_error.txt"
        with open(error_file, "w", encoding="utf-8") as f:
            f.write(str(e))
        print(f"Request failed: {e}")
        test_index[0] += 1
        return None

# Test 1: Labor dispute
data1 = invoke_analyze("Labor Dispute", "公司拖欠我三个月工资，我想申请劳动仲裁")
time.sleep(2)

# Test 2: Contract review
data2 = invoke_analyze("Contract Review", "房东违约不退押金，租房合同到期了")
time.sleep(2)

# Test 3: Multi-turn round 1
data3 = invoke_analyze("Multi-turn Round 1", "我要打官司")
if data3 and data3.get("status") == "need_info":
    sid = data3.get("session_id", "")
    time.sleep(2)
    invoke_analyze("Multi-turn Round 2", "", session_id=sid,
                   user_response="是因为交通事故对方全责但不赔偿，我受了轻伤，医疗费花了2万")
time.sleep(2)

# Test 4: Trade secret
invoke_analyze("Trade Secret", "我的商业秘密被泄露了，能申请禁令吗？")

print("\n" + "="*50)
print(f"All tests completed. Logs saved to: {LOG_DIR}")
files = sorted(os.listdir(LOG_DIR))
for f in files:
    fpath = os.path.join(LOG_DIR, f)
    size = os.path.getsize(fpath)
    print(f"  {f}  ({size} bytes)")
