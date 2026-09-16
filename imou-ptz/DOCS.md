# Configuration

For the complete Home Assistant REST command and video + PTZ card setup, see
the [Romanian guide](https://github.com/mihaifireball/ha-imou-local/blob/main/docs/home-assistant-ptz-ro.md).

Set these values on the add-on Configuration tab:

- `camera_host`: fixed LAN address of the IMOU camera.
- `dvrip_port`: DVRIP port; normally `37777`.
- `username`: camera user; normally `admin`.
- `password`: camera password.

The add-on exposes its HTTP and ONVIF service on Home Assistant port `8089` by
default. The port can be changed on the add-on Network tab.

Health check:

```text
http://HOME_ASSISTANT_IP:8089/health
```

Move right:

```text
http://HOME_ASSISTANT_IP:8089/ptz/move?code=Right&speed=2&duration=0.4
```

Do not expose this port to the Internet. The API is designed for a trusted LAN
and has no request authentication.
