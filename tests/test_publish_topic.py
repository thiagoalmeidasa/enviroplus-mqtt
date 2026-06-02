from unittest.mock import MagicMock

import pytest

from logger import EnvLogger


def _make_logger(prefix: str):
    instance = EnvLogger.__new__(EnvLogger)
    instance.prefix = prefix
    instance.client = MagicMock()
    return instance


def test_prefix_is_prepended():
    env = _make_logger(prefix="home")
    env.publish("sensor/Lounge/temperature/state", 21.4)
    env.client.publish.assert_called_once_with("home/sensor/Lounge/temperature/state", "21.4")


def test_prefix_slashes_are_stripped():
    env = _make_logger(prefix="/home/")
    env.publish("sensor/x/y", "value")
    env.client.publish.assert_called_once_with("home/sensor/x/y", "value")


def test_empty_prefix_yields_leading_slash():
    """Locks in current behavior: an empty prefix produces a leading-slash topic."""
    env = _make_logger(prefix="")
    env.publish("sensor/x/y", 1)
    env.client.publish.assert_called_once_with("/sensor/x/y", "1")


@pytest.mark.parametrize(
    "value,expected", [(42, "42"), (3.14, "3.14"), ("hello", "hello"), (True, "True")]
)
def test_value_is_stringified(value, expected):
    env = _make_logger(prefix="p")
    env.publish("t", value)
    env.client.publish.assert_called_once_with("p/t", expected)
