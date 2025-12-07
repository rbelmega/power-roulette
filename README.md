# Power Roulette

Power Roulette is a Home Assistant custom integration that tracks Ukraine's rolling blackout ("power roulette") schedule. Enter your city and queue to see when the next planned outage is expected.

[![Open config flow in Home Assistant](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=power_roulette)

## Installation (HACS)
1. In HACS, choose **Integrations** → **Custom repositories**.
2. Add this repository URL and select category **Integration**: https://github.com/rbelmega/power-roulette
3. Open HACS → Integrations, search for **Power Roulette**, and install.
4. Restart Home Assistant.

> Note: HACS custom integrations cannot be installed directly via a single button. Use the steps above to add this repo to HACS, then use the badge to launch the config flow once installed.
> If you see “This integration does not support configuration via the UI”, it means Home Assistant does not see the custom integration yet. Verify it is installed in HACS, restart Home Assistant, then try again.

## Configuration
1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **Power Roulette**.
3. Enter your city and queue number/label, then submit.

After setup, the integration creates a sensor showing the next planned outage time. Data refreshes automatically every 5 minutes via the remote schedule service. This skeleton uses a placeholder API client; swap in a real endpoint to power your production integration.

### Optional: Graph your outages
- The sensor `sensor.power_roulette_outage_schedule` exposes full interval data in attributes (`schedule`, `next_outage`, `next_restore`).
- Pair it with a Lovelace chart (e.g., `apexcharts-card`) to visualize blackout windows. Example:
  ```yaml
  type: custom:apexcharts-card
  stacked: true
  header:
    title: Power Roulette (today/tomorrow)
  series:
    - entity: sensor.power_roulette_outage_schedule
      name: Outage
      type: range
      data_generator: |
        const sched = entity.attributes.schedule || [];
        return sched.flatMap(day => (day.intervals || []).map(slot => {
          // Merge date + time into ISO strings
          const date = day.event_date?.split('.').reverse().join('-');
          return [new Date(`${date}T${slot.from}:00`), new Date(`${date}T${slot.to}:00`)];
        }));
  ```
