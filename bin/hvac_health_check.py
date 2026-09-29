#!/usr/bin/env python3
"""
Multi-Zone HVAC Health & Degradation Engine (ClickHouse Native HTTP).
Evaluates thermodynamic cooling efficiency (kWh/°F drop) across 3 independent zones:
  1. Downstairs (Floor 1 Central Trane: Panel 02 HP vs climate.t6_pro_downstairs)
  2. Upstairs (Floor 2 Central Trane: Panel 01 HP vs climate.t6_pro_upstairs)
  3. Office Mini-Split (Floor 2 Dedicated: Panel 01 Mini-Split vs sensor.office_sensor_air_temperature)
Zero external dependencies • Uses Python standard library (urllib.request) to query local ClickHouse HTTP API.
"""

import os
import json
import urllib.request
import urllib.parse
from datetime import datetime

CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "127.0.0.1")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", "8124"))
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "default")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "")
CLICKHOUSE_DB = os.getenv("CLICKHOUSE_DB", "home_assistant_data")

QUERY = """
WITH raw_combined AS (
  -- Downstairs Telemetry (Floor 1: Master Bedroom & Great Room)
  SELECT 'downstairs' as zone, timestamp, value as hp_power, CAST(NULL AS Nullable(Float64)) as indoor_temp, CAST(NULL AS Nullable(Float64)) as outdoor_temp, 300.0 as min_run_power
  FROM home_assistant_data.whole_home_telemetry
  WHERE entity_id = 'sensor.panel_02_downstairs_heat_pump_power'
    AND timestamp >= '2026-08-24 13:35:00'
  UNION ALL
  SELECT 'downstairs' as zone, timestamp, NULL as hp_power, value as indoor_temp, NULL as outdoor_temp, 300.0 as min_run_power
  FROM home_assistant_data.whole_home_telemetry
  WHERE entity_id = 'climate.t6_pro_downstairs'
    AND timestamp >= '2026-08-24 13:35:00'
  UNION ALL
  -- Upstairs Telemetry (Floor 2: Hallway, Bonus Room, Upstairs Bedroom)
  SELECT 'upstairs' as zone, timestamp, value as hp_power, CAST(NULL AS Nullable(Float64)) as indoor_temp, CAST(NULL AS Nullable(Float64)) as outdoor_temp, 300.0 as min_run_power
  FROM home_assistant_data.whole_home_telemetry
  WHERE entity_id = 'sensor.panel_01_upstairs_heat_pump_power'
    AND timestamp >= '2026-08-24 13:35:00'
  UNION ALL
  SELECT 'upstairs' as zone, timestamp, NULL as hp_power, value as indoor_temp, NULL as outdoor_temp, 300.0 as min_run_power
  FROM home_assistant_data.whole_home_telemetry
  WHERE entity_id = 'climate.t6_pro_upstairs'
    AND timestamp >= '2026-08-24 13:35:00'
  UNION ALL
  -- Office Mini-Split Telemetry (Floor 2: Office / Library)
  SELECT 'office_minisplit' as zone, timestamp, value as hp_power, CAST(NULL AS Nullable(Float64)) as indoor_temp, CAST(NULL AS Nullable(Float64)) as outdoor_temp, 100.0 as min_run_power
  FROM home_assistant_data.whole_home_telemetry
  WHERE entity_id = 'sensor.panel_01_mini_split_power'
    AND timestamp >= '2026-08-24 13:35:00'
  UNION ALL
  SELECT 'office_minisplit' as zone, timestamp, NULL as hp_power, value as indoor_temp, NULL as outdoor_temp, 100.0 as min_run_power
  FROM home_assistant_data.whole_home_telemetry
  WHERE entity_id = 'sensor.office_sensor_air_temperature'
    AND timestamp >= '2026-08-24 13:35:00'
  UNION ALL
  -- Outdoor Weather Station Temperature
  SELECT 'downstairs' as zone, timestamp, NULL as hp_power, NULL as indoor_temp, value as outdoor_temp, 300.0 as min_run_power
  FROM home_assistant_data.whole_home_telemetry
  WHERE entity_id = 'sensor.weather_station_temperature_outdoor'
    AND timestamp >= '2026-08-24 13:35:00'
  UNION ALL
  SELECT 'upstairs' as zone, timestamp, NULL as hp_power, NULL as indoor_temp, value as outdoor_temp, 300.0 as min_run_power
  FROM home_assistant_data.whole_home_telemetry
  WHERE entity_id = 'sensor.weather_station_temperature_outdoor'
    AND timestamp >= '2026-08-24 13:35:00'
  UNION ALL
  SELECT 'office_minisplit' as zone, timestamp, NULL as hp_power, NULL as indoor_temp, value as outdoor_temp, 100.0 as min_run_power
  FROM home_assistant_data.whole_home_telemetry
  WHERE entity_id = 'sensor.weather_station_temperature_outdoor'
    AND timestamp >= '2026-08-24 13:35:00'
),
filled AS (
  SELECT 
    zone,
    timestamp,
    hp_power,
    min_run_power,
    last_value(indoor_temp) OVER (PARTITION BY zone ORDER BY timestamp ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as indoor_temp,
    last_value(outdoor_temp) OVER (PARTITION BY zone ORDER BY timestamp ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as outdoor_temp
  FROM raw_combined
),
runs AS (
  SELECT 
    *,
    CASE 
      WHEN hp_power > min_run_power AND (lagInFrame(hp_power, 1, 0.0) OVER (PARTITION BY zone ORDER BY timestamp) <= min_run_power) THEN 1 
      ELSE 0 
    END as is_start
  FROM filled
  WHERE hp_power IS NOT NULL
),
sessions AS (
  SELECT *, sum(is_start) OVER (PARTITION BY zone ORDER BY timestamp ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as session_id
  FROM runs
),
cycle_stats AS (
  SELECT 
    zone,
    session_id,
    min(timestamp) as start_time,
    max(timestamp) as end_time,
    dateDiff('minute', min(timestamp), max(timestamp)) as duration_min,
    avg(hp_power) as avg_hp_watts,
    argMin(indoor_temp, timestamp) as start_temp,
    argMax(indoor_temp, timestamp) as end_temp,
    avg(outdoor_temp) as avg_outdoor_temp
  FROM sessions
  WHERE hp_power > min_run_power
  GROUP BY zone, session_id, min_run_power
  HAVING duration_min >= 8
     AND (argMin(indoor_temp, timestamp) - argMax(indoor_temp, timestamp)) >= 0.3
)
SELECT 
  zone,
  CASE WHEN start_time > now() - INTERVAL 3 DAY THEN 'recent' ELSE 'baseline' END as period,
  count(*) as valid_cycles,
  avg(duration_min) as avg_duration,
  avg(avg_hp_watts) as avg_watts,
  avg(start_temp - end_temp) as avg_temp_drop,
  avg(avg_outdoor_temp) as avg_outdoor,
  avg((avg_hp_watts * (duration_min / 60.0) / 1000.0) / (start_temp - end_temp)) as kwh_per_deg_drop
FROM cycle_stats
GROUP BY zone, period
FORMAT JSONCompact
"""

