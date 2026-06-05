import argparse
import sys
import time
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from enviroplus_mqtt.mqtt_logger import EnvLogger
from enviroplus_mqtt.system import get_serial_number

_DEFAULTS: dict[str, Any] = {
    "port": 1883,
    "username": None,
    "password": None,
    "prefix": "",
    "room": "LivingRoom",
    "client_id": None,
    "interval": 5,
    "delay": 15,
    "use_pms5003": False,
}

_TYPES: dict[str, type | tuple[type, ...]] = {
    "host": str,
    "port": int,
    "username": (str, type(None)),
    "password": (str, type(None)),
    "prefix": str,
    "room": str,
    "client_id": (str, type(None)),
    "interval": int,
    "delay": int,
    "use_pms5003": bool,
}


def _check_type(key: str, value: Any) -> None:
    expected = _TYPES[key]
    types_tuple = expected if isinstance(expected, tuple) else (expected,)
    # int fields must not accept bool (bool is a subclass of int)
    if int in types_tuple and bool not in types_tuple and isinstance(value, bool):
        sys.exit(f"config error: '{key}' must be an integer, got bool")
    if not isinstance(value, types_tuple):
        names = "/".join(t.__name__ for t in types_tuple)
        sys.exit(f"config error: '{key}' must be {names}, got {type(value).__name__}")


def load_config(path: Path) -> dict[str, Any]:
    """Load configuration from a TOML file at `path`.

    Required key: `host`. All other keys fall back to defaults; missing
    `client_id` defaults to the device serial number.
    """
    if not path.is_file():
        sys.exit(f"config error: file not found: {path}")

    try:
        with path.open("rb") as f:
            raw = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        sys.exit(f"config error: {path}: {exc}")

    unknown = set(raw) - set(_TYPES)
    if unknown:
        sys.exit(f"config error: unknown key(s): {', '.join(sorted(unknown))}")

    if "host" not in raw or raw["host"] == "" or raw["host"] == "CHANGE-ME":
        sys.exit("config error: 'host' is required and must be set (edit the config file)")

    config: dict[str, Any] = dict(_DEFAULTS)
    config.update(raw)

    for key in _TYPES:
        _check_type(key, config[key])

    if config["client_id"] is None:
        config["client_id"] = get_serial_number()

    return config


def _build_argparser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="enviroplus2mqtt", add_help=False)
    ap.add_argument(
        "--config",
        required=True,
        type=Path,
        help="path to the TOML configuration file",
    )
    ap.add_argument(
        "--remove-config",
        action="store_true",
        help="remove MQTT discovery configs from the broker and exit",
    )
    ap.add_argument("--help", action="help", help="print this help message and exit")
    return ap


def main() -> None:
    args = _build_argparser().parse_args()
    config = load_config(args.config)

    logger = EnvLogger(
        client_id=config["client_id"],
        host=config["host"],
        port=config["port"],
        username=config["username"],
        password=config["password"],
        room=config["room"],
        prefix=config["prefix"],
        use_pms5003=config["use_pms5003"],
        num_samples=config["interval"],
    )

    if args.remove_config:
        logger.remove_sensor_config()
        logger.destroy()
        sys.exit("Configs removed")

    # Warm-up window: take readings without publishing so sensors can stabilise.
    publish_start_time = time.time() + config["delay"]
    while time.time() < publish_start_time:
        logger.update(publish_readings=False)
        time.sleep(1)

    next_sample_time = time.time()
    next_publish_time = time.time() + config["interval"]

    while True:
        if logger.connection_error is not None:
            sys.exit(f"Connecting to the MQTT server failed: {logger.connection_error}")

        should_publish = time.time() >= next_publish_time
        if should_publish:
            next_publish_time += config["interval"]
            logger.sensor_config()
        logger.update(publish_readings=should_publish)

        next_sample_time += 1
        sleep_duration = max(next_sample_time - time.time(), 0)
        time.sleep(sleep_duration)


if __name__ == "__main__":
    main()
