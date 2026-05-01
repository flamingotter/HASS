import os
import json
from google.cloud import bigquery

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/config/bigquery_credentials.json"
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
    session_id,
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
  *,
  EXTRACT(HOUR FROM start_time AT TIME ZONE "America/New_York") as start_hour
FROM final_sessions
-- Filter for night time: After 7 PM (19) or before 7 AM (7)
WHERE EXTRACT(HOUR FROM start_time AT TIME ZONE "America/New_York") >= 19 
   OR EXTRACT(HOUR FROM start_time AT TIME ZONE "America/New_York") < 7
ORDER BY avg_outdoor DESC
"""

try:
    results = client.query(query)
    
    bins = {}
    for row in results:
        duration = (row.end_time - row.start_time).total_seconds() / 60
        drop = row.start_temp - row.end_temp
        rate = duration / drop
        
        bin_val = int(round(row.avg_outdoor / 5) * 5)
        if bin_val not in bins:
            bins[bin_val] = []
        bins[bin_val].append(rate)

    print(f"{'Outdoor Bin':<15} | {'Night Rate (min/deg)':<25} | {'Sessions'}")
    print("-" * 60)
    
    final_repo = {}
    for b in sorted(bins.keys(), reverse=True):
        avg_bin_rate = sum(bins[b]) / len(bins[b])
        count = len(bins[b])
        final_repo[str(b)] = round(avg_bin_rate, 1)
        print(f"{b}F{'':<12} | {avg_bin_rate:<25.1f} | {count}")

    print("\n--- New Night-Optimized Repository String ---")
    print(json.dumps(final_repo))
    
except Exception as e:
    print(f"Error: {e}")
