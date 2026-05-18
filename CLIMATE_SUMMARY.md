# The Master Bedroom Sleep Comfort Engine: Evolution & Architecture

This document tracks the history, rationale, and current state of the MBR Climate Engine. It is intended to provide context for future engineering sessions.

## 1. The Core Purpose (The "Why")
The engine's goal is to ensure the Master Bedroom reaches a precise sleep temperature (e.g., 64°F) exactly at bedtime, while minimizing AC runtime and protecting equipment. This is achieved by calculating a dynamic "Start Time" based on real-world cooling rates tied to outdoor temperature bins.

---

## 2. Physical Environment & Infrastructure
Understanding the system requires understanding the physical structure, mechanical architecture, and environmental orientation of the home.

### **Home Layout & Zones**
- **Floor 1 (Primary Living):** Designed with a clear separation between "Active Zones" and "Rest Zones."
    - **Great Room:** A large open-concept Foyer, Dining Area, and Living Room (containing the main downstairs thermostat).
    - **Master Suite (Rear Right):** The primary focus of the Climate Engine. It is physically buffered from the living area by a small transition hall and the Master Bath/Walk-In Closet complex. **Crucially, it possesses a dedicated return duct with an extremely short path to the air handler located in the crawl space directly beneath it.**
    - **Guest Wing (Far Left):** A dedicated wing containing two bedrooms and a shared bath.
    - **Service/Utility:** Laundry and Pantry areas provide a thermal/sound buffer between the Kitchen and the Garage.
- **Floor 2 (Work & Guest Zones):**
    - **The Office (Far Left):** Isolated at the end of a long hallway, functioning as a distinct thermal zone.
    - **Secondary Living:** Guest bedroom and bathroom.
    - **Bonus Room:** A large auxiliary space located over the Garage.

### **HVAC Infrastructure (Three Independent Systems)**
1.  **First Floor Central (Trane 2.5-Ton):**
    *   **Unit:** Model 4TWR4030D1000AA (Heat Pump).
    *   **Age:** Manufactured July 2015 (~10 years old).
    *   **Configuration:** The outdoor condenser is on the right side of the house. The indoor air handler is situated in the **crawl space directly under the Master Suite**.
    *   **Thermal Advantage:** The MBR's dedicated short-path return duct allows for rapid thermal response and higher air-exchange efficiency compared to the rest of the floor.
2.  **Second Floor Central (Trane 2-Ton):**
    *   **Unit:** Model 5TWR4024A1000AA (Heat Pump).
    *   **Age:** Brand New (April 2025).
    *   **Configuration:** Indoor air handler is in a second-floor hallway closet; its thermostat is in the hallway.
3.  **Office Mini-Split (Mr. Cool 1-Ton):**
    *   **Unit:** Dedicated split-type heat pump.
    *   **Age:** Brand New (2025).
    *   *Function:* Provides isolated climate control specifically for the 2nd-floor library/office, making it thermally independent.

### **Thermal Dynamics & Strategy Context**
- **The "Free Cooling" Path:** The Master Bedroom has a heavy exterior door leading directly to the **Screened Porch**. Opening this door creates a powerful thermal siphon, allowing outside air to "super-cool" the room significantly faster than the AC.
- **Main Return Lag:** The main house return vent is in the guest wing hall, approx 30' from the air handler, creating a slower thermal response in the common areas compared to the MBR.
- **The Staircase Chimney:** The staircase is located immediately outside the MBR door (featuring a coat closet underneath, opposite the garage entry). It acts as a natural conduit for heat rising from the first floor to the long second-floor hallway.
- **Year-Round Target:** The MBR target remains ~64°F regardless of season, acting as a "cold-pocket" even when the rest of the home is heated.

### **Environmental Orientation (Solar Load Modeling)**
- **Geospatial:** 37.4762975, -77.8725747
- **House Front:** 8.6° (North-Northeast).
- **Screened Porch:** 188.6° (South-Southwest). This area experiences significant late-afternoon solar gain, directly impacting MBR "Free Cooling" viability.
- **Garage Door:** 278.6° (West-Northwest).

