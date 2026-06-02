"""Home Assistant MQTT discovery payloads.

Pure data; no I/O, no hardware. The caller publishes the returned payloads.
"""

SENSOR_KEYS: tuple[str, ...] = (
    "proximity",
    "lux",
    "temperature",
    "pressure",
    "humidity",
    "oxidising",
    "reducing",
    "nh3",
    "pm10",
    "pm25",
    "pm100",
)

_BASE_CONFIGS: dict[str, dict] = {
    "proximity": {
        "unit_of_measurement": "cm",
        "value_template": "{{ value_json }}",
    },
    "lux": {
        "device_class": "illuminance",
        "unit_of_measurement": "lx",
        "value_template": "{{ value_json }}",
        "icon": "mdi:weather-sunny",
    },
    "temperature": {
        "device_class": "temperature",
        "unit_of_measurement": "°C",
        "value_template": "{{ value_json }}",
        "icon": "mdi:thermometer",
    },
    "pressure": {
        "device_class": "pressure",
        "unit_of_measurement": "hPa",
        "value_template": "{{ value_json }}",
        "icon": "mdi:arrow-down-bold",
    },
    "humidity": {
        "device_class": "humidity",
        "unit_of_measurement": "%",
        "value_template": "{{ value_json }}",
        "icon": "mdi:water-percent",
    },
    "oxidising": {
        "unit_of_measurement": "no2",
        "value_template": "{{ value_json }}",
        "icon": "mdi:thought-bubble",
    },
    "reducing": {
        "unit_of_measurement": "CO",
        "value_template": "{{ value_json }}",
        "icon": "mdi:thought-bubble",
    },
    "nh3": {
        "unit_of_measurement": "nh3",
        "value_template": "{{ value_json }}",
        "icon": "mdi:thought-bubble",
    },
}

_PMS_CONFIGS: dict[str, dict] = {
    "pm10": {
        "unit_of_measurement": "ug/m3",
        "value_template": "{{ value_json }}",
        "icon": "mdi:thought-bubble-outline",
    },
    "pm25": {
        "unit_of_measurement": "ug/m3",
        "value_template": "{{ value_json }}",
        "icon": "mdi:thought-bubble-outline",
    },
    "pm100": {
        "unit_of_measurement": "ug/m3",
        "value_template": "{{ value_json }}",
        "icon": "mdi:thought-bubble-outline",
    },
}


def build_sensor_configs(
    room: str, prefix: str, client_id: str, use_pms5003: bool
) -> dict[str, dict]:
    """Return {sensor_name: ha_discovery_payload} for all enabled sensors."""
    configs = {key: dict(value) for key, value in _BASE_CONFIGS.items()}
    if use_pms5003:
        for key, value in _PMS_CONFIGS.items():
            configs[key] = dict(value)

    for sensor, payload in configs.items():
        payload["name"] = f"{room} {sensor.capitalize()}"
        payload["state_topic"] = f"{prefix}/sensor/{room}/{sensor}/state"
        payload["unique_id"] = f"{sensor}-{client_id}"

    return configs
