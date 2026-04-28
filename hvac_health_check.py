import os
import json
from google.cloud import bigquery
from datetime import datetime

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "bigquery_credentials.json"
client = bigquery.Client()

query = """
WITH raw_combined AS (
  SELECT timestamp, value as indoor_temp, hvac_action, CAST(NULL AS FLOAT64) as outdoor_temp
  FROM `moonlit-botany-293421.home_assistant_data.climate_analytics`
  WHERE entity_id = 'climate.t6_pro_downstairs'
    AND timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 45 DAY)
  UNION ALL
  SELECT timestamp, NULL as indoor_temp, NULL as hvac_action, value as outdoor_temp
  FROM `moonlit-botany-293421.home_assistant_data.climate_analytics`
  WHERE entity_id = 'sensor.weather_station_temperature_outdoor'
    AND timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 45 DAY)
),
filled_data AS (
  SELECT 
    timestamp, indoor_temp, hvac_action,
    LAST_VALUE(outdoor_temp IGNORE NULLS) OVER(ORDER BY timestamp ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as outdoor_temp
  FROM raw_combined
),
session_markers AS (
  SELECT *,
    CASE WHEN hvac_action = 'cooling' AND (LAG(hvac_action) OVER(ORDER BY timestamp) != 'cooling' OR LAG(hvac_action) OVER(ORDER BY timestamp) IS NULL) THEN 1 ELSE 0 END as is_start
  FROM filled_data
  WHERE hvac_action IS NOT NULL
),
session_ids AS (
  SELECT *, SUM(is_start) OVER(ORDER BY timestamp) as session_id FROM session_markers
),
final_sessions AS (
  SELECT 
    MIN(timestamp) as start_time,
    MAX(timestamp) as end_time,
    ARRAY_AGG(indoor_temp ORDER BY timestamp ASC LIMIT 1)[OFFSET(0)] as start_temp,
    ARRAY_AGG(indoor_temp ORDER BY timestamp DESC LIMIT 1)[OFFSET(0)] as end_temp,
    AVG(outdoor_temp) as avg_outdoor
  FROM session_ids
  WHERE hvac_action = 'cooling'
  GROUP BY session_id
  HAVING TIMESTAMP_DIFF(MAX(timestamp), MIN(timestamp), MINUTE) > 10
     AND (ARRAY_AGG(indoor_temp ORDER BY timestamp ASC LIMIT 1)[OFFSET(0)] - ARRAY_AGG(indoor_temp ORDER BY timestamp DESC LIMIT 1)[OFFSET(0)]) > 0.5
)
SELECT 
  CASE WHEN start_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY) THEN 'recent' ELSE 'baseline' END as period,
  AVG(TIMESTAMP_DIFF(end_time, start_time, MINUTE) / NULLIF(start_temp - end_temp, 0)) as avg_rate
FROM final_sessions
WHERE avg_outdoor BETWEEN 60 AND 85
GROUP BY period
"""

try:
    results = client.query(query)
    data = {}
    for row in results:
        data[row.period] = row.avg_rate
    
    baseline = data.get('baseline')
    recent = data.get('recent')
    
    if not baseline or not recent:
        output = {"status": "insufficient_data", "detail": f"Baseline: {baseline}, Recent: {recent}"}
    else:
        diff_pct = round(((recent - baseline) / baseline) * 100, 1)
        status = "healthy"
        if diff_pct > 30: status = "degraded"
        if diff_pct > 60: status = "critical"
            
        output = {
            "status": status,
            "degradation_pct": diff_pct,
            "baseline_rate": round(baseline, 2),
            "recent_rate": round(recent, 2),
            "check_time": str(datetime.now())
        }
except Exception as e:
    output = {"status": "error", "detail": str(e)}

print(json.dumps(output))
