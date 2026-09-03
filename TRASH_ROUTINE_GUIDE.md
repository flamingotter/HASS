# 🗑️ The Ultimate "Trash & Recycling" Accountability Engine
> **Household Partner Routine for Home Assistant**
> 
> *A collaborative trash management system featuring lock screen action buttons, partner hand-offs, 24-hour holiday shift bumps, NFC tag scanning, anti-dismissal nag protection, and a bedtime failsafe.*

---

## ✨ Features
1. **Dual-Phone Broadcast:** Alerts both partners at 5:00 PM the evening before pickup.
2. **One-Tap Actions:** Lock screen buttons for **Done**, **Ask Other**, and **Delay 24hr**.
3. **Holiday Shift Bump ("Delay 24hr"):** If a Monday holiday (like Labor Day or Memorial Day) pushes trash pickup from Wednesday to Thursday, simply tap **Delay 24hr**. It silences bedtime reminders for Tuesday night and automatically reminds you again Wednesday at 5:00 PM!
4. **Multi-Device Synchronization:** As soon as one person takes out the trash and taps **Done**, the notification automatically vanishes from *both* phones, and notifies the partner (*"Josh Completed"*).
5. **"Pass the Buck" Delegation:** Tapping **Ask Other** immediately routes a high-priority prompt (*"YOU'RE MY ONLY HOPE"*) to your partner.
6. **NFC Can-Scanner (Optional):** Stick a cheap weatherproof NFC tag on the trash can lid. Tapping your phone against the can automatically marks it done!
7. **Anti-Ignore AI Nag:** Swiping away the notification without tapping Done triggers an AI-generated witty nag (*"The trash isn't going to take itself out"*).
8. **Bedtime Whisper Failsafe:** If you both head to bed and forgot, your bedroom smart speaker alerts you before you fall asleep.

---

## 📋 Step 1: Create the Helpers in the UI
Go to **Settings $\rightarrow$ Devices & Services $\rightarrow$ Helpers** and create these three items:

### 1. Dropdown Helper: Pickup Day
* **Type:** Dropdown (`input_select`)
* **Name:** `Trash Pickup Day`
* **Entity ID:** `input_select.trash_pickup_day`
* **Options:** Add all 7 days: `Monday`, `Tuesday`, `Wednesday`, `Thursday`, `Friday`, `Saturday`, `Sunday`
* *(Set this to the day of your reminder — e.g., if pickup is Wednesday morning, set this to `Tuesday`).*

### 2. Toggle Helper: Reminder Status
* **Type:** Toggle (`input_boolean`)
* **Name:** `Trash Reminder`
* **Entity ID:** `input_boolean.trash_reminder`

### 3. Template Binary Sensor: Trash Day Active
* **Type:** Template $\rightarrow$ **Template a binary sensor**
* **Name:** `Trash Day`
* **Entity ID:** `binary_sensor.trash_day`
* **State template:**
  ```jinja
  {% set _ = states('sensor.date') %}
  {{ now().strftime('%A') == states('input_select.trash_pickup_day') }}
  ```
  *(Note: Requires the native Home Assistant **Time & Date** integration enabled so it evaluates midnight day rollovers).*

---

## 🏷️ Step 2: The NFC Tag (Optional)
1. In the Home Assistant Companion App on your phone, go to **Settings $\rightarrow$ Tags**.
2. Tap **Add Tag**, hold an NFC sticker against the back of your phone, and name the Tag ID:
   ```text
   trash_done
   ```
3. Stick the tag under the trash can or recycling bin lid.

---

## ⚙️ Step 3: The Standalone Automation YAML

Copy this automation into your `automations.yaml` (or paste into **Settings $\rightarrow$ Automations $\rightarrow$ Create Automation $\rightarrow$ Edit in YAML**).

> **Customization Note:** Replace `partner_1_notify` and `partner_2_notify` with your companion app notify services (e.g. `notify.mobile_app_josh_mobile`), and set your actual device IDs in the `variables:` block at the bottom.

