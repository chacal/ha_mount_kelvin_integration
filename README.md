# Home Assistant Mount Kelvin integration

This repository contains a custom component for [Home Assistant](https://www.home-assistant.io/) that 
adds support for `mount_kelvin` platform through which Home Assistant can be used to control
lights of a [Mount Kelvin](https://www.mountkelvin.com/) system.

This is still very much work in progress and only very rudimentary support for controlling individual
lights has been implemented for now (meaning there is no support for Mount Kelvin scenes, schedules, 
rooms, switches, etc.).

## Installation

1. Create `custom_components` directory into Home Assistant's home directory (by default `~/.homeassistant`)
1. Clone this repository in the created dir as `mount_kelvin` directory: 

    `git clone https://github.com/chacal/ha_mount_kelvin_integration.git mount_kelvin`

1. Add the following snippet to the Home Assistant's `configuration.yaml`
```
    light:
      - platform: mount_kelvin
      api_key: <mount-kelvin-api-key>
```
1. Restart Home Assistant

Once started the integration queries Mount Kelvin API for all light devices and adds them as light entities
to Home Assistant. Support for both dimmable and on/off lights has been implemented.
