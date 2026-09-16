# IMOU Local PTZ — Home Assistant OS add-on

Runs the `ptz-imou` DVRIP/ONVIF proxy permanently on Home Assistant OS. It is
intended for IMOU cameras whose video works locally over RTSP but whose native
ONVIF PTZ does not move the camera.

The add-on exposes port `8089` on the Home Assistant host by default. Keep this
port inside your trusted LAN; the upstream HTTP API does not authenticate its
requests.

## Install

1. Upload this repository to GitHub (or copy the `imou-ptz` directory to
   `/addons/imou-ptz` for a local add-on).
2. In Home Assistant, open **Settings → Add-ons → Add-on Store → Repositories**
   and add the GitHub repository URL.
3. Install **IMOU Local PTZ**.
4. Set the camera IP, DVRIP port, username and password on the Configuration
   tab, then start the add-on.
5. Enable **Start on boot** and **Watchdog**.

Example add-on configuration:

```yaml
camera_host: 10.100.1.201
dvrip_port: 37777
username: admin
password: "CAMERA_PASSWORD"
```

Test from a device on the LAN (replace `HOME_ASSISTANT_IP`):

```text
http://HOME_ASSISTANT_IP:8089/health
http://HOME_ASSISTANT_IP:8089/ptz/move?code=Right&speed=2&duration=0.4
```

Supported movement codes include `Left`, `Right`, `Up`, `Down`, `LeftUp`,
`LeftDown`, `RightUp`, and `RightDown`.

## Home Assistant commands

Copy the relevant entries from `examples/configuration.yaml` into your Home
Assistant `configuration.yaml`, replace the IP addresses, and restart Home
Assistant. The file includes commands for both the IMOU camera and the hacked
Xiaomi C200.

Use `examples/dashboard.yaml` as a starting point for two live camera cards
with PTZ buttons. Replace `camera.imou_ranger` and `camera.xiaomi_c200` with the
actual camera entity IDs in your system.

## ONVIF proxy

The same port also provides the ONVIF device endpoint:

```text
http://HOME_ASSISTANT_IP:8089/onvif/device_service
```

This can be used by Frigate or another ONVIF client while video continues to
come directly from the camera's RTSP stream.

The container installs `jeremyalbrecht/ptz-imou` at commit
`686e9dc79725b2cfe21aeeb804d8eabbe33e8fb6` for reproducible builds.

