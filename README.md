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
4. To change city/queue later: **Settings → Devices & Services → Power Roulette → Configure**.

After setup, the integration creates:
- `sensor.power_roulette_next_outage` — next planned outage (timestamp).
- `sensor.power_roulette_next_power_restore` — when power should return (timestamp, lightning icon).
- `sensor.power_roulette_outage_schedule` — status plus full schedule attributes for charts.

Data refreshes automatically every 5 minutes via the remote schedule service. This skeleton uses a placeholder API client; swap in a real endpoint to power your production integration.

### Regions/providers
- Івано-Франківська область — джерело be-svitlo.oe.if.ua (працює зараз). Черги однакові для міст області.

### Optional: Graph your outages (timeline)
- The sensor `sensor.power_roulette_outage_schedule` exposes full interval data in attributes (`schedule`, `next_outage`, `next_restore`).
- ApexCharts (stepped areas “no power” / “power” по 15 хв кроку, на перший день із розкладу):
  ```yaml
  type: custom:apexcharts-card
  header:
    show: true
    title: Графік відключень
  now:
    show: true
  graph_span: 1d
  span:
    start: day
  all_series_config:
    curve: stepline
    stroke_width: 2
    show:
      legend_value: false
  yaxis:
    - min: 0
      max: 1
      decimals: 0
      show: false
  series:
    - entity: sensor.power_roulette_outage_schedule
      name: Немає світла
      type: area
      color: "#ff3b30"
      data_generator: |
        const sched = entity.attributes.schedule || [];
        if (!sched.length) return [];
        const day = sched[0];
        const dateStr = day.event_date;
        if (!dateStr) return [];
        const [dd, mm, yy] = dateStr.split('.').map(Number);
        if (!yy || !mm || !dd) return [];
        const intervals = (day.intervals || []).map((i) => {
          if (!i.from || !i.to) return null;
          const [fh, fm] = i.from.split(':').map(Number);
          const [th, tm] = i.to.split(':').map(Number);
          if (isNaN(fh) || isNaN(fm) || isNaN(th) || isNaN(tm)) return null;
          return {
            start: new Date(yy, mm - 1, dd, fh, fm).getTime(),
            end:   new Date(yy, mm - 1, dd, th, tm).getTime(),
          };
        }).filter(Boolean);
        if (!intervals.length) return [];
        const STEP = 15 * 60 * 1000;
        const dayStart = new Date(yy, mm - 1, dd, 0, 0).getTime();
        const dayEnd   = new Date(yy, mm - 1, dd, 23, 59).getTime();
        const points = [];
        for (let t = dayStart; t <= dayEnd; t += STEP) {
          const inOutage = intervals.some(int => t >= int.start && t < int.end);
          points.push([t, inOutage ? 1 : null]);
        }
        return points;
    - entity: sensor.power_roulette_outage_schedule
      name: Є світло
      type: area
      color: "#ffcc00"
      data_generator: |
        const sched = entity.attributes.schedule || [];
        if (!sched.length) return [];
        const day = sched[0];
        const dateStr = day.event_date;
        if (!dateStr) return [];
        const [dd, mm, yy] = dateStr.split('.').map(Number);
        if (!yy || !mm || !dd) return [];
        const intervals = (day.intervals || []).map((i) => {
          if (!i.from || !i.to) return null;
          const [fh, fm] = i.from.split(':').map(Number);
          const [th, tm] = i.to.split(':').map(Number);
          if (isNaN(fh) || isNaN(fm) || isNaN(th) || isNaN(tm)) return null;
          return {
            start: new Date(yy, mm - 1, dd, fh, fm).getTime(),
            end:   new Date(yy, mm - 1, dd, th, tm).getTime(),
          };
        }).filter(Boolean);
        if (!intervals.length) return [];
        const STEP = 15 * 60 * 1000;
        const dayStart = new Date(yy, mm - 1, dd, 0, 0).getTime();
        const dayEnd   = new Date(yy, mm - 1, dd, 23, 59).getTime();
        const points = [];
        for (let t = dayStart; t <= dayEnd; t += STEP) {
          const inOutage = intervals.some(int => t >= int.start && t < int.end);
          points.push([t, inOutage ? null : 1]);
        }
        return points;
  apex_config:
    xaxis:
      type: datetime
    tooltip:
      shared: true
      intersect: false
      x:
        format: dd MMM HH:mm
      y:
        formatter: |
          EVAL:function(val, opts) {
            if (opts.seriesIndex === 0) return 'Немає світла';
            if (opts.seriesIndex === 1) return 'Є світло';
            return val;
          }

### Brand images not showing?
Home Assistant should pick up `custom_components/power_roulette/logo.png` and `icon.png` (mirrored under `custom_components/power_roulette/brand/` and `branding/`). If you still see the default puzzle piece, clear browser cache and restart HA after updating the integration.
