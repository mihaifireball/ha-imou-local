# ha-imou-local

Home Assistant OS add-on repository for fully local PTZ control of compatible
IMOU/Dahua cameras.

## Installation

[Add repository to Home Assistant](https://my.home-assistant.io/redirect/supervisor_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fmihaifireball%2Fha-imou-local)

The link requires this repository to be public. GitHub login in your browser
does not grant Home Assistant access to a private repository.

Add this repository URL in **Settings → Add-ons → Add-on Store → Repositories**,
then install **IMOU Local PTZ**.

The add-on connects to the camera over DVRIP/TCP 37777 and exposes a local HTTP
API plus an ONVIF PTZ proxy. See `imou-ptz/README.md` for configuration and the
`examples` directory for Home Assistant commands and dashboard cards covering
both IMOU Ranger 2 and Xiaomi C200.

This add-on controls one IMOU camera. Xiaomi commands are examples based on
your existing HTTP hack; video and camera entities must be configured separately.
This is not an automatic video integration or a multi-camera proxy.

Only source/YAML checks have been performed here. Installation on HAOS/ARM64
and physical camera control still need testing on your Raspberry Pi.

Upstream: https://github.com/jeremyalbrecht/ptz-imou
