<p align="center">
  <img src="logo.png" alt="Powershop NZ" height="120">
</p>

# Powershop New Zealand — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release](https://img.shields.io/github/release/PMKA/powershop-nz.svg)](https://github.com/PMKA/powershop-nz/releases)

A Home Assistant custom component for **Powershop New Zealand** customers. Monitor your account balance, electricity rates, usage, and Power Pack coverage — updated every 15 minutes.

## Features

- **Account Balance** — current balance in NZD
- **Time-of-Use Rates** — off-peak, peak, and shoulder rates in c/kWh
- **Usage Monitoring** — today's kWh and billing period kWh
- **Billing Period Sensors** — mirrors the Powershop app: used cost, estimated total, pack coverage %, and still-to-buy shortfall for the current period
- **Power Pack Tracking** — total redeemable pack balance and full pack list; upcoming 5 billing periods show estimated cost vs packs already purchased
- **Passwordless Auth** — uses Powershop's email OTP login (no password stored)
- **Automatic Token Refresh** — stays authenticated in the background
- **Regular Updates** — 15-minute refresh interval

## Requirements

- A Powershop NZ account at [app.powershop.nz](https://app.powershop.nz) - Your account must be migrated to Powershop's new platform. You can verify this by checking if you can log in at app.powershop.nz. Powershop is rolling this out gradually and you'll get an email from them letting you know your account is being migrated — if your account hasn't been migrated yet, the integration will not work. 
- Home Assistant 2024.1 or later
- HACS (for managed installation)

## Installation

### Via HACS (Recommended)

1. Open **HACS** in Home Assistant
2. Go to **Integrations**
3. Click the three dots (⋮) in the top right corner and select **Custom repositories**
4. Add `https://github.com/PMKA/powershop-nz` and select **Integration**
5. Click **Add**, then find **Powershop NZ** in the list and install it
6. Restart Home Assistant

### Manual Installation

1. Download or clone this repository
2. Copy the `custom_components/powershop/` folder into your HA config's `custom_components/` directory
3. Restart Home Assistant

## Configuration

Authentication uses a one-time password (OTP) sent to your email — no password required:

1. Go to **Settings**, then **Devices & Services**, then **Add Integration**
2. Search for **Powershop**
3. Enter your Powershop account email address and click **Submit**
4. Check your email for the one-time code and enter it, then click **Submit**

Your account number and property ID are discovered automatically. Home Assistant will prompt you to re-authenticate if your session ever expires — just repeat the OTP process.

## Sensors

| Entity | Description | Unit |
|--------|-------------|------|
| `sensor.powershop_balance` | Current account balance | NZD |
| `sensor.powershop_off_peak_rate` | Off-peak electricity rate | c/kWh |
| `sensor.powershop_peak_rate` | Peak electricity rate | c/kWh |
| `sensor.powershop_shoulder_rate` | Shoulder electricity rate | c/kWh |
| `sensor.powershop_usage_today` | kWh consumed today (last 24 h) | kWh |
| `sensor.powershop_usage_billing_period` | kWh consumed this billing period | kWh |
| `sensor.powershop_cost_billing_period` | Cost for the current billing period | NZD |
| `sensor.powershop_period_used_cost` | Actual metered spend so far this billing period | NZD |
| `sensor.powershop_period_estimated_cost` | Projected total cost for this billing period | NZD |
| `sensor.powershop_period_still_to_buy` | How much more in packs you'd need to cover this billing period | NZD |
| `sensor.powershop_period_coverage_pct` | % of projected bill covered by packs already purchased | % |
| `sensor.powershop_voucher_balance` | Total redeemable Power Pack balance | NZD |
| `sensor.powershop_daily_standing_charge` | Daily fixed (standing/line) charge | NZD |

### Sensor Attributes

**`sensor.powershop_period_estimated_cost`** includes an `upcoming_periods` attribute — a list of the next 5 billing periods, each containing:

```yaml
- period_start: "2026-05-06"
  period_end: "2026-06-05"
  cost_estimated_nzd: 390.78     # projected cost based on your usage pattern
  voucher_bought_nzd: 0.00       # packs pre-purchased for that specific month
  cost_still_to_buy_nzd: 390.78  # shortfall
  coverage_pct: 0.0
```

**`sensor.powershop_voucher_balance`** includes a `vouchers` attribute listing every active pack with its name, available-from date, remaining balance, and original value.

## Troubleshooting

**No OTP email?** Check spam, make sure you're using the right address, and try again, i found at some times of day the emails were slow to come through.
**"Email address not found" during setup** Even if your email is correct, this can happen if your account hasn't yet been migrated to Powershop's new platform. Powershop is doing a staged rollout — check if you can log in at app.powershop.nz first. If you can't, your account isn't on the new system yet and you'll need to wait or contact Powershop.

## 📝 Changelog

### v2.1.0 (2026-05-21)

> ⚠️ **Breaking Change — Manual Reinstall Required**
>
> The integration domain has been renamed from `powershop` to `powershop_nz`. **The HACS automatic update will fail** with the following error — this is expected:
>
> ```
> Downloading PMKA/powershop-nz with version v2.1.0 failed with:
> No manifest.json file found 'custom_components/powershop/manifest.json'
> ```
>
> You need to manually reinstall instead:
>
> 1. Go to **Settings**, then **Devices & Services**, and delete the existing Powershop integration
> 2. In **HACS**, remove the Powershop NZ integration
> 3. **Restart Home Assistant** (this is required — it clears the HACS domain cache)
> 4. In **HACS**, add `https://github.com/PMKA/powershop-nz` back as a custom repository
> 5. Install **Powershop NZ** from HACS (it will now install to the correct folder)
> 6. **Restart Home Assistant**
> 7. Go to **Settings**, then **Devices & Services**, then **Add Integration** and set up Powershop NZ
>
> Your sensors will be created fresh with the correct entity IDs (`sensor.powershop_nz_{key}`, e.g. `sensor.powershop_nz_balance`).
> Update any automations, dashboards, or scripts that reference the old IDs.
>
> Sorry for the hassle — the install base is still small so this felt like the right time to get the naming sorted properly rather than leaving it as `powershop` forever. It makes the integration easier to maintain and opens up submitting the icon to the official HA brands repo, so it's worth it in the long run. This is a one-time thing — future updates will install normally through HACS.

- Renamed integration domain from `powershop` to `powershop_nz` to prevent future conflicts with other Powershop country integrations — this will also allow the icon to be submitted to the HA brands repo 🥳
- Fixed entity ID generation: sensors now reliably produce `sensor.powershop_nz_{key}` (e.g. `sensor.powershop_nz_balance`)

### v2.0.9 (2026-05-21)
- Added `hourly_usage` attribute to `sensor.powershop_usage_today` — hourly kWh and cost for today
- Added `daily_usage` attribute to `sensor.powershop_usage_billing_period` — daily kWh, cost, and reading quality for the current billing period

### v2.0.8 (2026-05-01)
- Added `Daily Standing Charge` sensor — exposes the daily fixed/line charge in c/day

### v2.0.5 (2026-04-10)
- Updated integration icon — new transparent PNG, shown in HA integrations page and HACS store
- Documented Firebase API key as public project identifier (not a secret)
- Added GitHub secret scanning allowlist to suppress false-positive alerts
- Removed developer/debug scripts from the repository
- Repository URLs updated following rename to `powershop-nz`

### v2.0.4 (2026-04-09)
- Fixed upcoming billing period pack coverage showing $0 for periods without dedicated future packs
- The redeemable pack pool now cascades across future periods, matching how the Powershop app calculates coverage

### v2.0.3 (2026-04-09)
- Fixed all sensors showing unavailable after updating to v2.0.2
- Fixed Power Pack sensors failing to load on some accounts
- Fixed integration failing to initialise correctly on HA startup
- Various HACS compliance fixes

### v2.0.2 (2026-04-09)
- Added `Used This Billing Period` sensor — actual confirmed spend (USED in app)
- Added `Estimated Cost This Billing Period` sensor — full projected monthly cost (EST in app)
- Added `Still To Buy This Billing Period` sensor — pack shortfall warning
- Added `Billing Period Pack Coverage` sensor — % of estimated bill covered by packs
- `period_estimated_cost` sensor exposes `upcoming_periods` attribute with 5-month forward forecast (estimated cost + pre-purchased packs per period)
- Updated Power Pack query to use `availableBeforeDate`/`availableFromDate` filters matching the website's per-period breakdown
- Daily measurements now use a dedicated date-range query that includes `readingQuality` (ACTUAL vs ESTIMATED)

### v2.0.1
- Added usage sensors (today kWh, billing period kWh, billing period cost)
- Added Power Pack / voucher balance sensor

### v2.0.0 (2026-04-08)
- Full rewrite for the new Powershop app (`app.powershop.nz`)
- Replaced HTML scraping with Firebase OTP authentication + GraphQL API
- Added account balance sensor
- Passwordless login — no password ever stored
- Automatic session refresh with long-lived tokens
- Re-authentication support via HA config flow

### v1.0.0 (2025-11-10)
- Initial release
- Rate monitoring via the legacy `secure.powershop.co.nz` site

##  License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

##  Disclaimer

This integration is **not officially affiliated** with Powershop. Use at your own risk, I just wanted to have my rate data available in HA, reached out to Powershop to ask for API access but was nothing available so built my own.