---

## 3. Phase I: The Data-Driven Foundation (v1.0 - v5.6)
**Key Milestone:** Establishing the "Night-Optimized" Performance Repository.
- **Architecture:** The system began using `input_text.mbr_cooling_performance_data` to store cooling rates (min/deg) for 5-degree outdoor temperature bins.
- **The Solar Penalty:** Analysis of BigQuery data revealed that the structure cools ~20% slower during the day.
- **The Heat Soak:** Measuring confirmed that at 8:00 PM, the attic "radiates" heat, making cooling harder than earlier in the afternoon.
- **The 60°F Rule:** A hard setpoint of 60°F was used during the "push" to ensure consistent cooling velocity for learning.

---

## 4. Phase II: Physical Hardening (v5.8 - v6.3)
**Key Milestone:** Overcoming sensor jitter and real-world race conditions.
- **The Jitter Problem:** High-frequency fluctuations in the bedroom sensor were causing "ping-pong" cycles (AC turning off/on in sub-60-second windows).
- **Hardening Solutions:**
    - **Smoothing (v6.3):** Integrated `sensor.bedroom_temperature_smoothed` (5-min moving average) to filter noise.
    - **Latching (v6.2):** Once a cycle starts, it remains "ON" until the target is reached, regardless of temporary sensor bounces.
    - **Validation (v6.0):** Added a 2-minute "Delay-on-Make" to ensure the high temp is persistent before triggering the compressor.
    - **Short-Cycle Prevention:** Enforced a 5-minute minimum run time for compressor health.
- **Timezone Correction (v6.1):** Fixed a bug where UTC-based Measure-and-Learn events were being ignored because they fell outside a hardcoded "Local Hour" window.

---

## 5. Phase III: The Intelligence Era (v7.0 Pilot)
**Key Milestone:** Moving from "Math-Only" to "Heuristic Reasoning" using AI.
- **The Strategy:** Version 7.0 introduced the `ai_task` (LLM) engine as a logic co-processor to handle nuance that math templates struggle with.
- **Free Cooling Strategist:** At 7:00 PM, the AI analyzes the forecast. If the outdoors is $\ge$ 3°F cooler, it suggests opening the patio door to achieve "Free Cooling," potentially saving ~20% AC runtime.
- **Comfort Optimizer:** The AI evaluates humidity. If >55%, it automatically lowers the sleep target by 1°F to prioritize dehumidification (Comfort Index) over raw temperature.
- **The Auditor:** A "Self-Healing" gate for the repository. The AI reviews every cooling session's duration/drop. If the math looks like an anomaly (e.g., cooling 1 degree in 1 minute), the AI blocks the update to prevent repository corruption.

---

## 6. Integrated Analytics & Health
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

## 8. Phase V: Operational Hardening (v7.2)
**Key Milestone:** Decoupling intelligence from physical safety.
- **Fail-Safe Architecture:** Implemented `continue_on_error: true` across all AI strategic tasks. The LLM is now a "consultant," not a "blocker." If the AI fails to respond, the system falls back to baseline targets, ensuring critical actions (like the AC handoff) always occur.
- **Data Armor (The Swing Cap):** Added a physical constraint to the repository learning logic. Even if a session passes the AI Auditor, bin updates are capped at a maximum shift of ±5 minutes per night to prevent repository corruption from extreme outliers.
- **Critical Template Fix:** Resolved a Jinja2 `TypeError` regarding dynamic dictionary keys that previously caused automation crashes and AC overshoots during the handoff phase.

---

## 9. Phase VI: Logical Integrity & Cleanup (v7.3)
**Key Milestone:** Internal logic consistency and code maintenance.
- **Redundant Trigger Cleanup:** Eliminated duplicate triggers in the `MBR Climate Engine` that were causing multiple AI calls for a single event.
- **Repository Normalization:** Standardized all JSON keys to strings to ensure consistent lookups.

---

