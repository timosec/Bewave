# BeWave custom integration

This custom integration models each configured BeWave zone as up to two Home Assistant entities:

- a **Button** entity that sends the configured trigger command to BeWave
- a **Binary Sensor** entity that reflects the latest feedback status from BeWave

## Configuration

For each zone, configure:

- **Name**: friendly zone name
- **HTTP command to BeWave**: exact trigger text to send when the button is pressed
- **HTTP output on request**: feedback text that means the zone is ON
- **HTTP output off request**: feedback text that means the zone is OFF
- **Listen port**: TCP port Home Assistant listens on for BeWave feedback

The integration still uses raw TCP under the hood, matching the original Homebridge plugin behavior:

- outgoing command to `<host>:5000`
- CRLF line endings
- short-lived TCP connection per trigger
- push feedback from BeWave back into Home Assistant

## Installation

1. Copy `custom_components/bewave` into your Home Assistant config folder.
2. Restart Home Assistant.
3. Add the BeWave integration via **Settings > Devices & Services**.
4. Configure one or more zones.

## Notes

- If the feedback fields are left empty, only the trigger button will be created.
- Existing old switch entities from earlier builds may remain in the entity registry and can be removed manually.
