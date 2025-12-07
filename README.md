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

### Optional: Graph your outages (timeline)
- The sensor `sensor.power_roulette_outage_schedule` exposes full interval data in attributes (`schedule`, `next_outage`, `next_restore`).
- Use `apexcharts-card` (HACS → Frontend) for a distributed range/timeline view. Example with defensive data handling (no spinners if data is missing):
  ```yaml
  type: custom:apexcharts-card
  header:
    title: Power Roulette — графік відключень
    show: true
  graph_span: 48h
  apex_config:
    chart:
      type: rangeBar
    plotOptions:
      bar:
        horizontal: true
        distributed: true
        rangeBarGroupRows: true
    dataLabels:
      enabled: true
      formatter: |
        function(val) {
          if (!val) return '';
          const [start, end] = val;
          const s = new Date(start).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
          const e = new Date(end).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
          return `${s}–${e}`;
        }
    xaxis:
      type: datetime
    yaxis:
      labels:
        show: true
  series:
    - entity: sensor.power_roulette_outage_schedule
      name: Відключення
      type: area
      color: '#ef4444'
      extend_to: false
      stroke_width: 0
      data_generator: |
        const sched = entity?.attributes?.schedule;
        if (!Array.isArray(sched)) return [];
        const bars = [];
        sched.forEach(day => {
          (day.intervals || []).forEach((slot, idx) => {
            if (!slot?.start_iso || !slot?.end_iso) return;
            const start = new Date(slot.start_iso);
            const end = new Date(slot.end_iso);
            if (isNaN(start) || isNaN(end)) return;
            bars.push({ x: `${day.event_date} #${idx+1}`, y: [start.getTime(), end.getTime()] });
          });
        });
        return bars;
  ```

Click to prefill a Lovelace card with this YAML:
[![Add outage timeline](https://my.home-assistant.io/badges/redirect.svg)](https://my.home-assistant.io/redirect/lovelace_yamleditor/?yaml=type%3A%20custom%3Aapexcharts-card%0Aheader%3A%0A%20%20title%3A%20Power%20Roulette%20%E2%80%94%20%D0%B3%D1%80%D0%B0%D1%84%D1%96%D0%BA%20%D0%B2%D1%96%D0%B4%D0%BA%D0%BB%D1%8E%D1%87%D0%B5%D0%BD%D1%8C%0A%20%20show%3A%20true%0Agraph_span%3A%2048h%0Aapex_config%3A%0A%20%20chart%3A%0A%20%20%20%20type%3A%20rangeBar%0A%20%20plotOptions%3A%0A%20%20%20%20bar%3A%0A%20%20%20%20%20%20horizontal%3A%20true%0A%20%20%20%20%20%20distributed%3A%20true%0A%20%20%20%20%20%20rangeBarGroupRows%3A%20true%0A%20%20dataLabels%3A%0A%20%20%20%20enabled%3A%20true%0A%20%20%20%20formatter%3A%20%7C%0A%20%20%20%20%20%20function%28val%29%20%7B%0A%20%20%20%20%20%20%20%20if%20%28%21val%29%20return%20%27%27%3B%0A%20%20%20%20%20%20%20%20const%20%5Bstart%2C%20end%5D%20%3D%20val%3B%0A%20%20%20%20%20%20%20%20const%20s%20%3D%20new%20Date%28start%29.toLocaleTimeString%28%5B%5D%2C%20%7Bhour%3A%272-digit%27%2C%20minute%3A%272-digit%27%7D%29%3B%0A%20%20%20%20%20%20%20%20const%20e%20%3D%20new%20Date%28end%29.toLocaleTimeString%28%5B%5D%2C%20%7Bhour%3A%272-digit%27%2C%20minute%3A%272-digit%27%7D%29%3B%0A%20%20%20%20%20%20%20%20return%20%60%24%7Bs%7D%E2%80%93%24%7Be%7D%60%3B%0A%20%20%20%20%20%20%7D%0A%20%20xaxis%3A%0A%20%20%20%20type%3A%20datetime%0A%20%20yaxis%3A%0A%20%20%20%20labels%3A%0A%20%20%20%20%20%20show%3A%20true%0Aseries%3A%0A%20%20-%20entity%3A%20sensor.power_roulette_outage_schedule%0A%20%20%20%20name%3A%20%D0%92%D1%96%D0%B4%D0%BA%D0%BB%D1%8E%D1%87%D0%B5%D0%BD%D0%BD%D1%8F%0A%20%20%20%20type%3A%20area%0A%20%20%20%20color%3A%20%27%23ef4444%27%0A%20%20%20%20extend_to%3A%20false%0A%20%20%20%20stroke_width%3A%200%0A%20%20%20%20data_generator%3A%20%7C%0A%20%20%20%20%20%20const%20sched%20%3D%20entity%3F.attributes%3F.schedule%3B%0A%20%20%20%20%20%20if%20%28%21Array.isArray%28sched%29%29%20return%20%5B%5D%3B%0A%20%20%20%20%20%20const%20bars%20%3D%20%5B%5D%3B%0A%20%20%20%20%20%20sched.forEach%28day%20%3D%3E%20%7B%0A%20%20%20%20%20%20%20%20const%20date%20%3D%20day%3F.event_date%3F.split%28%27.%27%29%3F.reverse%28%29%3F.join%28%27-%27%29%3B%0A%20%20%20%20%20%20%20%20if%20%28%21date%29%20return%3B%0A%20%20%20%20%20%20%20%20%28day.intervals%20%7C%7C%20%5B%5D%29.forEach%28%28slot%2C%20idx%29%20%3D%3E%20%7B%0A%20%20%20%20%20%20%20%20%20%20if%20%28%21slot%3F.from%20%7C%7C%20%21slot%3F.to%29%20return%3B%0A%20%20%20%20%20%20%20%20%20%20const%20start%20%3D%20new%20Date%28%60%24%7Bdate%7DT%24%7Bslot.from%7D%3A00%60%29%3B%0A%20%20%20%20%20%20%20%20%20%20const%20end%20%3D%20new%20Date%28%60%24%7Bdate%7DT%24%7Bslot.to%7D%3A00%60%29%3B%0A%20%20%20%20%20%20%20%20%20%20if%20%28isNaN%28start%29%20%7C%7C%20isNaN%28end%29%29%20return%3B%0A%20%20%20%20%20%20%20%20%20%20bars.push%28%7Bx%3A%20%60%24%7Bday.event_date%7D%20%23%24%7Bidx%2B1%7D%60%2C%20y%3A%20%5Bstart.getTime%28%29%2C%20end.getTime%28%29%5D%7D%29%3B%0A%20%20%20%20%20%20%20%20%7D%29%3B%0A%20%20%20%20%20%20%7D%29%3B%0A%20%20%20%20%20%20return%20bars%3B%0A)
