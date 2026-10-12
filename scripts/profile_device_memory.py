"""
Device Memory Profiler for LISAN
================================
Monitors memory usage (PSS, Native, Dalvik, Dirty) of com.example.ethiopian_translator
directly from connected Android device via adb.
"""

import subprocess
import time
import re
import sys
import os

ADB_PATH = r"C:\Users\admin\AppData\Local\Android\Sdk\platform-tools\adb.exe"
PACKAGE = "com.example.ethiopian_translator"
ALERT_THRESHOLD_MB = 350.0
CRITICAL_THRESHOLD_MB = 500.0

def run_adb(cmd: str) -> str:
    full_cmd = f'"{ADB_PATH}" {cmd}'
    res = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, errors="replace")
    return res.stdout

def get_memory_snapshot() -> dict | None:
    output = run_adb(f"shell dumpsys meminfo {PACKAGE}")
    if "No process found" in output or not output.strip():
        return None

    # Parse Total Pss, Native Heap, Dalvik Heap, Total Dirty
    snapshot = {
        "timestamp": time.time(),
        "total_pss_kb": 0,
        "native_heap_kb": 0,
        "dalvik_heap_kb": 0,
        "private_dirty_kb": 0,
        "pid": None
    }

    pid_match = re.search(r"MEMINFO in pid\s+(\d+)", output)
    if pid_match:
        snapshot["pid"] = int(pid_match.group(1))

    # App Summary TOTAL
    total_match = re.search(r"TOTAL:\s+(\d+)", output)
    if total_match:
        snapshot["total_pss_kb"] = int(total_match.group(1))

    # Native Heap
    native_match = re.search(r"Native Heap:\s+(\d+)", output)
    if native_match:
        snapshot["native_heap_kb"] = int(native_match.group(1))

    # Java / Dalvik Heap
    java_match = re.search(r"Java Heap:\s+(\d+)", output)
    if java_match:
        snapshot["dalvik_heap_kb"] = int(java_match.group(1))

    # Private Dirty
    dirty_match = re.search(r"TOTAL\s+\d+\s+(\d+)", output)
    if dirty_match:
        snapshot["private_dirty_kb"] = int(dirty_match.group(1))

    return snapshot

def print_status(snapshot: dict):
    pss_mb = snapshot["total_pss_kb"] / 1024.0
    native_mb = snapshot["native_heap_kb"] / 1024.0
    java_mb = snapshot["dalvik_heap_kb"] / 1024.0
    dirty_mb = snapshot["private_dirty_kb"] / 1024.0

    status = "SAFE [OK]"
    if pss_mb > CRITICAL_THRESHOLD_MB:
        status = "CRITICAL [DANGER LMK]"
    elif pss_mb > ALERT_THRESHOLD_MB:
        status = "WARNING [>350MB]"

    print(
        f"PID: {snapshot['pid']:<6} | "
        f"Total PSS: {pss_mb:6.1f} MB | "
        f"Native: {native_mb:5.1f} MB | "
        f"Java: {java_mb:5.1f} MB | "
        f"Dirty: {dirty_mb:5.1f} MB | "
        f"[{status}]"
    )

def main():
    print(f"Monitoring memory for {PACKAGE} (Budget: <= {ALERT_THRESHOLD_MB} MB)...")
    try:
        while True:
            snap = get_memory_snapshot()
            if snap:
                print_status(snap)
            else:
                print(f"Waiting for {PACKAGE} to start...")
            time.sleep(2.0)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        snap = get_memory_snapshot()
        if snap:
            print_status(snap)
            sys.exit(0)
        else:
            print("App not running.")
            sys.exit(1)
    main()
