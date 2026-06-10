<<<<<<< HEAD
# BMW Home Assistant

A custom Home Assistant integration for BMW vehicles using the official [BMW CarData API](https://bmw-cardata.bmwgroup.com/customer/public/api-documentation).

Designed for **petrol/diesel (ICE) BMW vehicles** in the UK/EU. Polls the BMW REST API every 30 minutes (within the free 50 calls/day limit).

---

## What You Get

| Entity | Type | Description |
|---|---|---|
| Mileage | Sensor | Odometer reading (km) |
| Fuel Level | Sensor | Fuel % |
| Remaining Fuel | Sensor | Estimated range from fuel (km) |
| Remaining Range | Sensor | Navigation system range estimate (km) |
| Next Service Distance | Sensor | km until next service |
| Service Due Date | Sensor | Date of next service |
| Door Lock Status | Sensor | Overall lock state |
| Door Status | Sensor | Overall door open/closed state |
| Alarm Status | Sensor | Alarm arm state |
| Bonnet | Binary Sensor | Open/closed |
| Boot | Binary Sensor | Open/closed |
| Door Front Driver | Binary Sensor | Open/closed |
| Door Front Passenger | Binary Sensor | Open/closed |
| Door Rear Driver | Binary Sensor | Open/closed |
| Door Rear Passenger | Binary Sensor | Open/closed |
| Windows (×4) | Binary Sensor | Open/closed |
| Alarm Active | Binary Sensor | Triggered/normal |
| Location | Device Tracker | GPS coordinates + heading |

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
- 2–3 calls on first setup (vehicle discovery + container creation)

If you have multiple BMWs, polling will use 1 call per VIN per poll. Consider increasing `SCAN_INTERVAL_MINUTES` in `const.py` if needed.

---

## Limitations

- **Read-only** – this integration cannot send commands (lock/unlock, remote start, etc.)
- BMW CarData portal is **not available in all regions** (e.g. disabled in Finland)
- ICE-only – EV/charging sensors not included (can be added by extending `const.py`)
- Older vehicles on iDrive 6 or below may send data infrequently

---

## Credits

Built using the official [BMW CarData API](https://bmw-cardata.bmwgroup.com/customer/public/api-documentation). Inspired by [kvanbiesen/bmw-cardata-ha](https://github.com/kvanbiesen/bmw-cardata-ha).
=======
# bmw-home-assistant
BMW Integration using car data
>>>>>>> 056b630e23a894115f4b08a3e614b29e713d15af
