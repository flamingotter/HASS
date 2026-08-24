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
  -- Downstairs Telemetry
  SELECT 'downstairs' as zone, timestamp, value as hp_power, CAST(NULL AS FLOAT64) as indoor_temp, CAST(NULL AS FLOAT64) as outdoor_temp
  FROM `moonlit-botany-293421.home_assistant_data.climate_analytics`
  WHERE entity_id = 'sensor.panel_02_downstairs_heat_pump_power'
    AND timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 45 DAY)
  UNION ALL
  SELECT 'downstairs' as zone, timestamp, NULL as hp_power, value as indoor_temp, NULL as outdoor_temp
  FROM `moonlit-botany-293421.home_assistant_data.climate_analytics`
  WHERE entity_id = 'climate.t6_pro_downstairs'
    AND timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 45 DAY)
  UNION ALL
  -- Upstairs Telemetry
  SELECT 'upstairs' as zone, timestamp, value as hp_power, CAST(NULL AS FLOAT64) as indoor_temp, CAST(NULL AS FLOAT64) as outdoor_temp
  FROM `moonlit-botany-293421.home_assistant_data.climate_analytics`
  WHERE entity_id = 'sensor.panel_01_upstairs_heat_pump_power'
    AND timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 45 DAY)
  UNION ALL
  SELECT 'upstairs' as zone, timestamp, NULL as hp_power, value as indoor_temp, NULL as outdoor_temp
  FROM `moonlit-botany-293421.home_assistant_data.climate_analytics`
  WHERE entity_id = 'sensor.bedroom_sensor_air_temperature'
    AND timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 45 DAY)
  UNION ALL
  -- Outdoor Temperature for both zones
  SELECT 'downstairs' as zone, timestamp, NULL as hp_power, NULL as indoor_temp, value as outdoor_temp
  FROM `moonlit-botany-293421.home_assistant_data.climate_analytics`
  WHERE entity_id = 'sensor.weather_station_temperature_outdoor'
    AND timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 45 DAY)
  UNION ALL
  SELECT 'upstairs' as zone, timestamp, NULL as hp_power, NULL as indoor_temp, value as outdoor_temp
  FROM `moonlit-botany-293421.home_assistant_data.climate_analytics`
  WHERE entity_id = 'sensor.weather_station_temperature_outdoor'
    AND timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 45 DAY)
),
filled AS (
  SELECT 
    zone,
    timestamp,
    hp_power,
    LAST_VALUE(indoor_temp IGNORE NULLS) OVER(PARTITION BY zone ORDER BY timestamp ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as indoor_temp,
    LAST_VALUE(outdoor_temp IGNORE NULLS) OVER(PARTITION BY zone ORDER BY timestamp ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as outdoor_temp
  FROM raw_combined
),
runs AS (
  SELECT 
    *,
    CASE 
      WHEN hp_power > 300 AND (LAG(hp_power) OVER(PARTITION BY zone ORDER BY timestamp) <= 300 OR LAG(hp_power) OVER(PARTITION BY zone ORDER BY timestamp) IS NULL) THEN 1 
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
  WHERE hp_power > 300
  GROUP BY zone, session_id
  HAVING duration_min >= 8
     AND (ARRAY_AGG(indoor_temp ORDER BY timestamp ASC LIMIT 1)[OFFSET(0)] - ARRAY_AGG(indoor_temp ORDER BY timestamp DESC LIMIT 1)[OFFSET(0)]) >= 0.3
)
SELECT 
  zone,
  CASE WHEN start_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY) THEN 'recent' ELSE 'baseline' END as period,
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

    # Evaluate Downstairs Zone
    ds_base = zone_data.get("downstairs", {}).get("baseline", {}).get("kwh_per_deg_drop")
    ds_rec = zone_data.get("downstairs", {}).get("recent", {}).get("kwh_per_deg_drop")
    if ds_base and ds_rec and ds_base > 0:
        ds_deg = round(((ds_rec - ds_base) / ds_base) * 100, 1)
        ds_status = "Healthy"
        if ds_deg > 25: ds_status = "Degraded"
        if ds_deg > 50: ds_status = "Critical"
    else:
        ds_deg = 0.0
        ds_status = "Healthy" if (ds_rec or ds_base) else "Insufficient Data"

    # Evaluate Upstairs Zone
    us_base = zone_data.get("upstairs", {}).get("baseline", {}).get("kwh_per_deg_drop")
    us_rec = zone_data.get("upstairs", {}).get("recent", {}).get("kwh_per_deg_drop")
    if us_base and us_rec and us_base > 0:
        us_deg = round(((us_rec - us_base) / us_base) * 100, 1)
        us_status = "Healthy"
        if us_deg > 25: us_status = "Degraded"
        if us_deg > 50: us_status = "Critical"
    else:
        us_deg = 0.0
        us_status = "Healthy" if (us_rec or us_base) else "Insufficient Data"

    # Overall Status Aggregation
    overall_status = "Healthy"
    if "Critical" in [ds_status, us_status]:
        overall_status = "Critical"
    elif "Degraded" in [ds_status, us_status]:
        overall_status = "Degraded"
    elif ds_status == "Insufficient Data" and us_status == "Insufficient Data":
        overall_status = "Insufficient Data"

    max_deg = max(ds_deg, us_deg)
    primary_baseline = ds_base if ds_base is not None else us_base
    primary_recent = ds_rec if ds_rec is not None else us_rec

    output = {
        "status": overall_status,
        "degradation_pct": max_deg,
        "baseline_rate": round(primary_baseline, 2) if primary_baseline is not None else 0.0,
        "recent_rate": round(primary_recent, 2) if primary_recent is not None else 0.0,
        "upstairs": {
            "status": us_status,
            "degradation_pct": us_deg,
            "baseline_kwh_per_deg": us_base,
            "recent_kwh_per_deg": us_rec,
            "recent_cycles": zone_data.get("upstairs", {}).get("recent", {}).get("valid_cycles", 0),
            "baseline_cycles": zone_data.get("upstairs", {}).get("baseline", {}).get("valid_cycles", 0),
            "avg_compressor_watts": zone_data.get("upstairs", {}).get("recent", {}).get("avg_compressor_watts") or zone_data.get("upstairs", {}).get("baseline", {}).get("avg_compressor_watts")
        },
        "downstairs": {
            "status": ds_status,
            "degradation_pct": ds_deg,
            "baseline_kwh_per_deg": ds_base,
            "recent_kwh_per_deg": ds_rec,
            "recent_cycles": zone_data.get("downstairs", {}).get("recent", {}).get("valid_cycles", 0),
            "baseline_cycles": zone_data.get("downstairs", {}).get("baseline", {}).get("valid_cycles", 0),
            "avg_compressor_watts": zone_data.get("downstairs", {}).get("recent", {}).get("avg_compressor_watts") or zone_data.get("downstairs", {}).get("baseline", {}).get("avg_compressor_watts")
        },
        "check_time": str(datetime.now())
    }
except Exception as e:
    output = {"status": "Error", "detail": str(e), "check_time": str(datetime.now())}

print(json.dumps(output))


