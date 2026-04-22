import sys, io, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
try:
    logs = sorted(glob.glob('d:/program/fcs/logs/fcs_*.log'))
    if logs:
        with open(logs[-1], 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        # 看最后40行
        for line in lines[-40:]:
            print(line.rstrip())
    else:
        print("No log files found")
except Exception as e:
    print(f"Error: {e}")
