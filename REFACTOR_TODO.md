# Refactor TODO: Optimization & Maintenance

## 🚨 Broken Entities (Watchman & Research)
Entities identified as missing or renamed that need updating in the config.

| Entity ID | Location | Suggestion |
| :--- | :--- | :--- |
| `select.wled_cloud_preset` | `automations.yaml:1354` | Check if renamed to `select.wled_cloud_main_preset` or use `select.select_option` on correct WLED entity. |
| `notify.porch_history` | `automations.yaml:3894` | Missing from `integrations/notify.yaml`. Add CSV/File notification service. |
| `camera.parlor_inside` | `scripts.yaml:251` | Rename to `camera.dining_room_inside_medium_resolution_channel`. |
| `camera.kitchen_inside` | `scripts.yaml:246, 212, etc` | Verify current Frigate/UI camera name for Kitchen. |
| `light.wled_bed` | `scenes.yaml:96, 310` | Check if entity was renamed or is currently offline. |
| `switch.office_strip_socket_06` | `automations.yaml:427, 445` | Identify new entity ID for the 3D printer power strip. |

## 🧹 Stale Automations (No trigger > 30 days)
Prime candidates for review or removal (as of 2026-03-29).

| Name | Entity ID | Last Triggered | Recommendation |
| :--- | :--- | :--- | :--- |
| Garage Door 01 | `automation.garage_door` | 2025-06-04 | Remove or Disable |
| 3D Print Progress Notify | `automation.3d_print_progress_notify` | 2024-09-16 | Review relevance; printer hardware might have changed. |
| Notify House Guests | `automation.notify_house_guests` | 2025-04-22 | Remove |
| webhook test | `automation.webhook_test` | 2025-03-22 | Delete |
| Generator Test | `automation.generator_test` | 2025-05-06 | Verify if still needed for maintenance. |
| Notify Water Filter | `automation.notify_water_filter` | 2025-07-10 | Review (AI logic in `automations.yaml` might have replaced this). |

## 🏗️ Architectural Improvements
Structural changes to improve maintainability and follow `GEMINI.md` rules.

- **Standardize Motion Naming:** Rename all motion binary sensors to follow `binary_sensor.motion_indoors_[room]` to support dynamic templates.
- **Consolidate Motion Lighting:** Replace room-specific motion automations with a single template-based automation or a specialized Blueprint.
- **Parameterized AI Scripts:** Consolidate `camera_parlor_snapshot_ai_notification` and `camera_kitchen_snapshot_ai_notification` into one script using fields for camera and room name.
- **Area Cleanup:** Move `media_player.living_room` from MBR area to Living Room area.
- **Modern Templates:** Continue moving legacy `platform: template` sensors to the modular structure in `entities/templates/`.
