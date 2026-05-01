import os
from google.cloud import bigquery

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/config/bigquery_credentials.json"
client = bigquery.Client()

query = """
SELECT 
  timestamp,
  value
FROM `moonlit-botany-293421.home_assistant_data.climate_analytics`
WHERE entity_id = 'timer.timer_hvac_filter'
ORDER BY timestamp DESC
LIMIT 50
"""

try:
    results = client.query(query)
    for row in results:
        print(f"{row.timestamp} | {row.value}")
except Exception as e:
    print(f"Error querying timer state: {e}")
