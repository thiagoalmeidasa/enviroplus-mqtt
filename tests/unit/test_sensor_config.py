import json
from unittest.mock import MagicMock

import pytest

from enviroplus_mqtt.mqtt_logger import EnvLogger

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


def _make_logger(
    use_pms5003: bool, *, room: str = "Lounge", prefix: str = "home", client_id: str = "CLIENT-1"
):
    """Build an EnvLogger without running __init__ (which opens MQTT and hits hardware)."""
    instance = EnvLogger.__new__(EnvLogger)
    instance.room = room
    instance.prefix = prefix
    instance.client_id = client_id
    instance.use_pms5003 = use_pms5003
    instance.client = MagicMock()
    return instance


def _published(env):
    """Return [(topic, payload_dict), ...] for every client.publish call."""
    out = []
    for call in env.client.publish.call_args_list:
        topic, payload = call.args
        out.append((topic, json.loads(payload)))
    return out


@pytest.mark.parametrize("use_pms5003", [False, True])
def test_publishes_one_config_per_sensor(use_pms5003):
    env = _make_logger(use_pms5003=use_pms5003)

    env.sensor_config()

    expected = BASE_SENSORS | (PM_SENSORS if use_pms5003 else set())
    actual_sensors = set()
    for topic, _ in _published(env):
        assert topic.startswith("home/sensor/Lounge/")
        sensor = topic.removeprefix("home/sensor/Lounge/").removesuffix("/config")
        actual_sensors.add(sensor)
    assert actual_sensors == expected


def test_pms_sensors_omitted_when_disabled():
    env = _make_logger(use_pms5003=False)
    env.sensor_config()
    topics = [topic for topic, _ in _published(env)]
    for pm in PM_SENSORS:
        assert not any(pm in t for t in topics)


def test_every_payload_has_required_ha_keys():
    env = _make_logger(use_pms5003=True)
    env.sensor_config()
    for _, payload in _published(env):
        assert {
            "name",
            "state_topic",
            "unique_id",
            "value_template",
            "unit_of_measurement",
        } <= payload.keys()


def test_state_topic_and_unique_id_format():
    env = _make_logger(use_pms5003=False, room="Kitchen", prefix="myhome", client_id="ABC123")
    env.sensor_config()
    for _, payload in _published(env):
        assert payload["state_topic"].startswith("myhome/sensor/Kitchen/")
        assert payload["state_topic"].endswith("/state")
        assert payload["unique_id"].endswith("-ABC123")


def test_humidity_unit_is_percent():
    """Locks in the fix from commit 2a8343a (unit was '%H', changed to '%')."""
    env = _make_logger(use_pms5003=False)
    env.sensor_config()
    for topic, payload in _published(env):
        if topic.endswith("humidity/config"):
            assert payload["unit_of_measurement"] == "%"
            return
    pytest.fail("humidity config was never published")


def test_known_sensor_device_classes_and_units():
    env = _make_logger(use_pms5003=False)
    env.sensor_config()
    by_sensor = {}
    for topic, payload in _published(env):
        sensor = topic.removeprefix("home/sensor/Lounge/").removesuffix("/config")
        by_sensor[sensor] = payload

    assert by_sensor["temperature"]["device_class"] == "temperature"
    assert by_sensor["temperature"]["unit_of_measurement"] == "°C"
    assert by_sensor["pressure"]["device_class"] == "pressure"
    assert by_sensor["pressure"]["unit_of_measurement"] == "hPa"
    assert by_sensor["humidity"]["device_class"] == "humidity"
    assert by_sensor["lux"]["device_class"] == "illuminance"
    assert by_sensor["lux"]["unit_of_measurement"] == "lx"
    assert by_sensor["proximity"]["unit_of_measurement"] == "cm"


def test_name_uses_capitalized_sensor_key():
    env = _make_logger(use_pms5003=False, room="Lounge")
    env.sensor_config()
    by_sensor = {
        topic.removeprefix("home/sensor/Lounge/").removesuffix("/config"): payload
        for topic, payload in _published(env)
    }
    assert by_sensor["temperature"]["name"] == "Lounge Temperature"
    assert by_sensor["nh3"]["name"] == "Lounge Nh3"
