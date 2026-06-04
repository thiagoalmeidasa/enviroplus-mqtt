def get_serial_number() -> str | None:
    """Return the Raspberry Pi serial number from /proc/cpuinfo, or None."""
    with open("/proc/cpuinfo") as f:
        for line in f:
            if line[0:6] == "Serial":
                return line.split(":")[1].strip()
    return None


def _query_active_ssid() -> str | None:
    """Read the active Wi-Fi SSID from NetworkManager over D-Bus.

    sdbus is imported lazily so this module stays importable on dev
    machines that don't install the `device` extra; unit tests
    monkeypatch this function directly rather than going through D-Bus.
    """
    import sdbus
    from sdbus_block.networkmanager import (
        AccessPoint,
        DeviceType,
        NetworkDeviceGeneric,
        NetworkDeviceWireless,
        NetworkManager,
    )

    sdbus.set_default_bus(sdbus.sd_bus_open_system())
    for device_path in NetworkManager().get_devices():
        generic = NetworkDeviceGeneric(device_path)
        if DeviceType(generic.device_type) != DeviceType.WIFI:
            continue
        wifi = NetworkDeviceWireless(device_path)
        ap_path = wifi.active_access_point
        if ap_path == "/":
            continue
        ssid: bytes = AccessPoint(ap_path).ssid
        if ssid:
            return ssid.decode("utf-8", "replace")
    return None


def wifi_status() -> str | None:
    """Return the active Wi-Fi SSID via NetworkManager, or None on failure."""
    try:
        return _query_active_ssid()
    except Exception:
        return None