## 10. Phase VII: Operational Transparency (v7.4)
**Key Milestone:** Exposing the AI's "Thought Process" and ensuring session accountability.
- **Full-Visibility Notifications (May 11, 2026):** Overhauled the notification engine to include the AI Auditor's raw qualitative analysis in mobile alerts. This provides the user with the "why" behind every learning decision (e.g., specific reasoning for valid sessions or detected anomalies).
- **Unconditional Reporting:** Decoupled the final session reporting from the AI Auditor's status. The system now guarantees a mobile notification and a CSV log entry for every `PHASE_3_HANDOFF`, ensuring no session completes silently, even if the AI API times out.
- **Math Breakdown:** Exposed the internal learning math (Observed Rate vs. Repository Baseline vs. Weighted Result) directly in the user interface and notifications, enabling instant human verification of the Data Armor v2 logic.
- **Environmental Insight:** BigQuery correlation analysis confirmed that **Outdoor Temperature** (correlation ~0.57) is the primary driver of cooling performance, while **Indoor Temperature** at session start has negligible impact (correlation ~-0.06), validating the 5-degree outdoor bin architecture.

---

## 11. Phase VIII: Logic Certification & Precision Math (v7.7)
**Key Milestone:** Eliminating math drift and hardening the logic through simulation.
- **Continuous Logic Validation (CLV):** Introduced a "Sim Lab" (`integrations/sim_lab.yaml`) - a digital twin environment used to run "Lethal Scenarios" (Flash Freezes, Bedtime Races). Logic is now considered "Certified" only after passing all 5 simulation tests.
- **The Unbreakable Latch:** Moved the "Active Push" check to the absolute top of the handoff conditions. The engine is now physically unable to double-command the thermostat because it verifies the current setpoint (must be 60°F) before evaluating any other handoff triggers.
- **Precision Math (Native Epochs):** Switched from fragile string-based time parsing to native epoch timestamps (`state_attr(..., 'timestamp')`). This eliminated a recurring 60-minute duration drift caused by timezone interpretation errors.
- **Total Transparency (v7.7):** 
    - **Phase 2 Mobile Visibility:** Real-time notifications when pre-cooling starts, including AI's "Comfort reasoning" and arrival estimates.
    - **Maintenance Visibility:** Mobile alerts for nightly Phase 4 (Maintenance Push) and Phase 5 (Over-Cool Guard) actions.
    - **Reasoning Logs:** The CSV log now captures the qualitative AI reasoning for every decision, providing a complete audit trail.
- **Ghost Engine Exorcism:** Completely removed the retired v6.3 automation from the codebase to eliminate background logic interference.

---

## 12. Phase IX: Repository Hardening & Environmental Averaging (v7.8)
**Key Milestone:** Resolving type-casting duplicates and improving environmental precision.
- **Int-Win String Pattern (May 13, 2026):** Resolved a critical repository duplication bug caused by Home Assistant's inconsistent JSON type-casting. The system now explicitly forces all keys to strings during both the `get()` lookup and the `combine` merge, ensuring that new data perfectly overwrites existing bins without creating duplicates.
- **Global Short-Cycle Blocker:** Hardened the Phase 3 learning gate to strictly require a minimum session duration of **5 minutes** for all triggers. This prevents the engine from learning from unreliable, short-burst data (e.g., bedtime triggers that occur immediately after manual overrides).
- **Outdoor Temperature Averaging:** Transitioned from "Point-in-Time" binning to "Session Averaging." The system now captures the outdoor temperature at Phase 2 Start and averages it with the temperature at Phase 3 Handoff. This ensures performance data is stored in the bin most representative of the actual environmental conditions during the entire cooling pull.
- **Sim Lab Expansion:** Added two new stress test scenarios (Scenario G: Short-Cycle Block and Scenario H: Bin Averaging) to the validation suite. The Climate Engine v7.8 passed all 8 scenarios before deployment.

---

