#!/usr/bin/env python3
"""
ClickHouse Analytics Skill for Home Assistant.
Provides high-speed local SQL query execution and diagnostic presets
against the home_assistant_data ClickHouse database.
Zero external dependencies (uses urllib.request).
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.parse

CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "127.0.0.1")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", "8124"))
CLICKHOUSE_DB = os.getenv("CLICKHOUSE_DB", "home_assistant_data")

PRESETS = {
    "entities": """
        SELECT 
            entity_id, 
            count() as record_count, 
            min(timestamp) as earliest, 
            max(timestamp) as latest
        FROM home_assistant_data.whole_home_telemetry
        GROUP BY entity_id
        ORDER BY record_count DESC
        LIMIT 50
    """,
    "asymmetry": """
        SELECT 
            toStartOfHour(timestamp) as hour,
            round(avg(if(entity_id = 'sensor.south_attic_sensor_air_temperature', value, null)), 1) as south_attic,
            round(avg(if(entity_id = 'sensor.north_attic_sensor_air_temperature', value, null)), 1) as north_attic,
            round(avg(if(entity_id = 'sensor.south_attic_sensor_air_temperature', value, null)) - 
                  avg(if(entity_id = 'sensor.north_attic_sensor_air_temperature', value, null)), 1) as attic_delta,
            round(avg(if(entity_id = 'sensor.weather_station_temperature_outdoor', value, null)), 1) as outdoor
        FROM home_assistant_data.whole_home_telemetry
        WHERE entity_id IN (
            'sensor.south_attic_sensor_air_temperature',
            'sensor.north_attic_sensor_air_temperature',
            'sensor.weather_station_temperature_outdoor'
        )
        AND timestamp >= now() - INTERVAL 24 HOUR
        GROUP BY hour
        ORDER BY hour DESC
        LIMIT 24
    """,
    "energy": """
        SELECT 
            toDate(timestamp) as day,
            round(max(if(entity_id = 'sensor.panel_01_total_daily_energy', value, 0)) / 1000.0, 2) as p1_kwh,
            round(max(if(entity_id = 'sensor.panel_02_total_daily_energy', value, 0)) / 1000.0, 2) as p2_kwh,
            round((max(if(entity_id = 'sensor.panel_01_total_daily_energy', value, 0)) + 
                   max(if(entity_id = 'sensor.panel_02_total_daily_energy', value, 0))) / 1000.0, 2) as total_kwh
        FROM home_assistant_data.whole_home_telemetry
        WHERE entity_id IN ('sensor.panel_01_total_daily_energy', 'sensor.panel_02_total_daily_energy')
        AND timestamp >= now() - INTERVAL 7 DAY
        GROUP BY day
        ORDER BY day DESC
    """
}

def execute_query(sql, default_format="PrettyCompact"):
    url = f"http://{CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}/?database={CLICKHOUSE_DB}&default_format={default_format}"
    req = urllib.request.Request(url, data=sql.encode("utf-8"), method="POST")
    req.add_header("Content-Type", "text/plain; charset=utf-8")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        sys.stderr.write(f"ClickHouse query error: {e}\n")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="ClickHouse Telemetry Analytics Skill")
    parser.add_argument("query", nargs="?", help="SQL query to execute against home_assistant_data")
    parser.add_argument("--preset", choices=list(PRESETS.keys()), help="Run a pre-compiled diagnostic query")
    parser.add_argument("--format", default="PrettyCompact", help="Output format (PrettyCompact, JSONCompact, CSV, etc.)")
    args = parser.parse_args()

    if args.preset:
        sql = PRESETS[args.preset]
    elif args.query:
        sql = args.query
    else:
        parser.print_help()
        sys.exit(1)

    result = execute_query(sql, default_format=args.format)
    print(result)

if __name__ == "__main__":
    main()
