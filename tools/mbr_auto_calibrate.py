#!/usr/bin/env python3
import os
import sys
import json
import requests
from datetime import datetime, timedelta, timezone
from google.cloud import bigquery

# 1. Paths & Project Configuration
PROJECT_ID = "moonlit-botany-293421"
DATASET_ID = "home_assistant_data"
TABLE_ID = "climate_analytics"

# Handle credential paths for both host and container running environment
if os.path.exists("/config/bigquery_credentials.json"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/config/bigquery_credentials.json"
elif os.path.exists("/app/service-account.json"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/app/service-account.json"
else:
    sys.stderr.write("CRITICAL: BigQuery service account credentials not found.\n")
    sys.exit(1)

def get_ha_credentials():
    """Loads Home Assistant credentials from global config or environment."""
    config_path = "/root/.gemini/antigravity-cli/mcp_config.json"
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
            ha_api = config.get("mcpServers", {}).get("ha_api", {})
            server_url = ha_api.get("serverUrl", "")
            if server_url.endswith("/mcp"):
                api_url = server_url[:-4]
            elif server_url.endswith("/"):
                api_url = server_url[:-1]
            else:
                api_url = server_url
            
            auth_header = ha_api.get("headers", {}).get("Authorization", "")
            token = auth_header.replace("Bearer ", "").strip()
            return api_url, token
        except Exception as e:
            sys.stderr.write(f"Warning: Failed to load config from {config_path}: {e}\n")
    
    # Fallbacks for running inside container/environment
    return "http://localhost:8123/api", ""

def fetch_telemetry_events():
    """Queries raw telemetry from BigQuery for the last 30 days."""
    sql = f"""
    SELECT timestamp, entity_id, value, hvac_action
    FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
    WHERE entity_id IN (
      'climate.t6_pro_downstairs',
      'sensor.bedroom_sensor_air_temperature',
      'sensor.weather_station_temperature_outdoor'
    )
    AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
    ORDER BY timestamp ASC
    """
    client = bigquery.Client()
    query_job = client.query(sql)
    return query_job.result()

def reconstruct_sessions(events):
    """Traces state changes to reconstruct exact pre-cooling runs."""
    sessions = []
    
    # Tracking variables for current state
    active_session = None
    bedroom_temp = None
    outdoor_temp = None
    hvac_state = "idle"
    
    for row in events:
        ts = row.timestamp
        eid = row.entity_id
        val = row.value
        hvac_act = row.hvac_action
        
        # 1. Update latest environmental states
        if eid == 'sensor.bedroom_sensor_air_temperature' and val is not None:
            bedroom_temp = float(val)
        elif eid == 'sensor.weather_station_temperature_outdoor' and val is not None:
            outdoor_temp = float(val)
            
        # 2. Watch for HVAC transitions
        elif eid == 'climate.t6_pro_downstairs':
            new_hvac_state = hvac_act if hvac_act else "idle"
            
            # Start of a cooling run
            if new_hvac_state == "cooling" and hvac_state != "cooling":
                # Ensure we have environmental sensor readings
                if bedroom_temp is not None and outdoor_temp is not None:
                    # Let's filter to evening pre-cooling (say, 5:00 PM to 12:00 AM local)
                    # EDT is UTC-4. Let's extract hour in EDT.
                    edt_ts = ts - timedelta(hours=4)
                    if 17 <= edt_ts.hour <= 23:
                        active_session = {
                            "start_time": ts,
                            "start_bedroom_temp": bedroom_temp,
                            "start_outdoor_temp": outdoor_temp,
                            "outdoor_temps": [outdoor_temp]
                        }
            
            # End of a cooling run
            elif new_hvac_state != "cooling" and hvac_state == "cooling":
                if active_session:
                    # Record end state if we have valid readings
                    if bedroom_temp is not None and outdoor_temp is not None:
                        active_session["end_time"] = ts
                        active_session["end_bedroom_temp"] = bedroom_temp
                        active_session["end_outdoor_temp"] = outdoor_temp
                        active_session["outdoor_temps"].append(outdoor_temp)
                        sessions.append(active_session)
                    active_session = None
                    
            hvac_state = new_hvac_state
            
        # Accumulate outdoor temp telemetry during active session
        if active_session and eid == 'sensor.weather_station_temperature_outdoor' and val is not None:
            active_session["outdoor_temps"].append(float(val))
            
    return sessions

def calculate_bin_averages(sessions):
    """Applies Data Armor v2 rules to filter, process, and bin sessions."""
    bins = {}
    valid_rates = []
    valid_temps = []
    
    print("\n--- RECONSTRUCTED PRE-COOLING SESSIONS ---")
    print(f"{'Date (EDT)':<12} | {'Duration':<8} | {'Temp Drop':<10} | {'Avg Outdoor':<12} | {'Rate (m/deg)':<15} | {'Status'}")
    print("-" * 75)
    
    for s in sessions:
        # Calculate session metrics
        duration = (s["end_time"] - s["start_time"]).total_seconds() / 60
        drop = s["start_bedroom_temp"] - s["end_bedroom_temp"]
        avg_outdoor = sum(s["outdoor_temps"]) / len(s["outdoor_temps"])
        edt_start = s["start_time"] - timedelta(hours=4)
        date_str = edt_start.strftime("%Y-%m-%d")
        
        # 1. Validation Filtering
        if duration < 10.0:
            status = "SHORT RUN (<10m)"
        elif drop <= 0.5:
            status = "LOW DROP (<=0.5F)"
        else:
            rate = duration / drop
            # 2. Data Armor v2 Clamping Bounds Check (10.0 - 90.0)
            if rate < 10.0 or rate > 90.0:
                status = f"ANOMALOUS RATE ({rate:.1f})"
            else:
                status = "VALID"
                # Store valid session points
                valid_rates.append(rate)
                valid_temps.append(avg_outdoor)
                
                # Assign to 5-degree temperature bins
                bin_key = int(round(avg_outdoor / 5) * 5)
                if bin_key not in bins:
                    bins[bin_key] = []
                bins[bin_key].append(rate)
                
        if status == "VALID":
            print(f"{date_str:<12} | {duration:5.1f}m   | {drop:5.1f}F     | {avg_outdoor:5.1f}F      | {rate:11.1f}     | {status}")
        else:
            print(f"{date_str:<12} | {duration:5.1f}m   | {drop:5.1f}F     | {avg_outdoor:5.1f}F      | {'-':^11}     | {status}")
            
    return bins, valid_rates, valid_temps

def extrapolate_missing_bins(bins, valid_rates, valid_temps):
    """Uses linear regression to extrapolate missing bins and clamps rates."""
    calibrated_repo = {}
    
    # Core target bins we want to define in Home Assistant
    target_bins = [45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100]
    
    # 1. Standard Averages for bins with data
    for b in target_bins:
        if b in bins:
            calibrated_repo[b] = round(sum(bins[b]) / len(bins[b]), 1)
            
    # 2. Linear Regression for empty bins
    n = len(valid_rates)
    if n >= 3: # Require at least 3 valid sessions to run a robust regression
        sum_x = sum(valid_temps)
        sum_y = sum(valid_rates)
        sum_xx = sum(x*x for x in valid_temps)
        sum_xy = sum(x*y for x, y in zip(valid_temps, valid_rates))
        
        denom = (n * sum_xx) - (sum_x ** 2)
        if denom != 0:
            slope = ((n * sum_xy) - (sum_x * sum_y)) / denom
            intercept = (sum_y - (slope * sum_x)) / n
            
            print(f"\n--- MACHINE LEARNING CALIBRATION ---")
            print(f"Regression Line: rate = {slope:.3f} * outdoor_temp + ({intercept:.1f})")
            
            # Fill missing target bins using regression trend
            for b in target_bins:
                if b not in calibrated_repo:
                    extrapolated_val = (slope * b) + intercept
                    # Apply physical safety clamps (Data Armor bounds)
                    clamped_val = max(10.0, min(90.0, extrapolated_val))
                    calibrated_repo[b] = round(clamped_val, 1)
                    print(f"  Extrapolated Bin {b}F: {calibrated_repo[b]:.1f} min/deg (Clamped)")
        else:
            print("\nWarning: Linear regression denominator was 0. Using fallback values.")
    else:
        print("\nWarning: Insufficient data for regression (< 3 valid sessions). Falling back to hardcoded profiles.")
        
    # 3. Fallback/Default profiles for any remaining undefined bins
    defaults = {45: 22.2, 50: 24.6, 55: 27.0, 60: 30.0, 65: 35.0, 70: 40.0, 75: 45.0, 80: 50.0, 85: 55.0, 90: 65.0, 95: 70.0, 100: 75.0}
    for b in target_bins:
        if b not in calibrated_repo:
            calibrated_repo[b] = defaults[b]
            
    # Sort keys for clean output
    return {str(k): v for k, v in sorted(calibrated_repo.items(), key=lambda x: int(x[0]))}

def update_ha_shadow_repo(calibrated_json_str):
    """Sends the newly calculated repository JSON string to Home Assistant."""
    api_url, token = get_ha_credentials()
    if not token:
        print("\nWarning: Home Assistant Token missing. Printing shadow JSON instead of writing back.")
        print(f"Calibrated Shadow JSON: {calibrated_json_str}")
        return False
        
    url = f"{api_url}/services/input_text/set_value"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "entity_id": "input_text.mbr_cooling_performance_shadow_data",
        "value": calibrated_json_str
    }
    
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        if r.status_code == 200:
            print("\n🎉 Success! Successfully updated Home Assistant Shadow Repository.")
            return True
        else:
            sys.stderr.write(f"\nError writing back to HA: {r.status_code} - {r.text}\n")
            return False
    except Exception as e:
        sys.stderr.write(f"\nError posting to Home Assistant: {e}\n")
        return False

def main():
    print("Initializing MBR Cooling Calibration Shadow Agent...")
    print("Fetching last 30 days of climate events from BigQuery...")
    
    events = fetch_telemetry_events()
    sessions = reconstruct_sessions(events)
    
    if not sessions:
        print("No pre-cooling sessions reconstructed from the last 30 days.")
        return
        
    bins, valid_rates, valid_temps = calculate_bin_averages(sessions)
    calibrated_repo = extrapolate_missing_bins(bins, valid_rates, valid_temps)
    
    json_str = json.dumps(calibrated_repo)
    print("\n--- FINAL CALIBRATED SHADOW DATA PROFILE ---")
    print(json_str)
    
    # Post back to Home Assistant
    update_ha_shadow_repo(json_str)

if __name__ == "__main__":
    main()
