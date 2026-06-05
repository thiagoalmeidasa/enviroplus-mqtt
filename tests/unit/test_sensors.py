"""Regression tests for sensor module behavior."""

import importlib
import sys

import enviroplus_mqtt.sensors


def test_ltr559_not_instantiated_at_module_import():
    """LTR559() must be deferred to SensorReader.__init__.

    Calling it at module import made `enviroplus2mqtt --help` crash on
    any machine without I2C hardware (e.g. CI smoke containers).
    """
    ltr559_mock = sys.modules["ltr559"].LTR559
    ltr559_mock.reset_mock()

    importlib.reload(enviroplus_mqtt.sensors)

    assert ltr559_mock.call_count == 0, (
        "LTR559() was called at module-import time; it must be deferred to SensorReader.__init__"
    )


def test_sensorreader_init_constructs_ltr559():
    ltr559_mock = sys.modules["ltr559"].LTR559
    ltr559_mock.reset_mock()

    enviroplus_mqtt.sensors.SensorReader(use_pms5003=False)

    assert ltr559_mock.called