def query_clickhouse():
    url = f"http://{CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}/?database={CLICKHOUSE_DB}"
    if CLICKHOUSE_USER:
        url += f"&user={urllib.parse.quote(CLICKHOUSE_USER)}"
    if CLICKHOUSE_PASSWORD:
        url += f"&password={urllib.parse.quote(CLICKHOUSE_PASSWORD)}"
    
    req = urllib.request.Request(url, data=QUERY.encode("utf-8"), method="POST")
    req.add_header("Content-Type", "text/plain; charset=utf-8")
    
    with urllib.request.urlopen(req, timeout=10) as response:
        payload = response.read().decode("utf-8")
        parsed = json.loads(payload)
        return parsed.get("data", [])

def run_health_check():
    try:
        results = query_clickhouse()
        zone_data = {}
        for row in results:
            z, p, valid_cycles, avg_dur, avg_w, avg_drop, avg_out, kwh_deg = row
            if z not in zone_data:
                zone_data[z] = {}
            zone_data[z][p] = {
                "valid_cycles": int(valid_cycles),
                "avg_duration_min": round(float(avg_dur), 1) if avg_dur else None,
                "avg_compressor_watts": round(float(avg_w), 1) if avg_w else None,
                "avg_temp_drop": round(float(avg_drop), 2) if avg_drop else None,
                "avg_outdoor": round(float(avg_out), 1) if avg_out else None,
                "kwh_per_deg_drop": round(float(kwh_deg), 3) if kwh_deg else None
            }

        MIN_SAMPLE_CYCLES = 2

        def evaluate_zone(zone_name):
            base = zone_data.get(zone_name, {}).get("baseline", {}).get("kwh_per_deg_drop")
            rec = zone_data.get(zone_name, {}).get("recent", {}).get("kwh_per_deg_drop")
            rec_cycles = zone_data.get(zone_name, {}).get("recent", {}).get("valid_cycles", 0)
            base_cycles = zone_data.get(zone_name, {}).get("baseline", {}).get("valid_cycles", 0)
            avg_w = (zone_data.get(zone_name, {}).get("recent", {}).get("avg_compressor_watts") or 
                     zone_data.get(zone_name, {}).get("baseline", {}).get("avg_compressor_watts"))

            if base and rec and base > 0:
                deg = round(((rec - base) / base) * 100, 1)
                status = "Healthy"
                if rec_cycles >= MIN_SAMPLE_CYCLES:
                    if deg > 25: status = "Degraded"
                    if deg > 50: status = "Critical"
            else:
                deg = 0.0
                status = "Healthy" if (rec or base) else "Insufficient Data"

            return {
                "status": status,
                "degradation_pct": deg,
                "baseline_kwh_per_deg": base,
                "recent_kwh_per_deg": rec,
                "recent_cycles": rec_cycles,
                "baseline_cycles": base_cycles,
                "avg_compressor_watts": avg_w
            }

        downstairs_res = evaluate_zone("downstairs")
        upstairs_res = evaluate_zone("upstairs")
        office_res = evaluate_zone("office_minisplit")

        statuses = [downstairs_res["status"], upstairs_res["status"], office_res["status"]]
        if "Critical" in statuses:
            overall_status = "Critical"
        elif "Degraded" in statuses:
            overall_status = "Degraded"
        elif all(s == "Insufficient Data" for s in statuses):
            overall_status = "Insufficient Data"
        else:
            overall_status = "Healthy"

        valid_degs = [r["degradation_pct"] for r in [downstairs_res, upstairs_res, office_res] if r["recent_cycles"] >= MIN_SAMPLE_CYCLES]
        max_deg = max(valid_degs) if valid_degs else 0.0
        primary_baseline = upstairs_res["baseline_kwh_per_deg"] or downstairs_res["baseline_kwh_per_deg"]
        primary_recent = upstairs_res["recent_kwh_per_deg"] or downstairs_res["recent_kwh_per_deg"]

        output = {
            "status": overall_status,
            "degradation_pct": max_deg,
            "baseline_rate": round(primary_baseline, 2) if primary_baseline is not None else 0.0,
            "recent_rate": round(primary_recent, 2) if primary_recent is not None else 0.0,
            "upstairs": upstairs_res,
            "downstairs": downstairs_res,
            "office_minisplit": office_res,
            "check_time": str(datetime.now())
        }
    except Exception as e:
        output = {"status": "Error", "detail": str(e), "check_time": str(datetime.now())}

    print(json.dumps(output))

if __name__ == "__main__":
    run_health_check()
