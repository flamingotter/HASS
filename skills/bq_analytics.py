#!/usr/bin/env python3
"""
Telemetry Analytics Skill Wrapper.
Transparently forwards legacy BigQuery CLI calls to ClickHouse Analytics Skill (ch_analytics.py).
"""

import sys
import subprocess
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CH_SCRIPT = os.path.join(SCRIPT_DIR, "ch_analytics.py")

def main():
    args = sys.argv[1:]
    cmd = [sys.executable, CH_SCRIPT] + args
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        if res.returncode == 0:
            print(res.stdout, end="")
        else:
            sys.stderr.write(res.stderr)
            sys.exit(res.returncode)
    except Exception as e:
        sys.stderr.write(f"Error executing analytics skill: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
