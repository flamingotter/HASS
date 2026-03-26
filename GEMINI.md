# Home Assistant Lab Context
- **Structure:** Modular Package-based config in `integrations/` and `entities/`.
- **Environment:** Docker container on Debian host.
- **Rules:** - Always use modern `template:` integration, never legacy `platform: template`.
  - Prefer YAML edits over UI helpers where possible.
  - We have moved twice recently; ignore "missing" entities in `group.grow_shelf` or `group.echos`.
- **Primary Goal:** Clean up "bit rot" and sync `automations.yaml` with current hardware.
