#!/usr/bin/env python3
"""
Log Diagnostic & Performance Compiler Skill.
Parses climate_control_log.csv and home-assistant.log to summarize thermal runs and track system warnings.
"""

import os
import sys
import argparse
from datetime import datetime, timedelta

CLIMATE_LOG_PATH = "/opt/docker/appdata/hub/hass/www/climate_control_log.csv"
HA_LOG_PATH = "/opt/docker/appdata/hub/hass/home-assistant.log"

def parse_climate_log(days_filter=7):
    """Parses climate_control_log.csv and compiles a structured summary table."""
    if not os.path.exists(CLIMATE_LOG_PATH):
        print(f"Error: Climate log not found at {CLIMATE_LOG_PATH}")
        return
        
    cutoff_date = datetime.now() - timedelta(days=days_filter)
    runs = {}
    
    with open(CLIMATE_LOG_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("Home Assistant") or line.startswith("---"):
                continue
                
            parts = line.split(",", 2)
            if len(parts) < 2:
                continue
                
            timestamp_part = parts[0]
            phase = parts[1]
            extra = parts[2] if len(parts) > 2 else ""
            
            # Format: '2026-04-18T00:35:00.753322+00:00 2026-04-17 20:35:00'
            # Split by space and take the first part as UTC ISO timestamp
            ts_subparts = timestamp_part.split()
            if not ts_subparts:
                continue
            iso_ts = ts_subparts[0]
            
            try:
                # Truncate microseconds and timezone if any
                clean_ts = iso_ts.split("+")[0].split(".")[0]
                dt = datetime.fromisoformat(clean_ts)
            except ValueError:
                continue
                
            if dt < cutoff_date:
                continue
                
            # Grouping logs by date (local run date from second part of timestamp if possible)
            run_date = ts_subparts[1] if len(ts_subparts) > 1 else dt.strftime("%Y-%m-%d")
            
            if run_date not in runs:
                runs[run_date] = {
                    "start_dt": None,
                    "handoff_dt": None,
                    "start_indoor": "-",
                    "start_outdoor": "-",
                    "expected_rate": "-",
                    "duration": "-",
                    "drop": "-",
                    "actual_rate": "-",
                    "bin": "-",
                    "handoff_indoor": "-",
                    "status": "Incomplete",
                    "ai_reason": "-",
                    "audit": "-",
                    "keep_cool_count": 0,
                    "prevent_overcool_count": 0
                }
            
            # Parse key-value attributes
            attrs = {}
            for pair in extra.split(","):
                pair = pair.strip()
                if ":" in pair:
                    k, v = pair.split(":", 1)
                    attrs[k.strip().lower()] = v.strip()
                    
            if phase == "PHASE_2_START":
                runs[run_date]["start_indoor"] = attrs.get("indoor", "-")
                runs[run_date]["start_outdoor"] = attrs.get("outdoor", "-")
                runs[run_date]["ai_reason"] = attrs.get("ai_reason", "-")
                runs[run_date]["start_dt"] = dt
                runs[run_date]["status"] = "Started"
            elif phase == "PHASE_3_HANDOFF":
                runs[run_date]["handoff_indoor"] = attrs.get("indoor", "-")
                runs[run_date]["handoff_dt"] = dt
                if runs[run_date]["status"] == "Started":
                     runs[run_date]["status"] = "Handoff Only"
                
                # Compute duration and drop dynamically
                if runs[run_date]["start_dt"]:
                    duration_mins = int((dt - runs[run_date]["start_dt"]).total_seconds() / 60)
                    runs[run_date]["duration"] = str(duration_mins)
                if runs[run_date]["start_indoor"] != "-":
                    try:
                        start_temp = float(runs[run_date]["start_indoor"])
                        handoff_temp = float(attrs.get("indoor", 0))
                        runs[run_date]["drop"] = f"{start_temp - handoff_temp:.1f}"
                    except ValueError:
                        pass
            elif phase == "PHASE_3_LEARNED":
                runs[run_date]["actual_rate"] = attrs.get("obsrate", "-")
                runs[run_date]["expected_rate"] = attrs.get("newrate", "-")
                runs[run_date]["bin"] = attrs.get("bin", "-")
                runs[run_date]["audit"] = attrs.get("audit", "-")
                runs[run_date]["status"] = "Completed & Learned"
            elif phase == "PHASE_3_ANOMALY":
                runs[run_date]["actual_rate"] = attrs.get("obsrate", "-")
                runs[run_date]["audit"] = attrs.get("audit", "-")
                runs[run_date]["status"] = "Anomaly Blocked"
            elif phase == "PHASE_4_KEEP_COOL":
                runs[run_date]["keep_cool_count"] += 1
            elif phase == "PHASE_5_PREVENT_OVERCOOL":
                runs[run_date]["prevent_overcool_count"] += 1

    # Display the result in Markdown
    print(f"# Climate Control Performance Summary (Last {days_filter} Days)")
    print()
    print("| Date | Start Temp (In/Out) | Duration | Drop | Obs Rate | New Rate | Bin | Handoff Temp | Status |")
    print("|------|---------------------|----------|------|----------|----------|-----|--------------|--------|")
    
    for date in sorted(runs.keys(), reverse=True):
        r = runs[date]
        start_temp = f"{r['start_indoor']}°F / {r['start_outdoor']}°F" if r['start_indoor'] != "-" else "-"
        obs_rate_str = f"{r['actual_rate']} m/d" if r['actual_rate'] != "-" else "-"
        new_rate_str = f"{r['expected_rate']} m/d" if r['expected_rate'] != "-" else "-"
        duration_str = f"{r['duration']} min" if r['duration'] != "-" else "-"
        drop_str = f"{r['drop']}°F" if r['drop'] != "-" else "-"
        handoff_temp_str = f"{r['handoff_indoor']}°F" if r['handoff_indoor'] != "-" else "-"
        print(f"| {date} | {start_temp} | {duration_str} | {drop_str} | {obs_rate_str} | {new_rate_str} | {r['bin']} | {handoff_temp_str} | {r['status']} |")

    print()
    print("## Detailed Run Telemetry & AI Commentary")
    print()
    for date in sorted(runs.keys(), reverse=True):
        r = runs[date]
        print(f"### Run Date: {date}")
        print(f"- **Status:** {r['status']}")
        if r['start_indoor'] != "-":
            print(f"- **Initial Conditions:** Room at {r['start_indoor']}°F, Outdoors at {r['start_outdoor']}°F")
        if r['ai_reason'] and r['ai_reason'] != "-":
            print(f"- **AI Pre-Cooling Reason:** *\"{r['ai_reason']}\"*")
        if r['handoff_indoor'] != "-":
            print(f"- **Handoff Conditions:** Room at {r['handoff_indoor']}°F after {r['duration']} minutes (cooling drop of {r['drop']}°F)")
        if r['keep_cool_count'] > 0 or r['prevent_overcool_count'] > 0:
            print(f"- **Sleep Maintenance Profile:** {r['keep_cool_count']} Keep-Cool cycles, {r['prevent_overcool_count']} Over-Cool Guard cycles")
        if r['actual_rate'] != "-":
            print(f"- **Observed Rate:** {r['actual_rate']} min/deg")
        if r['expected_rate'] != "-":
            print(f"- **New Learned Rate:** {r['expected_rate']} min/deg (Stored in Bin {r['bin']})")
        if r['audit'] and r['audit'] != "-":
            print(f"- **AI Auditor Verdict:** *\"{r['audit']}\"*")
        print()

def scan_ha_warnings():
    """Scans home-assistant.log for core warnings, database locked messages, and component failures."""
    if not os.path.exists(HA_LOG_PATH):
        print(f"Error: Home Assistant log not found at {HA_LOG_PATH}")
        return
        
    print("# Home Assistant System Diagnostic Audit")
    print()
    
    categories = {
        "Database Status / Locks": ["database is locked", "sqlite", "recorder", "write delay"],
        "Core Climate & Template Errors": ["climate", "mbr_sleep_comfort", "template error", "jinja"],
        "Connection & Stream Failures": ["stream", "camera", "hstream", "dts", "rstp", "disconnected"],
        "Critical Component Failures": ["setup failed", "could not set up", "error during setup", "traceback"]
    }
    
    findings = {cat: [] for cat in categories}
    total_warnings = 0
    total_errors = 0
    
    with open(HA_LOG_PATH, "r", errors="ignore") as f:
        for line in f:
            line_lower = line.lower()
            if "warning" in line_lower:
                total_warnings += 1
            elif "error" in line_lower:
                total_errors += 1
                
            for cat, keywords in categories.items():
                for kw in keywords:
                    if kw in line_lower:
                        if len(findings[cat]) < 15:  # Limit findings per category to keep it readable
                            findings[cat].append(line.strip())
                        break
                        
    print(f"**Total Log Metrics:** {total_errors} Errors | {total_warnings} Warnings")
    print()
    
    for cat, logs in findings.items():
        print(f"### {cat}")
        if not logs:
            print("*No critical items found in log.*")
        else:
            for l in logs:
                # Escape markdown characters
                safe_log = l.replace("|", "\\|").replace("*", "\\*")
                print(f"- `{safe_log}`")
        print()

def main():
    parser = argparse.ArgumentParser(description="Home Assistant Log Diagnostic Skill")
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")
    
    # Summary parser
    summary_parser = subparsers.add_parser("summary", help="Summarize cooling runs")
    summary_parser.add_argument("--days", type=int, default=7, help="Number of days to summarize")
    
    # Warnings parser
    subparsers.add_parser("warnings", help="Scan home-assistant.log for warnings and errors")
    
    args = parser.parse_args()
    
    if args.command == "summary":
        parse_climate_log(args.days)
    elif args.command == "warnings":
        scan_ha_warnings()
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
