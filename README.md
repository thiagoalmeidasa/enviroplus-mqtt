# Enviro+ MQTT Logger

`enviroplus-mqtt` is a Python service that publishes environmental data from an [Enviro+](https://shop.pimoroni.com/products/enviro-plus) via MQTT, with Home Assistant discovery.

## Install on a Raspberry Pi

Pre-built `.deb` packages are attached to each [GitHub Release](https://github.com/thiagoalmeidasa/enviroplus-mqtt/releases). Pick the file matching your Pi OS / Debian / Ubuntu release and architecture:

| File                                                | Target                                      |
|-----------------------------------------------------|---------------------------------------------|
| `enviroplus-mqtt_X.Y.Z-1~bookworm_arm64.deb`        | Raspberry Pi OS / Debian bookworm, 64-bit   |
| `enviroplus-mqtt_X.Y.Z-1~bookworm_armhf.deb`        | Raspberry Pi OS bookworm, 32-bit            |
| `enviroplus-mqtt_X.Y.Z-1~noble_arm64.deb`           | Ubuntu 24.04, 64-bit                        |

1. Connect the Enviro+ board (and the PMS5003 sensor if you have one).
2. Download the matching `.deb` from the latest Release, then:

       sudo apt install ./enviroplus-mqtt_*.deb

   The package installs a self-contained venv at `/opt/venvs/enviroplus-mqtt`, creates a system user `enviroplus-mqtt` with access to the `i2c`, `spi`, `gpio`, and `dialout` groups, and ships the systemd unit `enviroplus-mqtt.service` (installed but not enabled).

3. Edit `/etc/enviroplus-mqtt/config.toml` and set at least `host`.
4. Enable and start the service:

       sudo systemctl enable --now enviroplus-mqtt.service
       journalctl -u enviroplus-mqtt -f

Upgrades preserve your edits to `/etc/enviroplus-mqtt/config.toml` (it is a Debian conffile).

## Configuration

All settings live in `/etc/enviroplus-mqtt/config.toml`. The CLI accepts only `--config PATH` and the maintenance flag `--remove-config`.

```toml
# /etc/enviroplus-mqtt/config.toml

host = "broker.local"   # required
port = 1883
username = "sensor"     # optional
password = "..."        # optional

prefix = "lounge/enviroplus"
room = "LivingRoom"
# client_id defaults to the Pi's serial number

interval = 5            # seconds between published readings
delay = 15              # warm-up seconds before publishing starts
use_pms5003 = false     # set true if the PMS5003 PM sensor is attached
```

| Key           | Type    | Default                  | Notes                                                     |
|---------------|---------|--------------------------|-----------------------------------------------------------|
| `host`        | string  | (required)               | MQTT broker hostname                                      |
| `port`        | int     | `1883`                   | MQTT broker port                                          |
| `username`    | string? | unset                    | MQTT username                                             |
| `password`    | string? | unset                    | MQTT password                                             |
| `prefix`      | string  | `""`                     | Topic prefix (e.g. `lounge/enviroplus`)                   |
| `room`        | string  | `"LivingRoom"`           | Room name used in HA discovery                            |
| `client_id`   | string? | Pi serial number         | MQTT client identifier                                    |
| `interval`    | int     | `5`                      | Seconds between published readings                        |
| `delay`       | int     | `15`                     | Sensor warm-up seconds before publishing starts           |
| `use_pms5003` | bool    | `false`                  | Take PM readings from PMS5003 instead of Enviro+'s gas    |

## Published Topics

Readings publish to:

- `<prefix>/proximity`
- `<prefix>/lux`
- `<prefix>/temperature`
- `<prefix>/pressure`
- `<prefix>/humidity`
- `<prefix>/gas/oxidising`
- `<prefix>/gas/reducing`
- `<prefix>/gas/nh3`
- `<prefix>/particulate/1.0`
- `<prefix>/particulate/2.5`
- `<prefix>/particulate/10.0`

## Build from source

For development or non-Debian systems, run directly with `uv`:

    git clone https://github.com/thiagoalmeidasa/enviroplus-mqtt
    cd enviroplus-mqtt
    uv sync --extra device
    uv run enviroplus2mqtt --config ./config.toml

Run the test suite with `uv run pytest`.

### Reproducing a CI build locally

CI builds each `.deb` inside a prebuilt image at `ghcr.io/thiagoalmeidasa/enviroplus-mqtt-builder:<suite>-<arch>` (defined by `packaging/builder.Dockerfile`, published by `.github/workflows/builder-image.yml`). Pulling the same image locally reproduces a CI build exactly — useful when something fails in CI and you want to poke at it:

    docker login ghcr.io   # one-time; uses a GitHub PAT with read:packages

    docker run --rm -it --platform linux/arm64 \
      -v "$PWD:/src:ro" -v "$PWD/out:/out" \
      ghcr.io/thiagoalmeidasa/enviroplus-mqtt-builder:bookworm-arm64 \
      bash -euxo pipefail -c '
        cp -a /src /work && cd /work
        dch -v "0.2.0-local" -D bookworm --force-distribution "Local build"
        dpkg-buildpackage -us -uc -b
        cp ../enviroplus-mqtt_*.deb /out/
      '

For an interactive shell to debug a failing build, drop the trailing `bash -c '...'` and just run the image:

    docker run --rm -it --platform linux/arm64 \
      -v "$PWD:/work" \
      ghcr.io/thiagoalmeidasa/enviroplus-mqtt-builder:bookworm-arm64

If you need to rebuild the builder image yourself (e.g. testing a `debian/control` change before merging):

    docker build --platform linux/arm64 \
      --build-arg BASE_IMAGE=debian:bookworm-slim \
      -f packaging/builder.Dockerfile \
      -t enviroplus-mqtt-builder:bookworm-arm64 .

The release workflow (`.github/workflows/release-deb.yml`) builds the full matrix on tag push and attaches the artifacts to the GitHub Release. On the first run after a `debian/control` change, trigger `builder-image.yml` first (it auto-runs on `master` push when relevant paths change, or via `gh workflow run builder-image.yml`).
