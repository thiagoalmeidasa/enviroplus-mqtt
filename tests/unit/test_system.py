from io import StringIO
from subprocess import CalledProcessError

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


def test_wifi_returns_ssid_stripped(monkeypatch):
    monkeypatch.setattr(system, "check_output", lambda *_a, **_kw: "MyNetwork\n")
    assert system.wifi_status() == "MyNetwork"


def test_wifi_returns_empty_string_when_no_ssid(monkeypatch):
    monkeypatch.setattr(system, "check_output", lambda *_a, **_kw: "\n")
    assert system.wifi_status() == ""


def test_wifi_returns_false_when_subprocess_fails(monkeypatch):
    def boom(*_a, **_kw):
        raise CalledProcessError(1, ["iwgetid", "-s"])

    monkeypatch.setattr(system, "check_output", boom)
    assert system.wifi_status() is False


def test_wifi_returns_false_when_iwgetid_missing(monkeypatch):
    def boom(*_a, **_kw):
        raise FileNotFoundError("iwgetid")

    monkeypatch.setattr(system, "check_output", boom)
    assert system.wifi_status() is False
