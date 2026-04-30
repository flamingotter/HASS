# Climate Engine & BigQuery Analysis Summary

This document summarizes the state of the **Master Bedroom Sleep Comfort Engine (v5.6)** and the integrated **BigQuery HVAC Analytics** as of April 30, 2026.

## 1. Master Bedroom Comfort Engine (v5.6)
The system uses a data-driven "Pre-Cooling" window to ensure the bedroom reaches a target temperature (e.g., 64°F) exactly at bedtime.

### Key Logic:
- **Phase 2 (The Push):** When the automation enters the pre-cool window, it sets the thermostat to a hard **60°F** to force a continuous cooling run.
- **Phase 3 (Handoff & Learning):** Once the target is hit, the system hands off to a maintenance target and calculates the "Actual Rate" of cooling for that session.
- **The Failsafe:** To handle Z-Wave sensor drops, the engine uses `state_attr('climate.t6_pro_downstairs', 'current_temperature')` as a fallback, ensuring the AC never runs indefinitely if the bedroom sensor goes `unavailable`.
- **The 60°F Rule:** The system only "learns" from a session if the thermostat was set to exactly 60°F. Manual overrides or adjustments during the run prevent the repository from being updated with corrupted data.

---

## 2. BigQuery Analysis Environment
To perform deep analysis of HVAC performance, a dedicated Python virtual environment and BigQuery integration were established.

### VENV Setup:
1. **Directory:** `bq_venv/`
2. **Credentials:** `bigquery_credentials.json` (GCP Project: `moonlit-botany-293421`)
3. **Creation Command:**
   ```bash
   python3 -m venv bq_venv
   source bq_venv/bin/activate
   pip install google-cloud-bigquery
   ```

### Data Schema:
The table `moonlit-botany-293421.home_assistant_data.climate_analytics` contains:
- `timestamp`: UTC time of state change.
- `entity_id`: `climate.t6_pro_downstairs` or `sensor.weather_station_temperature_outdoor`.
- `value`: Temperature value.
- `hvac_action`: Current state (cooling, idle, etc.).

---

## 3. The Performance Repository (Night-Optimized)
The core of the "Start Time Calculator" is the `input_text.mbr_cooling_performance_data` repository. 

### Night vs. Day Analysis:
Analysis of 45 days of data revealed a significant **"Solar Penalty"** during the day and a **"Heat Soak"** effect at night:
- **Solar Penalty:** AC is ~20% slower during the day due to direct sun on the structure.
- **Heat Soak:** In the 70°F bin, the AC is actually *slower* at 8:00 PM than at 2:00 PM because the attic is still radiating heat from the day.

### Verified Night-Optimized String:
Used for the 8:00 PM Pre-Cool calculation.
```json
{"45": 20.1, "50": 32.6, "55": 33.6, "60": 26.8, "65": 34.4, "70": 48.5, "75": 55.0, "80": 62.0, "85": 70.0, "90": 80.0}
```

---

## 4. HVAC Health & Anomaly Detection
A "Check Engine" light for the AC was implemented to detect efficiency degradation (e.g., dirty filters or refrigerant loss).

### Architecture:
1. **Script:** `hvac_health_check.py`.
2. **Logic:** Compares the cooling rate (`min/deg`) of the last 7 days against the 45-day baseline for the same outdoor temperature bins.
3. **Sensor:** `sensor.hvac_health_status` (Command Line Sensor).
   - Runs daily via `integrations/command_line.yaml` -> `entities/command_line/hvac_health.yaml`.
4. **Alert:** `System: HVAC Health Alert` in `automations.yaml`.
   - Triggers a notification if efficiency drops by >30% (`Degraded`) or >60% (`Critical`).

### Baseline Performance (Verified 4/28):
- **Baseline:** 40.3 min/deg
- **Recent:** 33.2 min/deg (Efficiency currently **Improved** by 17.8% due to v5.6 updates).

---

## 5. Troubleshooting Notes
- **Sensor Jitter:** If the bedroom sensor reports physically impossible fluctuations (e.g., 1°F jump in 30 seconds), check placement relative to AC vents.
- **Early Starts:** If the system starts too early, it is likely using "Overall" averages instead of "Night-Optimized" rates in the repository.
