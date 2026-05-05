# The Master Bedroom Sleep Comfort Engine: Evolution & Architecture

This document tracks the history, rationale, and current state of the MBR Climate Engine. It is intended to provide context for future engineering sessions.

## 1. The Core Purpose (The "Why")
The engine's goal is to ensure the Master Bedroom reaches a precise sleep temperature (e.g., 64°F) exactly at bedtime, while minimizing AC runtime and protecting equipment. This is achieved by calculating a dynamic "Start Time" based on real-world cooling rates tied to outdoor temperature bins.

---

## 2. Phase I: The Data-Driven Foundation (v1.0 - v5.6)
**Key Milestone:** Establishing the "Night-Optimized" Performance Repository.
- **Architecture:** The system began using `input_text.mbr_cooling_performance_data` to store cooling rates (min/deg) for 5-degree outdoor temperature bins.
- **The Solar Penalty:** Analysis of BigQuery data revealed that the structure cools ~20% slower during the day.
- **The Heat Soak:** Measuring confirmed that at 8:00 PM, the attic "radiates" heat, making cooling harder than earlier in the afternoon.
- **The 60°F Rule:** A hard setpoint of 60°F was used during the "push" to ensure consistent cooling velocity for learning.

---

## 3. Phase II: Physical Hardening (v5.8 - v6.3)
**Key Milestone:** Overcoming sensor jitter and real-world race conditions.
- **The Jitter Problem:** High-frequency fluctuations in the bedroom sensor were causing "ping-pong" cycles (AC turning off/on in sub-60-second windows).
- **Hardening Solutions:**
    - **Smoothing (v6.3):** Integrated `sensor.bedroom_temperature_smoothed` (5-min moving average) to filter noise.
    - **Latching (v6.2):** Once a cycle starts, it remains "ON" until the target is reached, regardless of temporary sensor bounces.
    - **Validation (v6.0):** Added a 2-minute "Delay-on-Make" to ensure the high temp is persistent before triggering the compressor.
    - **Short-Cycle Prevention:** Enforced a 5-minute minimum run time for compressor health.
- **Timezone Correction (v6.1):** Fixed a bug where UTC-based Measure-and-Learn events were being ignored because they fell outside a hardcoded "Local Hour" window.

---

## 4. Phase III: The Intelligence Era (v7.0 Pilot)
**Key Milestone:** Moving from "Math-Only" to "Heuristic Reasoning" using AI.
- **The Strategy:** Version 7.0 introduced the `ai_task` (LLM) engine as a logic co-processor to handle nuance that math templates struggle with.
- **Free Cooling Strategist:** At 7:00 PM, the AI analyzes the forecast. If the outdoors is $\ge$ 3°F cooler, it suggests opening the patio door to achieve "Free Cooling," potentially saving ~20% AC runtime.
- **Comfort Optimizer:** The AI evaluates humidity. If >55%, it automatically lowers the sleep target by 1°F to prioritize dehumidification (Comfort Index) over raw temperature.
- **The Auditor:** A "Self-Healing" gate for the repository. The AI reviews every cooling session's duration/drop. If the math looks like an anomaly (e.g., cooling 1 degree in 1 minute), the AI blocks the update to prevent repository corruption.

---

## 5. Integrated Analytics & Health
- **BigQuery Pipeline:** All HVAC actions and temperature changes are streamed to GCP for long-term trend analysis.
- **HVAC Health Check:** A daily script (`hvac_health_check.py`) compares the last 7 days of performance to a 45-day baseline. This acts as a "Check Engine" light for dirty filters or refrigerant loss.
- **Current Baseline (Verified 5/1/26):**
    - **Baseline:** 40.01 min/deg
    - **Recent:** 29.57 min/deg (Efficiency **Improved** due to recent optimizations).

---

## 7. Phase IV: Global Presence & Conservation (v7.1)
**Key Milestone:** Bridging the gap between long-distance travel and home-state intelligence.
- **The 500-Mile Rule (v7.1):** Upgraded the `Person: Status Synchronizer` to treat any distance >500 miles as an immediate "Extended Away" event. This bypasses the traditional 24-hour clock, allowing Eco Mode to engage the moment you cross the state line.
- **Unified Voice Consolidation:** Centralized all Eco Mode messaging into a single "Manager" automation. Removed redundant notifications from the Alarm system to ensure a consistent interaction style and reliable notification tagging (`eco-finish`).
- **AI Extension Parser:** Integrated a natural language processor into the notification flow. Users can now reply with "until Sunday" or "a few more days," and the AI converts this into a precise second-based timer.
- **Pet-Friendly Seasonal Targets:** Established a conservation baseline that protects the home's permanent residents (the cats):
    - **Heating Season:** 66°F
    - **Cooling Season:** 74°F
- **Proximity-Based Recovery:** Implemented a 50-mile "Homebound" trigger. If **both** Josh and MJ enter this radius, the system automatically releases Eco Mode, allowing the T6 Pro to begin its 6-degree recovery pull before they arrive.

---

## 8. Current Configuration (As of May 5, 2026)
- **Active Version:** v7.1 (Presence-Aware AI Mode).
- **Core Repository:** `{"45":20.1, "50":21.0, "55":18.0, "60":26.8, "65":34.4, "70":17.2, "75":55.0, "80":62.0, "85":70.0, "90":80.0}`
- **Persistence:** YAML `initial` values removed; state is managed via `restore_state` and learned measurements.
