#!/usr/bin/env python3
"""
BigQuery Analytics Engine Skill (Host Wrapper).
Delegates execution cleanly to the running ha_bq_exporter container where all dependencies exist.
"""

import sys
import subprocess

def main():
    # Pass all arguments transparently to the container-side script
    args = sys.argv[1:]
    
    # Run the command inside the ha_bq_exporter container
    cmd = ["docker", "exec", "ha_bq_exporter", "python3", "/app/bq_analytics.py"] + args
    
    try:
        # Run process and pipe output
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        
        if res.returncode == 0:
            print(res.stdout, end="")
        else:
            sys.stderr.write(res.stderr)
            sys.exit(res.returncode)
            
    except Exception as e:
        sys.stderr.write(f"Error executing skill wrapper: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
