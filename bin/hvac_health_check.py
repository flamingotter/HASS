import os
import json
from google.cloud import bigquery
from datetime import datetime

cred_paths = [
    os.path.abspath("bigquery_credentials.json"),
    "/config/bigquery_credentials.json",
    "/opt/docker/secrets/mcp-bq-key.json",
    "/app/service-account.json"
]
for cp in cred_paths:
    if os.path.exists(cp):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cp
        break

client = bigquery.Client()

query = """
WITH raw_combined AS (
  -- Downstairs Telemetry (Floor 1: Master Bedroom & Great Room)
  SELECT 'downstairs' as zone, timestamp, value as hp_power, CAST(NULL AS FLOAT64) as indoor_temp, CAST(NULL AS FLOAT64) as outdoor_temp, 300 as min_run_power
  FROM `moonlit-botany-293421.home_assistant_data.climate_analytics`
  WHERE entity_id = 'sensor.panel_02_downstairs_heat_pump_power'
    AND timestamp >= '2026-08-24T13:35:00Z'
  UNION ALL
  SELECT 'downstairs' as zone, timestamp, NULL as hp_power, value as indoor_temp, NULL as outdoor_temp, 300 as min_run_power
  FROM `moonlit-botany-293421.home_assistant_data.climate_analytics`
  WHERE entity_id = 'climate.t6_pro_downstairs'
    AND timestamp >= '2026-08-24T13:35:00Z'
  UNION ALL
  -- Upstairs Telemetry (Floor 2: Hallway, Bonus Room, Upstairs Bedroom)
  SELECT 'upstairs' as zone, timestamp, value as hp_power, CAST(NULL AS FLOAT64) as indoor_temp, CAST(NULL AS FLOAT64) as outdoor_temp, 300 as min_run_power
  FROM `moonlit-botany-293421.home_assistant_data.climate_analytics`
  WHERE entity_id = 'sensor.panel_01_upstairs_heat_pump_power'
    AND timestamp >= '2026-08-24T13:35:00Z'
  UNION ALL
  SELECT 'upstairs' as zone, timestamp, NULL as hp_power, value as indoor_temp, NULL as outdoor_temp, 300 as min_run_power
  FROM `moonlit-botany-293421.home_assistant_data.climate_analytics`
  WHERE entity_id = 'climate.t6_pro_upstairs'
    AND timestamp >= '2026-08-24T13:35:00Z'
  UNION ALL
  -- Office Mini-Split Telemetry (Floor 2: Office / Library)
  SELECT 'office_minisplit' as zone, timestamp, value as hp_power, CAST(NULL AS FLOAT64) as indoor_temp, CAST(NULL AS FLOAT64) as outdoor_temp, 100 as min_run_power
  FROM `moonlit-botany-293421.home_assistant_data.climate_analytics`
  WHERE entity_id = 'sensor.panel_01_mini_split_power'
    AND timestamp >= '2026-08-24T13:35:00Z'
  UNION ALL
  SELECT 'office_minisplit' as zone, timestamp, NULL as hp_power, value as indoor_temp, NULL as outdoor_temp, 100 as min_run_power
  FROM `moonlit-botany-293421.home_assistant_data.climate_analytics`
  WHERE entity_id = 'sensor.office_sensor_air_temperature'
    AND timestamp >= '2026-08-24T13:35:00Z'
  UNION ALL
  -- Outdoor Temperature for all zones
  SELECT 'downstairs' as zone, timestamp, NULL as hp_power, NULL as indoor_temp, value as outdoor_temp, 300 as min_run_power
  FROM `moonlit-botany-293421.home_assistant_data.climate_analytics`
  WHERE entity_id = 'sensor.weather_station_temperature_outdoor'
    AND timestamp >= '2026-08-24T13:35:00Z'
  UNION ALL
  SELECT 'upstairs' as zone, timestamp, NULL as hp_power, NULL as indoor_temp, value as outdoor_temp, 300 as min_run_power
  FROM `moonlit-botany-293421.home_assistant_data.climate_analytics`
  WHERE entity_id = 'sensor.weather_station_temperature_outdoor'
    AND timestamp >= '2026-08-24T13:35:00Z'
  UNION ALL
  SELECT 'office_minisplit' as zone, timestamp, NULL as hp_power, NULL as indoor_temp, value as outdoor_temp, 100 as min_run_power
  FROM `moonlit-botany-293421.home_assistant_data.climate_analytics`
  WHERE entity_id = 'sensor.weather_station_temperature_outdoor'
    AND timestamp >= '2026-08-24T13:35:00Z'
),
filled AS (
  SELECT 
    zone,
    timestamp,
    hp_power,
    min_run_power,
    LAST_VALUE(indoor_temp IGNORE NULLS) OVER(PARTITION BY zone ORDER BY timestamp ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as indoor_temp,
    LAST_VALUE(outdoor_temp IGNORE NULLS) OVER(PARTITION BY zone ORDER BY timestamp ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as outdoor_temp
  FROM raw_combined
),
runs AS (
  SELECT 
    *,
    CASE 
      WHEN hp_power > min_run_power AND (LAG(hp_power) OVER(PARTITION BY zone ORDER BY timestamp) <= min_run_power OR LAG(hp_power) OVER(PARTITION BY zone ORDER BY timestamp) IS NULL) THEN 1 
      ELSE 0 
    END as is_start
  FROM filled
  WHERE hp_power IS NOT NULL
),
sessions AS (
  SELECT *, SUM(is_start) OVER(PARTITION BY zone ORDER BY timestamp) as session_id
  FROM runs
),
cycle_stats AS (
  SELECT 
    zone,
    session_id,
    MIN(timestamp) as start_time,
    MAX(timestamp) as end_time,
    TIMESTAMP_DIFF(MAX(timestamp), MIN(timestamp), MINUTE) as duration_min,
    AVG(hp_power) as avg_hp_watts,
    ARRAY_AGG(indoor_temp ORDER BY timestamp ASC LIMIT 1)[OFFSET(0)] as start_temp,
    ARRAY_AGG(indoor_temp ORDER BY timestamp DESC LIMIT 1)[OFFSET(0)] as end_temp,
    AVG(outdoor_temp) as avg_outdoor_temp
  FROM sessions
  WHERE hp_power > min_run_power
  GROUP BY zone, session_id, min_run_power
  HAVING duration_min >= 8
     AND (ARRAY_AGG(indoor_temp ORDER BY timestamp ASC LIMIT 1)[OFFSET(0)] - ARRAY_AGG(indoor_temp ORDER BY timestamp DESC LIMIT 1)[OFFSET(0)]) >= 0.3
)
SELECT 
  zone,
  CASE WHEN start_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 3 DAY) THEN 'recent' ELSE 'baseline' END as period,
  COUNT(*) as valid_cycles,
  AVG(duration_min) as avg_duration,
  AVG(avg_hp_watts) as avg_watts,
  AVG(start_temp - end_temp) as avg_temp_drop,
  AVG(avg_outdoor_temp) as avg_outdoor,
  AVG((avg_hp_watts * (duration_min / 60.0) / 1000.0) / (start_temp - end_temp)) as kwh_per_deg_drop
FROM cycle_stats
GROUP BY zone, period
"""

