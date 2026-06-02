from io import StringIO

import main

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


def test_returns_trimmed_serial(monkeypatch):
    monkeypatch.setattr("builtins.open", lambda *_a, **_kw: StringIO(_CPUINFO_WITH_SERIAL))
    assert main.get_serial_number() == "0000000012345678"


def test_returns_none_when_serial_missing(monkeypatch):
    monkeypatch.setattr("builtins.open", lambda *_a, **_kw: StringIO(_CPUINFO_WITHOUT_SERIAL))
    assert main.get_serial_number() is None
