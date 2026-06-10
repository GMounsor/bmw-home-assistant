# BMW Home Assistant

A custom Home Assistant integration for BMW vehicles using the official [BMW CarData API](https://bmw-cardata.bmwgroup.com/customer/public/api-documentation).

Designed for **petrol/diesel (ICE) BMW vehicles** in the UK/EU. All distances and speeds are displayed in **miles**. Polls the BMW REST API every 30 minutes (within the free 50 calls/day limit).

**v1.0.2** — Adds display precision, diagnostic entity categories, CBS service item parsing, per-VIN partial failure resilience, and a Home Assistant repairs notification on auth failure.

---

## What You Get

### Sensors

| Entity | Description |
|---|---|
| Mileage | Odometer (miles) |
| Fuel Level | Fuel % |
| Remaining Fuel | Estimated range from fuel (miles) |
| Remaining Range | Navigation system range estimate (miles) |
| Last Remaining Range | Most recent range before ignition off (miles) |
| Engine Coolant Temp | Engine ECT in °C |
| 12V Battery Voltage | Electrical system voltage (V) |
| 12V Battery SOC | Battery state of charge (%) |
| Tyre Pressure FL/FR/RL/RR | Current pressure (bar) |
| Tyre Pressure Target FL/FR/RL/RR | Manufacturer target pressure (bar) |
| Tyre Temperature FL/FR/RL/RR | Tyre surface temperature (°C) |
| Tyre Diagnosis | Overall tyre health status |
| Average Speed | Trip average speed (mph) |
| Next Service Distance | Miles until next service |
| Service Due Date | Date of next service |
| Condition Based Services | Count of pending CBS items (0 = all clear); individual service items in attributes |
| Check Control Messages | Active warning messages |
| Door Lock Status | Overall lock state |
| Door Status | Overall door open/closed state |
| Alarm Arm Status | Alarm armed/disarmed state |
| Trip Distance | Last trip segment distance (miles) |
| Trip End Time | Last trip end timestamp |
| Driving Score – Acceleration | Star rating (0–5) |
| Driving Score – Braking | Star rating (0–5) |
| Weekly Distance (Short Term) | Recent weekly average (miles) |
| Weekly Distance (Long Term) | Long-term weekly average (miles) |
| Lifetime Fuel Used | Total fuel consumed (L) |
| Lifetime Reference Distance | Distance over which fuel was measured (miles) |
| SIM Status | Embedded SIM connectivity state |
| Diagnostic Trouble Codes | Raw OBD DTC data |

### Binary Sensors

| Entity | Description |
|---|---|
| Engine Active | Engine running |
| Ignition | Ignition on/off |
| Moving | Vehicle in motion |
| Lights | Running lights on/off |
| Door Front Driver | Open/closed |
| Door Front Passenger | Open/closed |
| Door Rear Driver | Open/closed |
| Door Rear Passenger | Open/closed |
| Bonnet | Open/closed |
| Boot | Open/closed |
| Window Front Driver | Open/closed |
| Window Front Passenger | Open/closed |
| Window Rear Driver | Open/closed |
| Window Rear Passenger | Open/closed |
| Alarm Active | Triggered/normal |
| 12V Battery Recharge Needed | Service alert |
| Deep Sleep Mode | Vehicle in deep sleep |

### Device Tracker

| Entity | Description |
|---|---|
| Location | GPS coordinates + heading |

---

## Prerequisites

1. A **BMW ConnectedDrive** account linked to your car.
2. Access to the [BMW CarData portal](https://www.bmw.co.uk/en-gb/mybmw/vehicle-overview) — select your vehicle → **BMW CarData**.
3. **Home Assistant 2024.1+** with [HACS](https://hacs.xyz) installed.

---

## Step 1 – BMW Portal Setup

> **Do this before installing in Home Assistant.**

1. Go to [bmw.co.uk/mybmw](https://www.bmw.co.uk/en-gb/mybmw/vehicle-overview) and select your vehicle.
2. Click **BMW CarData**.
3. Under **CarData API**, delete any existing Client ID and generate a new one. **Copy it** — you'll need it during HA setup.
4. Click **Request access to CarData API**. Wait 60 seconds.
5. Click **Request access to CarData Stream**. Wait 60 seconds.
   > BMW's backend takes time to activate permissions. Rushing causes 403 errors.
6. Under **CarData Streaming → Configure data stream**, select all the descriptors you want. You can select all with this browser console snippet (press F12):
   ```js
   document.querySelectorAll('label.chakra-checkbox:not([data-checked])').forEach(l => l.click());
   ```
7. Save.

---

## Step 2 – Install via HACS

1. In Home Assistant, go to **HACS → Integrations → ⋮ → Custom repositories**.
2. Add `https://github.com/GMounsor/bmw-home-assistant` as an **Integration**.
3. Find **BMW Home Assistant** in HACS and install it.
4. Restart Home Assistant.

---

## Step 3 – Configure

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **BMW CarData**.
3. Enter your **Client ID** from the portal.
4. A verification URL and code will appear — open the URL in your browser, enter the code, and approve.
5. Return to Home Assistant and click **Submit**. If you see "authorization pending", complete the BMW approval first and try again.

---

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| 403 Forbidden | Permissions not active yet | Wait 2–3 min after enabling in portal, delete and regenerate Client ID |
| 500 Server Error | Rate limit or BMW backend issue | Wait 5–10 min, delete integration, create new Client ID |
| Authorization pending | Submitted before approving | Complete BMW portal approval, then click Submit again |
| No vehicles found | Account not linked to car | Check ConnectedDrive subscription is active |

---

## API Quota

BMW allows **50 API calls/day** per account. This integration uses:
- 1 call per VIN per poll (every 30 min = max 48 calls/day for 1 car)
- 1 call per VIN per day for tyre diagnosis (refreshed at most every 23 hours)
- 2–3 calls on first setup (vehicle discovery + container creation)

If you have multiple BMWs, polling will use 1 call per VIN per poll. Consider increasing `SCAN_INTERVAL_MINUTES` in `const.py` if needed.

---

## Limitations

- **Read-only** – this integration cannot send commands (lock/unlock, remote start, etc.)
- BMW CarData portal is **not available in all regions** (e.g. disabled in Finland)
- ICE-only – EV/charging sensors not included
- Older vehicles on iDrive 6 or below may send data infrequently

---

## Credits

Built using the official [BMW CarData API](https://bmw-cardata.bmwgroup.com/customer/public/api-documentation).
