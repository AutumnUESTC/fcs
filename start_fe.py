import subprocess, time, os, sys

os.chdir(r"d:\program\fcs-1\fronted_v2")
print(f"CWD: {os.getcwd()}")

proc = subprocess.Popen(
    ["cmd", "/c", "npx", "vite"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
)

print("Waiting for Vite to start...")
for i in range(30):
    line = proc.stdout.readline()
    if line:
        print(line.rstrip())
        if "ready" in line.lower() or "Local:" in line:
            break
    time.sleep(1)
    if proc.poll() is not None:
        print("Process ended early")
        break
else:
    print("Timeout waiting for vite")

# Keep running
import signal
try:
    proc.wait(timeout=300)
except:
    proc.terminate()