try:
    results = client.query(query)
    zone_data = {}
    for row in results:
        z = row.zone
        p = row.period
        if z not in zone_data:
            zone_data[z] = {}
        zone_data[z][p] = {
            "valid_cycles": row.valid_cycles,
            "avg_duration_min": round(row.avg_duration, 1) if row.avg_duration else None,
            "avg_compressor_watts": round(row.avg_watts, 1) if row.avg_watts else None,
            "avg_temp_drop": round(row.avg_temp_drop, 2) if row.avg_temp_drop else None,
            "avg_outdoor": round(row.avg_outdoor, 1) if row.avg_outdoor else None,
            "kwh_per_deg_drop": round(row.kwh_per_deg_drop, 3) if row.kwh_per_deg_drop else None
        }

    MIN_SAMPLE_CYCLES = 2

    # Helper function to evaluate zone status
    def evaluate_zone(zone_name):
        base = zone_data.get(zone_name, {}).get("baseline", {}).get("kwh_per_deg_drop")
        rec = zone_data.get(zone_name, {}).get("recent", {}).get("kwh_per_deg_drop")
        rec_cycles = zone_data.get(zone_name, {}).get("recent", {}).get("valid_cycles", 0)
        base_cycles = zone_data.get(zone_name, {}).get("baseline", {}).get("valid_cycles", 0)
        avg_w = zone_data.get(zone_name, {}).get("recent", {}).get("avg_compressor_watts") or zone_data.get(zone_name, {}).get("baseline", {}).get("avg_compressor_watts")

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

    # Overall status aggregation
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
