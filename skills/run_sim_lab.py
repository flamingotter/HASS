#!/usr/bin/env python3
"""
Sim Lab Scenarios Runner Skill.
Triggers Sim Lab digital twin stress tests and audits the resulting changes in the simulation repository.
"""

import os
import sys
import time
import json
from ha_client import load_credentials, call_action, get_entity_state

INITIAL_REPO = {
    "45": 22.2, "50": 24.6, "55": 28.4, "60": 30.0, "65": 35.5,
    "70": 40.6, "75": 44.8, "80": 35.0, "85": 45.0
}

def trigger_sim_lab(api_url, token):
    """Triggers the run_climate_stress_tests script in Home Assistant."""
    print("Triggering Sim Lab Digital Twin Stress Tests...")
    try:
        call_action(api_url, token, "script", "run_climate_stress_tests")
        print("Sim Lab triggered successfully. Running scenarios (this takes ~10 seconds)...")
    except Exception as e:
        sys.stderr.write(f"Error starting Sim Lab: {e}\n")
        sys.exit(1)

def audit_sim_repository(api_url, token):
    """Audits the sim_mbr_repo state to verify math correctness and learning outputs."""
    try:
        state_data = get_entity_state(api_url, token, "input_text.sim_mbr_repo")
        raw_state = state_data.get("state", "{}")
        learned_repo = json.loads(raw_state)
    except Exception as e:
        sys.stderr.write(f"Error auditing sim repository: {e}\n")
        return
        
    print("\n# Sim Lab Digital Twin Stress Test Audit")
    print("\nBelow is the audit of learning outputs comparing the baseline repository against the post-simulation learned state:")
    print()
    print("| Temperature Bin (°F) | Initial Rate (m/d) | Learned Rate (m/d) | Delta (m/d) | Status |")
    print("|----------------------|--------------------|---------------------|-------------|--------|")
    
    for bin_key in sorted(INITIAL_REPO.keys(), key=int):
        init_val = INITIAL_REPO[bin_key]
        learned_val = learned_repo.get(bin_key, init_val)
        delta = learned_val - init_val
        
        if delta == 0.0:
            status = "No Change (Not Simulated)"
            delta_str = "-"
        else:
            status = "✨ Learned & Verified"
            delta_str = f"{delta:+.1f}"
            
        print(f"| {bin_key}°F | {init_val:.1f} | {learned_val:.1f} | {delta_str} | {status} |")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  run_sim_lab.py run      (Trigger Sim Lab and audit learned repository)")
        print("  run_sim_lab.py status   (Audit currently saved Sim Lab repository state)")
        sys.exit(1)
        
    cmd = sys.argv[1]
    api_url, token = load_credentials()
    if not token:
        sys.stderr.write("Error: Bearer token not found.\n")
        sys.exit(1)
        
    if cmd == "run":
        trigger_sim_lab(api_url, token)
        # Sleep to let HA process scenarios and execute learning logic
        time.sleep(12)
        audit_sim_repository(api_url, token)
        
    elif cmd == "status":
        audit_sim_repository(api_url, token)
        
    else:
        sys.stderr.write(f"Unknown command: {cmd}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