```yaml
alias: 'Notify: Trash Day'
description: 'Collaborative household trash accountability engine'
triggers:
  - trigger: time
    at: '17:00:00'
    id: trash_time
  - trigger: event
    event_type: mobile_app_notification_action
    event_data:
      action: trash_done
    id: trash_done
  - trigger: event
    event_type: mobile_app_notification_action
    event_data:
      action: trash_passon
    id: trash_passon
  - trigger: event
    event_type: mobile_app_notification_action
    event_data:
      action: trash_delay
    id: trash_delay
  - trigger: event
    event_type: mobile_app_notification_cleared
    event_data:
      tag: trash-notify
    id: trash_cleared
  - trigger: tag
    tag_id: trash_done
    id: trash_tag_scanned

actions:
  - choose:
      # --- 1. DAILY 5:00 PM REMINDER ---
      - conditions:
          - condition: state
            entity_id: binary_sensor.trash_day
            state: 'on'
          - condition: trigger
            id: trash_time
        sequence:
          - action: input_boolean.turn_on
            target:
              entity_id: input_boolean.trash_reminder
          - action: notify.all_devices
            data:
              title: "Trash and Recycling"
              message: "Put to the Curb"
              data:
                tag: trash-notify
                actions:
                  - action: trash_done
                    title: "Done"
                  - action: trash_passon
                    title: "Ask Other"
                  - action: trash_delay
                    title: "Delay 24hr"

      # --- 2. TRASH COMPLETED (BUTTON OR NFC SCAN) ---
      - conditions:
          - or:
              - condition: trigger
                id: trash_done
              - condition: trigger
                id: trash_tag_scanned
        sequence:
          - action: input_boolean.turn_off
            target:
              entity_id: input_boolean.trash_reminder
          # Clear notification on both phones immediately
          - action: notify.all_devices
            data:
              message: clear_notification
              data:
                tag: trash-notify
          # Identify who completed it and notify the other partner
          - variables:
              scanned_device: '{{ trigger.device_id | default(trigger.event.data.device_id) | default("unknown") }}'
              scanned_name: '{{ partner_1_name if scanned_device == partner_1_device_id else partner_2_name }}'
              target_notify: '{{ partner_2_notify if scanned_name == partner_1_name else partner_1_notify }}'
          - action: '{{ target_notify }}'
            data:
              title: "Trash and Recycling"
              message: "{{ scanned_name }} Completed"
              data:
                tag: trash-status

      # --- 3. ASK OTHER ("PASS THE BUCK") ---
      - conditions:
          - condition: trigger
            id: trash_passon
        sequence:
          - variables:
              scanned_device: '{{ trigger.device_id | default(trigger.event.data.device_id) | default("unknown") }}'
              scanned_name: '{{ partner_1_name if scanned_device == partner_1_device_id else partner_2_name }}'
              target_notify: '{{ partner_2_notify if scanned_name == partner_1_name else partner_1_notify }}'
          - action: '{{ target_notify }}'
            data:
              title: "Trash and Recycling"
              message: "YOU'RE MY ONLY HOPE."
              data:
                tag: trash-notify
                actions:
                  - action: trash_done
                    title: "Done"

      # --- 4. ANTI-IGNORE NAG (IF SWIPED AWAY WITHOUT COMPLETING) ---
      - conditions:
          - condition: trigger
            id: trash_cleared
          - condition: state
            entity_id: input_boolean.trash_reminder
            state: 'on'
        sequence:
          - delay:
              seconds: 2
          - action: notify.all_devices
            data:
              title: "Trash and Recycling"
              message: "The trash isn't going to take itself out."
              data:
                tag: trash-notify
                actions:
                  - action: trash_done
                    title: "Done"
                  - action: trash_passon
                    title: "Ask Other"
                  - action: trash_delay
                    title: "Delay 24hr"

      # --- 5. DELAY 24 HOURS (HOLIDAY SHIFT BUMP) ---
      - conditions:
          - condition: trigger
            id: trash_delay
        sequence:
          # Turn off reminder so bedtime check doesn't yell at you tonight
          - action: input_boolean.turn_off
            target:
              entity_id: input_boolean.trash_reminder
          - action: notify.all_devices
            data:
              message: clear_notification
              data:
                tag: trash-notify
          # Wait 24 hours to re-prompt tomorrow evening
          - delay:
              hours: 24
          - action: input_boolean.turn_on
            target:
              entity_id: input_boolean.trash_reminder
          - action: notify.all_devices
            data:
              title: "Trash and Recycling"
              message: "Put to the Curb"
              data:
                tag: trash-notify
                actions:
                  - action: trash_done
                    title: "Done"
                  - action: trash_passon
                    title: "Ask Other"
                  - action: trash_delay
                    title: "Delay 24hr"

variables:
  partner_1_name: "Josh"
  partner_1_device_id: "d818035824cf47ea"
  partner_1_notify: "notify.mobile_app_josh_mobile"

  partner_2_name: "MJ"
  partner_2_device_id: "0aa560faf0e8784c"
  partner_2_notify: "notify.mobile_app_mj_pixel_8_pro"

mode: parallel
max: 10
```

---

## 🛏️ Step 4: Bedtime Routine Integration (Bonus)

Add this condition check into your existing **Goodnight / Bedtime Routine**:

```yaml
- if:
    - condition: state
      entity_id: input_boolean.trash_reminder
      state: 'on'
  then:
    - action: tts.speak
      target:
        entity_id: media_player.bedroom_speaker
      data:
        message: "It looks like you may have forgotten to take the trash to the street."
```
