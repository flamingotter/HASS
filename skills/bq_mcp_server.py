#!/usr/bin/env python3
"""
BigQuery stdio MCP Server.
Implements Model Context Protocol (MCP) JSON-RPC 2.0 over stdio.
Enables instant, permission-less BigQuery querying and analytics for AI agents.
"""

import sys
import json
import subprocess
import traceback

def execute_bq_sql(sql):
    """Executes SQL via docker exec ha_bq_exporter."""
    cmd = ["docker", "exec", "ha_bq_exporter", "python3", "/app/bq_analytics.py", "query", sql]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        if res.returncode == 0:
            return res.stdout.strip()
        else:
            return f"Error executing BigQuery query:\n{res.stderr.strip()}"
    except Exception as e:
        return f"Error executing docker delegate: {e}"

def execute_bq_preset(preset_name):
    """Executes preset query via docker exec ha_bq_exporter."""
    cmd = ["docker", "exec", "ha_bq_exporter", "python3", "/app/bq_analytics.py", "presets", preset_name]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        if res.returncode == 0:
            return res.stdout.strip()
        else:
            return f"Error executing BigQuery preset:\n{res.stderr.strip()}"
    except Exception as e:
        return f"Error executing docker delegate: {e}"

def get_tools_list():
    return [
        {
            "name": "bigquery_query",
            "description": "Execute any SQL query against Home Assistant's Google BigQuery dataset (moonlit-botany-293421.home_assistant_data).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "Standard SQL query to execute."
                    }
                },
                "required": ["sql"]
            }
        },
        {
            "name": "bigquery_preset",
            "description": "Execute a pre-compiled diagnostic query (entities, velocity, decay, asymmetry).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "preset": {
                        "type": "string",
                        "enum": ["entities", "velocity", "decay", "asymmetry"],
                        "description": "The preset diagnostic name."
                    }
                },
                "required": ["preset"]
            }
        },
        {
            "name": "bigquery_energy_summary",
            "description": "Retrieve daily energy consumption (kWh) per panel, HVAC sub-circuit breakdown, and outdoor temperature correlation.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days of history to fetch (default 7).",
                        "default": 7
                    }
                }
            }
        }
    ]

def handle_energy_summary(days=7):
    sql = f"""
    WITH daily_maxes AS (
      SELECT 
        DATE(timestamp, 'America/New_York') as day,
        entity_id,
        MAX(value) / 1000.0 as kwh
      FROM `moonlit-botany-293421.home_assistant_data.climate_analytics`
      WHERE entity_id LIKE '%daily_energy'
        AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
      GROUP BY day, entity_id
    ),
    pivoted AS (
      SELECT
        day,
        MAX(CASE WHEN entity_id = 'sensor.panel_01_total_daily_energy' THEN kwh ELSE 0 END) as p1_total,
        MAX(CASE WHEN entity_id = 'sensor.panel_02_total_daily_energy' THEN kwh ELSE 0 END) as p2_total,
        MAX(CASE WHEN entity_id = 'sensor.panel_01_upstairs_heat_pump_daily_energy' THEN kwh ELSE 0 END) as up_hp,
        MAX(CASE WHEN entity_id = 'sensor.panel_01_upstairs_air_handler_daily_energy' THEN kwh ELSE 0 END) as up_ah,
        MAX(CASE WHEN entity_id = 'sensor.panel_02_downstairs_heat_pump_daily_energy' THEN kwh ELSE 0 END) as down_hp,
        MAX(CASE WHEN entity_id = 'sensor.panel_02_downstairs_air_handler_daily_energy' THEN kwh ELSE 0 END) as down_ah,
        MAX(CASE WHEN entity_id = 'sensor.panel_01_mini_split_daily_energy' THEN kwh ELSE 0 END) as mini_split,
        MAX(CASE WHEN entity_id = 'sensor.panel_01_network_rack_daily_energy' THEN kwh ELSE 0 END) as network_rack,
        MAX(CASE WHEN entity_id = 'sensor.panel_02_water_heater_daily_energy' THEN kwh ELSE 0 END) as water_heater,
        MAX(CASE WHEN entity_id = 'sensor.panel_02_well_daily_energy' THEN kwh ELSE 0 END) as well_pump
      FROM daily_maxes
      GROUP BY day
    ),
    temps AS (
      SELECT 
        DATE(timestamp, 'America/New_York') as day,
        ROUND(MAX(value), 1) as max_outdoor_temp,
        ROUND(AVG(value), 1) as avg_outdoor_temp
      FROM `moonlit-botany-293421.home_assistant_data.climate_analytics`
      WHERE entity_id = 'sensor.weather_station_temperature_outdoor'
        AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
      GROUP BY day
    )
    SELECT 
      p.day,
      ROUND(p.p1_total + p.p2_total, 2) as total_house_kwh,
      ROUND(p.up_hp + p.up_ah + p.down_hp + p.down_ah + p.mini_split, 2) as total_hvac_kwh,
      ROUND((p.up_hp + p.up_ah + p.down_hp + p.down_ah + p.mini_split) / NULLIF(p.p1_total + p.p2_total, 0) * 100, 1) as hvac_percent,
      ROUND(p.up_hp + p.up_ah, 2) as upstairs_hvac_kwh,
      ROUND(p.down_hp + p.down_ah, 2) as downstairs_hvac_kwh,
      ROUND(p.mini_split, 2) as mini_split_kwh,
      ROUND(p.network_rack, 2) as network_rack_kwh,
      ROUND(p.well_pump, 2) as well_pump_kwh,
      ROUND(p.water_heater, 2) as water_heater_kwh,
      t.max_outdoor_temp,
      t.avg_outdoor_temp
    FROM pivoted p
    LEFT JOIN temps t ON p.day = t.day
    ORDER BY p.day ASC
    """
    return execute_bq_sql(sql)

def handle_tool_call(name, args):
    if name == "bigquery_query":
        sql = args.get("sql", "")
        if not sql:
            return "Error: 'sql' argument is required."
        return execute_bq_sql(sql)
    elif name == "bigquery_preset":
        preset = args.get("preset", "")
        if not preset:
            return "Error: 'preset' argument is required."
        return execute_bq_preset(preset)
    elif name == "bigquery_energy_summary":
        days = args.get("days", 7)
        return handle_energy_summary(days)
    else:
        return f"Error: Unknown tool '{name}'"

def main():
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            line = line.strip()
            if not line:
                continue
            
            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})
            
            if method == "initialize":
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "bigquery",
                            "version": "1.0.0"
                        }
                    }
                }
                sys.stdout.write(json.dumps(res) + "\n")
                sys.stdout.flush()
                
            elif method == "notifications/initialized":
                pass
                
            elif method == "ping":
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {}
                }
                sys.stdout.write(json.dumps(res) + "\n")
                sys.stdout.flush()
                
            elif method == "tools/list":
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "tools": get_tools_list()
                    }
                }
                sys.stdout.write(json.dumps(res) + "\n")
                sys.stdout.flush()
                
            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                
                output = handle_tool_call(tool_name, tool_args)
                
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": output
                            }
                        ],
                        "isError": False
                    }
                }
                sys.stdout.write(json.dumps(res) + "\n")
                sys.stdout.flush()
                
            else:
                if req_id is not None:
                    res = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {method}"
                        }
                    }
                    sys.stdout.write(json.dumps(res) + "\n")
                    sys.stdout.flush()
                    
        except Exception as e:
            sys.stderr.write(f"MCP server exception: {traceback.format_exc()}\n")

if __name__ == "__main__":
    main()
