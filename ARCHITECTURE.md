# Home Assistant System Architecture

This document maps the logical flow and inter-dependencies of the core automation engines in this smart home.

---

## 1. Presence & Mode Engine (The Authority Model)
The system uses a strict **Authority -> Reactor** architecture to prevent race conditions during person status changes.

### **The Authority:** `Person: Status Synchronizer`
- **Responsibility:** The ONLY automation permitted to change `input_select.josh_status` or `input_select.mj_status`.
- **States:** `Home` -> `Just Left` -> `Away` -> `Extended Away`.
- **Triggers:** 
    - **Time:** Transitions from `Away` to `Extended Away` after 24 hours.
    - **Distance:** Transitions immediately to `Extended Away` if distance > 500 miles (2,640,000 ft).
    - **Debounce:** 3-minute timers on "Just Arrived" and "Just Left" to prevent GPS jitter.

### **The Reactor:** `Alarm panel functions and mode actions`
- **Responsibility:** Syncs the physical security state to the logical presence state.
- **Logic:** 
    - Both `Away` -> Arms Away.
    - Both `Extended Away` -> Arms Vacation (Eco Mode).
    - Either `Home/Just Arrived` -> Disarms Alarm.

---

## 2. Eco Mode State Machine
Eco Mode manages the home during long-term absences (Vacation).

- **Activation:** Triggered when the Alarm Panel enters `armed_vacation`.
- **Manager (`v7.1`):** Centralizes all messaging and timers under `tag: eco-finish`.
- **The Timer:** `timer.timer_eco_mode_normal` dictates the duration.
- **AI Extension:** Uses `ai_task` to parse natural language (e.g., "until Monday") into timer seconds.
- **Homebound Recovery:** 
    - **Threshold:** 50 miles (264,000 ft).
    - **Condition:** BOTH Josh and MJ must be within the radius.
    - **Action:** Turns off `input_boolean.eco_mode`, releasing the Climate Engine to begin recovery.

---

## 3. MBR Climate Engine (v7.2)
A high-precision engine designed to reach sleep temperature exactly at bedtime.

- **Data Repository:** `input_text.mbr_cooling_performance_data` (JSON). Stores min/deg cooling rates in 5-degree outdoor bins.
- **Phases:**
    1. **Wakeup:** Reset to 68°F.
    2. **Strategist (7:00 PM):** AI evaluates "Free Cooling" via patio door.
    3. **Pre-Cooling:** Aggressive push to 60°F based on bin math + AI Humidity Optimizer.
    4. **Handoff:** At target, reset T6 Pro to maintenance temp. AI Auditor validates session data.
    5. **Sleep Window:** Maintenance loop (+/- 2°F drift protection).
- **Safety Layers:**
    - **Fail-Safe AI:** `continue_on_error: true` on all tasks.
    - **Data Armor:** ±5 min/deg maximum swing per learning session.

---

## 4. Maintenance & Notification Layer
### **Maintenance Engine (v2.0)**
- **Discovery:** Dynamically watches all `timer.maintenance_*` entities.
- **Persistence:** Logs completion events to `maintenance_log.csv` via `script.system_log_maintenance_task`.
- **Nag Logic:** Re-notifies upon arrival or notification clear if the task is still idle.

### **Notification Standards**
- **Actionable:** Heavily utilizes `REPLY` and custom actions.
- **Threaded:** Uses strict `tag` management to prevent notification clutter:
    - `eco-finish`: Presence/Vacation.
    - `pets-notify`: Feeding.
    - `trash-notify`: Waste management.
    - `cleaning-warning`: Cleaning mode persistence.

---

## 6. Physical Interface Layer
The system uses specialized physical interfaces to bridge the gap between hardware and digital logic.

### **The Hub:** `System: NFC Tag Manager`
- **Logic:** Variable-based "Switchboard" (`tag_map`) that maps unique `tag_id`s to actions and entities.
- **Handling:** Uses robust ID detection to capture both direct `tag_id` and event-based payloads.
- **Standard Tags:** Handles simple toggles for infrastructure like `garage` (Shuttle Bay) and `cam_alerts` (Camera Alerts).

### **Lighting Control (Scene Mode):**
Used for instant response in rooms with smart bulbs and Zooz toggle dimmers (ZEN24, ZEN74).
- **Configuration:** Switch local/Z-Wave control is disabled; Central Scene mode is enabled.
- **Flow:** `zwave_js_value_notification` -> Automation (Logic) -> `light.turn_on/off`.
- **Rooms:** Dining Room (v2.0), Office.
### **Notification Strategy (The Detective Butler):**
Used in multi-user chore automations (e.g., Feed Pets v3.0, Trash Day).
- **Logic:** Uses a consolidated `scanned_device` variable to capture IDs from both physical NFC scans (`trigger.device_id`) and notification button actions (`trigger.event.data.device_id`).
- **Standard:** Explicitly maps IDs to names (`scanned_name`) and target notification services (`target_notify`). This ensures the "other" person is always notified correctly without fragile `else` fallbacks.

---

## 4. Climate Control (The Sleep Engine)
...
### **Data Integrity (The Learning Gate):**
To ensure the performance repository remains "pure," the system implements a strict gate:
- **Condition:** Repository updates ONLY occur if the thermostat is set to 60°F (Aggressive Push).
- **Short-Cycle Protection:** If a session is < 5 minutes, the system performs the temperature handoff to protect comfort but skips the learning phase to protect data.
- **Physical Clamps:** Data Armor v2 enforces an absolute range of 10.0–45.0 min/deg for all learned values.
---

## 8. System Monitoring (Admin Baseline)
The `dashboard-admin` serves as the authoritative "Single Pane of Glass" for system health and logic integrity.

### **Health Summary Logic (v2.0)**
- **48h Rolling Window:** Log error/warning counts only reflect issues from the last 48 hours to ensure recent relevance.
- **Noise Filtering:** Known frontend-only errors (e.g., `frontend.js.modern` incompatibilities) are excluded from the health counts to prevent "noise" from masking backend logic failures.

### **Baseline Sections**
- **System Health:** Tracks `sensor.system_health_summary`, HA Uptime, and real-time log Error/Warning counts.
- **Climate Control:** Aggregates MBR smoothed vs. raw data, pre-cooling schedule attributes, and the Bin Performance repository.
- **Engine Heartbeat:** Monitors the `last_triggered` status of all core AI and maintenance automations.
- **Hardware & Vitals:** High-signal tracking of security hardware (Shuttle Bay, Alarm).

### **Maintenance Workflow**
Critical infrastructure monitoring is driven by the `critical` label. Any entity tagged as `critical` that enters an `unavailable`, `unknown`, or `off` state will immediately trigger a "Critical Issue" status in the Health Summary.
