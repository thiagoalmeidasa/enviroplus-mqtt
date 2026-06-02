from subprocess import CalledProcessError

import logger


def test_returns_ssid_stripped(monkeypatch):
    monkeypatch.setattr(logger, "check_output", lambda *_a, **_kw: "MyNetwork\n")
    assert logger.wifi_status() == "MyNetwork"


def test_returns_empty_string_when_no_ssid(monkeypatch):
    monkeypatch.setattr(logger, "check_output", lambda *_a, **_kw: "\n")
    assert logger.wifi_status() == ""


def test_returns_false_when_subprocess_fails(monkeypatch):
    def boom(*_a, **_kw):
        raise CalledProcessError(1, ["iwgetid", "-s"])

    monkeypatch.setattr(logger, "check_output", boom)
    assert logger.wifi_status() is False


def test_returns_false_when_iwgetid_missing(monkeypatch):
    def boom(*_a, **_kw):
        raise FileNotFoundError("iwgetid")

    monkeypatch.setattr(logger, "check_output", boom)
    assert logger.wifi_status() is False
