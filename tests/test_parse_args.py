import pytest

import main


@pytest.fixture(autouse=True)
def stub_serial(monkeypatch):
    monkeypatch.setattr(main, "get_serial_number", lambda: "FAKE-SERIAL")


def _set_argv(monkeypatch, *args):
    monkeypatch.setattr("sys.argv", ["main.py", *args])


def test_host_is_required(monkeypatch):
    _set_argv(monkeypatch)
    with pytest.raises(SystemExit):
        main.parse_args()


def test_defaults(monkeypatch):
    _set_argv(monkeypatch, "--host", "broker.local")
    args = main.parse_args()
    assert args == {
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
        "remove_config": False,
    }


def test_numeric_flags_coerce_to_int(monkeypatch):
    _set_argv(
        monkeypatch,
        "--host",
        "broker.local",
        "--port",
        "8883",
        "--interval",
        "10",
        "--delay",
        "30",
    )
    args = main.parse_args()
    assert args["port"] == 8883
    assert args["interval"] == 10
    assert args["delay"] == 30
    assert isinstance(args["port"], int)
    assert isinstance(args["interval"], int)
    assert isinstance(args["delay"], int)


def test_string_flags_pass_through(monkeypatch):
    _set_argv(
        monkeypatch,
        "--host",
        "broker.local",
        "--username",
        "user",
        "--password",
        "pw",
        "--prefix",
        "home/lounge",
        "--room",
        "Kitchen",
        "--client-id",
        "custom-id",
    )
    args = main.parse_args()
    assert args["username"] == "user"
    assert args["password"] == "pw"
    assert args["prefix"] == "home/lounge"
    assert args["room"] == "Kitchen"
    assert args["client_id"] == "custom-id"


def test_store_true_flags(monkeypatch):
    _set_argv(
        monkeypatch,
        "--host",
        "broker.local",
        "--use-pms5003",
        "--remove-config",
    )
    args = main.parse_args()
    assert args["use_pms5003"] is True
    assert args["remove_config"] is True
