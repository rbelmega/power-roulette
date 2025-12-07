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
- Pair it with a Lovelace chart (e.g., `apexcharts-card`) to visualize blackout windows. Example (uses only built-in series types):
  ```yaml
  type: custom:apexcharts-card
  graph_span: 48h
  header:
    title: Power Roulette (today/tomorrow)
  series:
    - entity: sensor.power_roulette_outage_schedule
      name: Outage
      type: area
      color: '#e53935'
      extend_to: false
      stroke_width: 0
      data_generator: |
        const sched = entity.attributes.schedule || [];
        const points = [];
        sched.forEach(day => {
          const date = day.event_date?.split('.').reverse().join('-'); // dd.MM.yyyy -> yyyy-MM-dd
          (day.intervals || []).forEach(slot => {
            const start = new Date(`${date}T${slot.from}:00`);
            const end = new Date(`${date}T${slot.to}:00`);
            points.push([start, 1]);
            points.push([end, 1]);
            points.push([end, 0]);
          });
        });
        points.sort((a, b) => new Date(a[0]) - new Date(b[0]));
        return points;
  apex_config:
    chart:
      type: area
    stroke:
      curve: stepline
    yaxis:
      min: 0
      max: 1
      labels:
        show: false
  ```

Click to prefill a Lovelace card with this YAML:
[![Add outage chart](https://my.home-assistant.io/badges/redirect.svg)](https://my.home-assistant.io/redirect/lovelace_yamleditor/?yaml=type%3A%20custom%3Aapexcharts-card%0Agraph_span%3A%2048h%0Aheader%3A%0A%20%20title%3A%20Power%20Roulette%20%28today%2Ftomorrow%29%0Aseries%3A%0A%20%20-%20entity%3A%20sensor.power_roulette_outage_schedule%0A%20%20%20%20name%3A%20Outage%0A%20%20%20%20type%3A%20area%0A%20%20%20%20color%3A%20%27%23e53935%27%0A%20%20%20%20extend_to%3A%20false%0A%20%20%20%20stroke_width%3A%200%0A%20%20%20%20data_generator%3A%20%7C%0A%20%20%20%20%20%20const%20sched%20%3D%20entity.attributes.schedule%20%7C%7C%20%5B%5D%3B%0A%20%20%20%20%20%20const%20points%20%3D%20%5B%5D%3B%0A%20%20%20%20%20%20sched.forEach%28day%20%3D%3E%20%7B%0A%20%20%20%20%20%20%20%20const%20date%20%3D%20day.event_date%3F.split%28%27.%27%29.reverse%28%29.join%28%27-%27%29%3B%0A%20%20%20%20%20%20%20%20%28day.intervals%20%7C%7C%20%5B%5D%29.forEach%28slot%20%3D%3E%20%7B%0A%20%20%20%20%20%20%20%20%20%20const%20start%20%3D%20new%20Date%28%60%24%7Bdate%7DT%24%7Bslot.from%7D%3A00%60%29%3B%0A%20%20%20%20%20%20%20%20%20%20const%20end%20%3D%20new%20Date%28%60%24%7Bdate%7DT%24%7Bslot.to%7D%3A00%60%29%3B%0A%20%20%20%20%20%20%20%20%20%20points.push%28%5Bstart%2C%201%5D%29%3B%0A%20%20%20%20%20%20%20%20%20%20points.push%28%5Bend%2C%201%5D%29%3B%0A%20%20%20%20%20%20%20%20%20%20points.push%28%5Bend%2C%200%5D%29%3B%0A%20%20%20%20%20%20%20%20%7D%29%3B%0A%20%20%20%20%20%20%7D%29%3B%0A%20%20%20%20%20%20points.sort%28%28a%2C%20b%29%20%3D%3E%20new%20Date%28a%5B0%5D%29%20-%20new%20Date%28b%5B0%5D%29%29%3B%0A%20%20%20%20%20%20return%20points%3B%0Aapex_config%3A%0A%20%20chart%3A%0A%20%20%20%20type%3A%20area%0A%20%20stroke%3A%0A%20%20%20%20curve%3A%20stepline%0A%20%20yaxis%3A%0A%20%20%20%20min%3A%200%0A%20%20%20%20max%3A%201%0A%20%20%20%20labels%3A%0A%20%20%20%20%20%20show%3A%20false)
