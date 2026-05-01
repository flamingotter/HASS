import os
from google.cloud import bigquery
from datetime import datetime

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/config/bigquery_credentials.json"
client = bigquery.Client()

query = """
WITH raw_data AS (
  SELECT 
    timestamp,
    value as indoor_temp,
    hvac_action
  FROM `moonlit-botany-293421.home_assistant_data.climate_analytics`
  WHERE entity_id = 'climate.t6_pro_downstairs'
),
outdoor_data AS (
  SELECT 
    timestamp,
    value as outdoor_temp
  FROM `moonlit-botany-293421.home_assistant_data.climate_analytics`
  WHERE entity_id = 'sensor.weather_station_temperature_outdoor'
),
session_markers AS (
  SELECT c.*,
    CASE 
      WHEN (hvac_action != 'cooling' OR hvac_action IS NULL) 
           AND (LAG(hvac_action) OVER(ORDER BY timestamp) = 'cooling') THEN 1 
      ELSE 0 
    END as is_start
  FROM raw_data c
),
session_ids AS (
  SELECT *,
    SUM(is_start) OVER(ORDER BY timestamp) as session_id
  FROM session_markers
),
warming_sessions AS (
  SELECT 
    session_id,
    MIN(timestamp) as start_time,
    MAX(timestamp) as end_time,
    ARRAY_AGG(indoor_temp ORDER BY timestamp ASC LIMIT 1)[OFFSET(0)] as start_temp,
    ARRAY_AGG(indoor_temp ORDER BY timestamp DESC LIMIT 1)[OFFSET(0)] as end_temp
  FROM session_ids
  WHERE hvac_action != 'cooling' OR hvac_action IS NULL
  GROUP BY session_id
  HAVING TIMESTAMP_DIFF(MAX(timestamp), MIN(timestamp), MINUTE) > 30
     AND (ARRAY_AGG(indoor_temp ORDER BY timestamp DESC LIMIT 1)[OFFSET(0)] - ARRAY_AGG(indoor_temp ORDER BY timestamp ASC LIMIT 1)[OFFSET(0)]) >= 0.5
)
SELECT 
  s.*,
  AVG(o.outdoor_temp) as avg_outdoor_temp
FROM warming_sessions s
JOIN outdoor_data o ON o.timestamp BETWEEN s.start_time AND s.end_time
GROUP BY session_id, start_time, end_time, start_temp, end_temp
ORDER BY avg_outdoor_temp DESC
"""

results = client.query(query)

print(f"{'Outdoor Bin':<15} | {'Warming Rate (deg/hr)':<25} | {'Minutes to gain 1F'} | {'Sessions'}")
print("-" * 85)

bins = {}
for row in results:
    duration_hr = (row.end_time - row.start_time).total_seconds() / 3600
    temp_gain = row.end_temp - row.start_temp
    rate = temp_gain / duration_hr
    
    bin_val = int(round(row.avg_outdoor_temp / 10) * 10) # 10 degree bins for cleaner trend
    if bin_val not in bins:
        bins[bin_val] = []
    bins[bin_val].append(rate)

for b in sorted(bins.keys(), reverse=True):
    avg_rate = sum(bins[b]) / len(bins[b])
    min_per_deg = 60 / avg_rate if avg_rate > 0 else 0
    count = len(bins[b])
    print(f"{b}F{'':<12} | {avg_rate:<25.2f} | {min_per_deg:<18.1f} | {count}")

