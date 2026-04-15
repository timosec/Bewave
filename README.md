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
- push feedback from BeWave back into Home Assistant

## Installation

1. Copy `custom_components/bewave` into your Home Assistant config folder.
2. Restart Home Assistant.
3. Add the BeWave integration via **Settings > Devices & Services**.
4. Configure one or more zones.

## Notes

- If the feedback fields are left empty, only the trigger button will be created.
- Existing old switch entities from earlier builds may remain in the entity registry and can be removed manually.

## Settup

<img width="730" height="383" alt="image" src="https://github.com/user-attachments/assets/42205247-fa12-4075-97ed-ee1e62825e04" />

Enter the IP address of the Hub.

<img width="733" height="385" alt="image" src="https://github.com/user-attachments/assets/d00784ef-0e9c-478b-82b7-75d6c91cbc77" />

First, configure the first zone:

<img width="729" height="985" alt="image" src="https://github.com/user-attachments/assets/5caddc44-c569-4e26-83be-69fce4cffa56" />

1: Zone name</br>
2: Command to send to the Bewave hub</br>
3: Status (ON) – used to receive the ON state from the Bewave hub</br>
5: Status (OFF) – used to receive the OFF state from the Bewave hub


<img width="730" height="449" alt="image" src="https://github.com/user-attachments/assets/1e29a376-2fb0-4ee3-9797-db2ac4e5dcb0" />

1: To add an new zone </br>
2: to save the zone

## Settings in the BeWave Hub: 

<img width="600" height="1304" alt="image" src="https://github.com/user-attachments/assets/dd5bbaac-d990-49a1-83c0-d8450676ff2d" />

