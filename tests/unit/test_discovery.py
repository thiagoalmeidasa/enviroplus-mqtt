import pytest

from enviroplus_mqtt.discovery import SENSOR_KEYS, build_sensor_configs

BASE_SENSORS = {
    "proximity",
    "lux",
    "temperature",
    "pressure",
    "humidity",
    "oxidising",
    "reducing",
    "nh3",
}
PM_SENSORS = {"pm10", "pm25", "pm100"}
REQUIRED_HA_KEYS = {
    "name",
    "state_topic",
    "unique_id",
    "value_template",
    "unit_of_measurement",
}


@pytest.mark.parametrize("use_pms5003", [False, True])
def test_returned_sensor_keys(use_pms5003):
    configs = build_sensor_configs(
        room="Lounge", prefix="home", client_id="CLIENT-1", use_pms5003=use_pms5003
    )
    expected = BASE_SENSORS | (PM_SENSORS if use_pms5003 else set())
    assert set(configs.keys()) == expected


def test_every_payload_has_required_ha_keys():
    configs = build_sensor_configs(
        room="Lounge", prefix="home", client_id="CLIENT-1", use_pms5003=True
    )
    for payload in configs.values():
        assert payload.keys() >= REQUIRED_HA_KEYS


def test_state_topic_and_unique_id_format():
    configs = build_sensor_configs(
        room="Kitchen", prefix="myhome", client_id="ABC123", use_pms5003=False
    )
    for sensor, payload in configs.items():
        assert payload["state_topic"] == f"myhome/sensor/Kitchen/{sensor}/state"
        assert payload["unique_id"] == f"{sensor}-ABC123"


def test_humidity_unit_is_percent():
    configs = build_sensor_configs(
        room="Lounge", prefix="home", client_id="CLIENT-1", use_pms5003=False
    )
    assert configs["humidity"]["unit_of_measurement"] == "%"


def test_known_sensor_device_classes_and_units():
    configs = build_sensor_configs(
        room="Lounge", prefix="home", client_id="CLIENT-1", use_pms5003=False
    )
    assert configs["temperature"]["device_class"] == "temperature"
    assert configs["temperature"]["unit_of_measurement"] == "°C"
    assert configs["pressure"]["device_class"] == "pressure"
    assert configs["pressure"]["unit_of_measurement"] == "hPa"
    assert configs["humidity"]["device_class"] == "humidity"
    assert configs["lux"]["device_class"] == "illuminance"
    assert configs["lux"]["unit_of_measurement"] == "lx"
    assert configs["proximity"]["unit_of_measurement"] == "cm"


def test_name_uses_capitalized_sensor_key():
    configs = build_sensor_configs(
        room="Lounge", prefix="home", client_id="CLIENT-1", use_pms5003=False
    )
    assert configs["temperature"]["name"] == "Lounge Temperature"
    assert configs["nh3"]["name"] == "Lounge Nh3"


def test_sensor_keys_constant_matches_full_set():
    assert set(SENSOR_KEYS) == BASE_SENSORS | PM_SENSORS


def test_payload_dicts_are_independent_between_calls():
    """Mutating one returned payload must not leak into a later call."""
    first = build_sensor_configs(room="A", prefix="p", client_id="c1", use_pms5003=False)
    first["humidity"]["unit_of_measurement"] = "MUTATED"

    second = build_sensor_configs(room="A", prefix="p", client_id="c2", use_pms5003=False)
    assert second["humidity"]["unit_of_measurement"] == "%"
