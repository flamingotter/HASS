# Home Assistant Lab Context
- **Structure:** Modular Package-based config in `integrations/` and `entities/`.
- **Environment:** Docker container on Debian host. Python 3.14.2.
- **BigQuery:** Analytics environment in `bq_venv/`. Credentials at `/config/bigquery_credentials.json`.

## 1. Documentation Map
- **[ARCHITECTURE.md](ARCHITECTURE.md):** Core logic engines, state machines, and cross-automation dependencies.
- **[CLIMATE_SUMMARY.md](CLIMATE_SUMMARY.md):** Historical evolution and detailed technical breakdown of the MBR Sleep Comfort Engine.
- **[ROADMAP.md](ROADMAP.md):** Active goals, pending fixes, and planned feature expansions.

## 2. Primary Rules & Standards
- **Modern Syntax:** Always use `template:` integration, `action:` instead of `service:`, and `data:` for all templated values.
- **Persistence:** Avoid `initial:` values in YAML for entities that rely on `restore_state` (e.g., input_text/numbers).
- **Cleanup:** Ignore "missing" entities in `group.grow_shelf` or `group.echos`. Holiday entities (e.g., `light.led_tree`) are seasonal.
- **Integrity:** Do NOT remove or modify logic marked `enabled: false`.

## 3. Active Architectural Patterns
- **Authority -> Reactor:** For state-heavy logic (Presence, Alarm), centralize decisions in an "Authority" automation (e.g., `Person: Status Synchronizer`). Reactor automations should watch state changes and remain simple.
- **Fail-Safe AI:** Strategic LLM tasks (`ai_task`) must use `continue_on_error: true` and provide robust fallback defaults (`| float(target)`) to prevent system stalls.
- **Data Armor:** Always implement physical swing caps (e.g., ±5 min) when updating repositories from live data to protect against sensor jitter.
- **Mode-Based Lighting:** Lighting is heavily dictated by mode booleans (`onair`, `cleaning`, `reading_mode`). Always check for active overrides before changing lights.

## 4. Global Constants & Identity
- **Users:**
    - **Josh:** `device_id: d818035824cf47ea` | `notify.mobile_app_josh_mobile`
    - **MJ:** `device_id: 0aa560faf0e8784c` | `notify.mobile_app_mj_pixel_8_pro`
- **Pets (The Felines):**
    - **Battle Cat:** (he/him)
    - **Josie:** (she/her)
    - **Custard:** (she/her)
- **Notification Tags:**
    - `eco-finish`: Unified tag for all Eco Mode activation and timer interactions.
    - `pets-notify`: Daily feeding task management.
    - `trash-notify`: Weekly curb reminders.
    - `cleaning-warning`: Occupancy nag for Cleaning Mode.
    - `arm-guests`: Verification for arming with house guests present.

## 5. Current System State (As of May 6, 2026)
- **Presence Engine:** 
    - **Extended Away:** Triggered by 24h absence OR crossing a 500-mile radius.
    - **Homebound Reset:** Eco Mode releases only when BOTH Josh and MJ are within 50 miles.
- **Climate Engine (v7.2):** 
    - Hardened AI mode with logical Auditor and physical Swing Cap.
    - **Eco Mode Targets:** 66°F (Heat) / 74°F (Cool) for pet comfort.

## 6. Operational Focus
- **Primary Goal:** Transition Climate Engine to v7.x stable while maintaining physical safety.
- **Bit Rot:** Continually sync `automations.yaml` with current hardware realities.
