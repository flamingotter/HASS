# Home Assistant Lab Context
- **Structure:** Modular Package-based config in `integrations/` and `entities/`.
- **Environment:** Docker container on Debian host. Home Assistant 2026.5.0. Python 3.14.2.
- **Paths:** Internal container path is `/config/`. External host path is `/data/brick1/docker_data/appdata/hub/hass/`.
- **BigQuery:** Analytics environment in `bq_venv/` (rebuilt inside container May 6, 2026). Credentials at `/config/bigquery_credentials.json`. Dedicated remote MCP credentials configured at `/opt/docker/secrets/mcp-bq-key.json`.

## 1. Documentation Map
- **[ARCHITECTURE.md](ARCHITECTURE.md):** Core logic engines, state machines, and cross-automation dependencies.
- **[CLIMATE_SUMMARY.md](CLIMATE_SUMMARY.md):** Historical evolution and detailed technical breakdown of the MBR Sleep Comfort Engine.
- **[ROADMAP.md](ROADMAP.md):** Active projects, pending infrastructure fixes, and planned feature expansions.

## 2. Primary Rules & Standards
- **Modern Syntax:** Always use `template:` integration, `action:` instead of `service:`, and `data:` for all templated values.
- **Persistence:** Avoid `initial:` values in YAML for entities that rely on `restore_state` (e.g., input_text/numbers).
- **Cleanup:** Ignore "missing" entities in `group.grow_shelf` or `group.echos`. Holiday entities (e.g., `light.led_tree`) are seasonal.
- **Integrity:** Do NOT remove or modify logic marked `enabled: false`.
- **Repository Management:** PERFORMANCE REPOS MUST use the "Single-Pass Clean-Sweep" pattern (v7.8.3+). Never pass dictionary variables between blocks; Home Assistant will re-parse and corrupt types. Perform Load, Normalize, Lookup, and Merge in a single atomic Jinja block.

## 3. Active Architectural Patterns
- **Authority -> Reactor:** For state-heavy logic (Presence, Alarm), centralize decisions in an "Authority" automation (e.g., `Person: Status Synchronizer`). Reactor automations should watch state changes and remain simple.
- **Fail-Safe AI:** Strategic LLM tasks (`ai_task`) must use `continue_on_error: true` and provide robust fallback defaults (`| float(target)`) to prevent system stalls.
- **Data Armor:** Always implement physical swing caps (e.g., ±5 min) and a 5-minute minimum duration gate for all climate learning sessions.
- **Whitespace Hardening:** Aggressively use `>-` and `{%- ... -%}` in all multi-line Jinja templates. Hidden newlines (`\n`) in variables cause string lookup failures and JSON duplication.

## 4. Global Constants & Identity
- **Users:**
    - **Josh:** `device_id: d818035824cf47ea` | `notify.mobile_app_josh_mobile`
    - **MJ:** `device_id: 0aa560faf0e8784c` | `notify.mobile_app_mj_pixel_8_pro`
- **Pets (The Felines):**
    - **Battle Cat:** (he/him)
    - **Josie:** (she/her)
    - **Custard:** (she/her)

## 5. Maintenance & Diagnostics
- **Docker API:** Kickoff containers via `shell_command.kickoff_bq_exporter`. Do NOT use `monitor_docker`.
- **Log Review:** Use `grep "PHASE_"` for Climate diagnostics or `grep "SIM_DATA"` for simulation results in `home-assistant.log`.
- **Simulation First:** ALL major logic changes (Climate, Presence) MUST be verified in `integrations/sim_lab.yaml` using the stress test script before production deployment.

## 6. Current System State (As of June 27, 2026)
- **Climate Engine (v7.8.6):** Logic Certified stable. Uses sorted string-keyed JSON repository with Overrides/Attic sensors integrated June 2026.
- **Vision Engine (v1.5):** Resilient recording with 2s flush delay to survive DTS stream drift.
- **BigQuery Remote MCP (v1.0):** Active and verified stable. Utilizes service account `mcp-bigquery-reader` for direct AI analytics.
- **Containers (HA & Z-Wave):** Core `homeassistant` and `zwave_js` container images successfully updated to their latest versions for performance and Z-Wave driver stability.
- **Alexa Media Player Custom Integration:** Downgraded to previous stable release to bypass Amazon's expired cookie/session authentication loop.
- **Security & Alarm State:** Staged aggregate watcher `binary_sensor.door_locks` checking the native `lock.door_locks` helper group, and optimized sirens automations to prevent triggering during `armed_night` status.
- **Startup:** Log sensor and core settings hardened; zero-warning boot.