## 13. Phase X: The Definitive Fix - Single-Pass Clean-Sweep (v7.8.3)
**Key Milestone:** Eliminating the "Troubleshooting Loop" via internal Jinja memory hardening.
- **Single-Pass Consolidated Logic:** Transitioned all repository management (Load, Normalize, Lookup, and Merge) into a single, atomic Jinja template. This prevents Home Assistant from re-parsing and corrupting data types between variable blocks.
- **Clean-Sweep Pattern:** Implemented a list-based merging strategy that explicitly filters out any key matching the target bin (regardless of original type) before rebuilding the dictionary. This makes JSON duplicate keys mathematically impossible.
- **Whitespace Hardening:** Identified and fixed a bug where multi-line Jinja blocks were appending hidden newlines (`\n`) to keys. Added aggressive `| trim` and whitespace-stripping tags (`{%- ... -%}`) to ensure 100% string alignment.
- **Incremental Sorting:** Added a post-merge sort filter, ensuring the performance repository is always stored in incremental bin order for better human readability.
- **Sim Lab Certification:** Added Scenario J (Type Mismatch Challenge) to the stress tests. v7.8.3 passed all 10 scenarios with zero duplicates and perfect data armor enforcement.
- **Bug Fix (May 17, 2026):** Resolved an `UndefinedError` in the Data Armor block where the variable `cap` was incorrectly referenced as `cp` in certain branches.

---

## 14. Phase XI: Safety-First Hardening & Mode Normalization (v7.8.4)
**Key Milestone:** Eliminating "Handoff Shadowing" and zombie automation queues.
- **The "Off the Rails" Failure (May 16, 2026):** A logic crash (the `cp` typo) occurred *inside* the Phase 3 Learning block. Because the thermostat reset command was located *after* the learning logic, the crash prevented the AC from ever being reset to its maintenance target. The system remained stuck in an "Agonal Push" (60°F), causing the room to drop to 56°F until manually intervened.
- **Safety-First Handoff:** Refactored Phase 3 to perform the `climate.set_temperature` reset to the maintenance target at the **absolute start** of the sequence. This ensures that even if the AI Auditor or repository math fails, the home remains at a safe temperature.
- **Mode Shift (Queued -> Restart):** 
    - **Historical Context:** `mode: queued` was originally implemented to handle AI co-processor latency (10s+), ensuring sequential processing of triggers. However, this led to "Zombie Queues" where old, invalid data could be saved after a crash/recovery.
    - **Engineering Standard (v7.8.4):** Transitioned to `mode: restart`. When combined with the "Safety-First" handoff, this creates an "Atomic Lock." Once the thermostat is reset at the start of Phase 3, any subsequent trigger while the AI is thinking will restart the automation, find the thermostat no longer at 60°F, and immediately stop—safely preventing duplicate runs and data corruption.
- **Math Defaults:** Hardened all duration and rate calculations with `| default` and `[..., 1]|max` filters to prevent division-by-zero or undefined variable crashes.

---

## 15. Future Roadmap: Phase XII - Winter Comfort Strategy
**Conceptual Goal:** Pivot the engine from "Aggressive AC" to "Managed Free Cooling" and "Heat Guard."
- **Winter Super-Cooling:** During heating season, the engine will prioritize opening the porch door to achieve the 64°F target. Unlike cooling season, the residents are comfortable with the room dropping **well below** the 64°F target.
- **The Heat Guard:** The engine's primary winter job will be to prevent the HVAC from heating the MBR until it drops below a secondary safety threshold (e.g., 60°F), allowing it to remain a "cold pocket" for better sleep.
- **Dual-Mode Repository:** Future analysis will determine if separate "Heating Season" and "Cooling Season" performance repositories are required to account for the different thermal dynamics of the porch door vs. the HVAC blower.

---

## 16. Current Configuration (As of May 18, 2026)
- **Active Version:** v7.8.4 (Logic Certified).
- **Core Repository:** Managed with **Single-Pass Clean-Sweep** and **Automatic Sorting**.
- **Safety Standard:** **Safety-First Handoff** (thermostat reset before learning) and **Restart Mode** active.
- **Validation Suite:** 10-scenario stress test active in Sim Lab.
- **Persistence:** State managed via `restore_state`; strictly normalized string-keyed JSON.
