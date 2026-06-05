from pathlib import Path

import pytest

from enviroplus_mqtt import cli


@pytest.fixture(autouse=True)
def stub_serial(monkeypatch):
    monkeypatch.setattr("enviroplus_mqtt.cli.get_serial_number", lambda: "FAKE-SERIAL")


def _write(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "config.toml"
    p.write_text(body)
    return p


def test_minimal_config_applies_defaults(tmp_path):
    config = cli.load_config(_write(tmp_path, 'host = "broker.local"\n'))
    assert config == {
        "host": "broker.local",
        "port": 1883,
        "username": None,
        "password": None,
        "prefix": "",
        "room": "LivingRoom",
        "client_id": "FAKE-SERIAL",
        "interval": 5,
        "delay": 15,
        "use_pms5003": False,
    }


def test_full_config_overrides_defaults(tmp_path):
    config = cli.load_config(
        _write(
            tmp_path,
            """
            host = "broker.local"
            port = 8883
            username = "user"
            password = "pw"
            prefix = "home/lounge"
            room = "Kitchen"
            client_id = "custom-id"
            interval = 10
            delay = 30
            use_pms5003 = true
            """,
        )
    )
    assert config["port"] == 8883
    assert config["username"] == "user"
    assert config["password"] == "pw"
    assert config["prefix"] == "home/lounge"
    assert config["room"] == "Kitchen"
    assert config["client_id"] == "custom-id"
    assert config["interval"] == 10
    assert config["delay"] == 30
    assert config["use_pms5003"] is True


def test_missing_file_exits(tmp_path):
    with pytest.raises(SystemExit, match="file not found"):
        cli.load_config(tmp_path / "does-not-exist.toml")


def test_invalid_toml_exits(tmp_path):
    with pytest.raises(SystemExit, match="config error"):
        cli.load_config(_write(tmp_path, "host = \n"))


def test_missing_host_exits(tmp_path):
    with pytest.raises(SystemExit, match="'host' is required"):
        cli.load_config(_write(tmp_path, "port = 1883\n"))


def test_placeholder_host_exits(tmp_path):
    with pytest.raises(SystemExit, match="'host' is required"):
        cli.load_config(_write(tmp_path, 'host = "CHANGE-ME"\n'))


def test_empty_host_exits(tmp_path):
    with pytest.raises(SystemExit, match="'host' is required"):
        cli.load_config(_write(tmp_path, 'host = ""\n'))


def test_unknown_key_exits(tmp_path):
    with pytest.raises(SystemExit, match="unknown key"):
        cli.load_config(_write(tmp_path, 'host = "x"\nwat = 1\n'))


def test_wrong_type_for_port_exits(tmp_path):
    with pytest.raises(SystemExit, match="'port' must be"):
        cli.load_config(_write(tmp_path, 'host = "x"\nport = "1883"\n'))


def test_bool_rejected_for_int_field(tmp_path):
    with pytest.raises(SystemExit, match="'port' must be an integer"):
        cli.load_config(_write(tmp_path, 'host = "x"\nport = true\n'))


def test_wrong_type_for_bool_field(tmp_path):
    with pytest.raises(SystemExit, match="'use_pms5003' must be"):
        cli.load_config(_write(tmp_path, 'host = "x"\nuse_pms5003 = 1\n'))
