FROM python:3.12-alpine

ARG PTZ_IMOU_COMMIT=686e9dc79725b2cfe21aeeb804d8eabbe33e8fb6
ARG BUILD_VERSION=0.1.2
ARG BUILD_ARCH

LABEL io.hass.version="${BUILD_VERSION}" \
      io.hass.type="addon" \
      io.hass.arch="${BUILD_ARCH}"

# Upstream's pinned pyproject has an invalid build backend. Its runtime is
# stdlib-only, so extract the original package without invoking that backend.
RUN apk add --no-cache ca-certificates \
    && mkdir -p /opt/ptz-imou \
    && wget -O /tmp/ptz-imou.tar.gz \
       "https://codeload.github.com/jeremyalbrecht/ptz-imou/tar.gz/${PTZ_IMOU_COMMIT}" \
    && tar -xzf /tmp/ptz-imou.tar.gz -C /opt/ptz-imou --strip-components=1

ENV PYTHONPATH=/opt/ptz-imou
RUN python3 -c "from imou_ptz.server import run_server"

COPY run.py /run.py
COPY proxy.py privacy_diagnostics.py /
RUN python3 -c "import proxy, privacy_diagnostics"

CMD ["python3", "/run.py"]
