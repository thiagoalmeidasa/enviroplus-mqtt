from subprocess import CalledProcessError, TimeoutExpired, check_output


def get_serial_number() -> str | None:
    """Return the Raspberry Pi serial number from /proc/cpuinfo, or None."""
    with open("/proc/cpuinfo") as f:
        for line in f:
            if line[0:6] == "Serial":
                return line.split(":")[1].strip()
    return None


def wifi_status() -> str | None:
    """Return the current Wi-Fi SSID, or None if iwgetid is unavailable / fails."""
    try:
        return check_output(["iwgetid", "-r"], text=True, timeout=2).rstrip()
    except (FileNotFoundError, CalledProcessError, TimeoutExpired):
        return None
