# Climate Engine & BigQuery Analysis Summary

This document summarizes the state of the **Master Bedroom Sleep Comfort Engine (v6.3)** and the integrated **BigQuery HVAC Analytics** as of May 3, 2026.

## 1. Master Bedroom Comfort Engine (v6.3)
The system uses a data-driven "Pre-Cooling" window to ensure the bedroom reaches a target temperature exactly at bedtime. 

### Key Hardening & Logic (v5.8 - v6.3):
- **Jitter Protection:** The engine now uses `sensor.bedroom_temperature_smoothed` (5-minute moving average) and a 2-minute **"Delay-on-Make"** validation in Phase 2 to ensure cooling only starts on persistent temperature rises.
- **Latching (v6.2):** The `binary_sensor.mbr_precool_active` uses latching logic. Once a cooling cycle starts, it remains "ON" until the target is reached, preventing sensor noise from resetting the start-time clock mid-run.
- **Short-Cycle Prevention:** Added a **5-minute minimum run time** in Phase 3 to protect the compressor from rapid cycling.
- **Timezone-Independent Learning:** The learning logic was updated to use a 4-hour window relative to `input_datetime.bedroom_bedtime`, resolving a bug where UTC-based Measure-and-Learn events were being skipped.
- **Hysteresis:** A 0.5°F trigger hysteresis prevents the system from "ping-ponging" when the temperature is hovering exactly at the target.

---

## 2. BigQuery Analysis Environment
Following the Home Assistant 2026.4.4 upgrade, the analysis environment was modernized to support **Python 3.14.2**.

### Environment Organization:
1. **VENV:** `bq_venv/` (Recreated May 2026 with Python 3.14).
2. **Operational Scripts (`bin/`):** Contains `hvac_health_check.py` which runs daily.
3. **Research Tools (`tools/`):** Cold storage for calibration scripts (e.g., `thermal_decay_analysis.py`).
4. **Credentials:** Absolute path mapping used for `/config/bigquery_credentials.json` to ensure container-wide compatibility.

---

## 3. The Performance Repository (Night-Optimized)
The `input_text.mbr_cooling_performance_data` repository now stores learned cooling rates. The `initial:` YAML value has been removed to allow for persistent state restoration across restarts.

### Current Performance String (Verified 5/3):
```json
{"45":20.1, "50":8.6, "55":18.0, "60":26.8, "65":34.4, "70":17.2, "75":55.0, "80":62.0, "85":70.0, "90":80.0}
```
*Note: The **50 Bin** (8.6) and **55 Bin** (18.0) were recently calibrated to fix "early start" errors.*

---

## 4. HVAC Health & Anomaly Detection
### Baseline Performance (Verified 5/1):
- **Status:** Healthy
- **Degradation:** -26.1% (Efficiency **Improved**).
- **Baseline Rate:** 40.01 min/deg.
- **Recent Rate:** 29.57 min/deg.

---

## 5. Maintenance Notes
- **Smoothing:** If temperature response feels "laggy," reduce the moving average window in the `sensor.bedroom_temperature_smoothed` UI settings.
- **Manual Calibration:** If the system consistently starts too early/late for a specific outdoor temperature, manually adjust that bin in the performance string via Developer Tools.
