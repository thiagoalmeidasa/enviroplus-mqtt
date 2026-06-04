from io import StringIO

from enviroplus_mqtt import system

_CPUINFO_WITH_SERIAL = """\
processor\t: 0
model name\t: ARMv7 Processor rev 4 (v7l)
Hardware\t: BCM2835
Revision\t: a020d3
Serial\t\t: 0000000012345678
Model\t\t: Raspberry Pi 3 Model B+
"""

_CPUINFO_WITHOUT_SERIAL = """\
processor\t: 0
model name\t: ARMv7 Processor rev 4 (v7l)
Hardware\t: BCM2835
Revision\t: a020d3
"""


def test_serial_returns_trimmed_value(monkeypatch):
    monkeypatch.setattr("builtins.open", lambda *_a, **_kw: StringIO(_CPUINFO_WITH_SERIAL))
    assert system.get_serial_number() == "0000000012345678"


def test_serial_returns_none_when_missing(monkeypatch):
    monkeypatch.setattr("builtins.open", lambda *_a, **_kw: StringIO(_CPUINFO_WITHOUT_SERIAL))
    assert system.get_serial_number() is None


def test_wifi_returns_ssid_from_query(monkeypatch):
    monkeypatch.setattr(system, "_query_active_ssid", lambda: "MyNetwork")
    assert system.wifi_status() == "MyNetwork"


def test_wifi_returns_none_when_no_active_wifi(monkeypatch):
    monkeypatch.setattr(system, "_query_active_ssid", lambda: None)
    assert system.wifi_status() is None


def test_wifi_returns_none_when_query_raises(monkeypatch):
    def boom():
        raise RuntimeError("dbus exploded")

    monkeypatch.setattr(system, "_query_active_ssid", boom)
    assert system.wifi_status() is None
