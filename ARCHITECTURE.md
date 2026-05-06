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

## 5. Vision AI Pattern
Used for parlor/kitchen motion and cat locating.
- **Flow:** `camera.snapshot` (3 frames) -> `ai_task` (Image Analysis) -> `notify` (with latest frame).
- **Logic:** Stops execution if the AI returns "No Obvious Motion Detected" to prevent notification fatigue.
