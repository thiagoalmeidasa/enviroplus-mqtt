import argparse
import sys
import time

from enviroplus_mqtt.mqtt_logger import EnvLogger
from enviroplus_mqtt.system import get_serial_number


def parse_args() -> dict:
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument(
        "-h", "--host", required=True, help="the MQTT host to connect to"
    )
    ap.add_argument(
        "-p", "--port", type=int, default=1883, help="the port on the MQTT host to connect to"
    )
    ap.add_argument(
        "-U", "--username", default=None, help="the MQTT username to connect with"
    )
    ap.add_argument(
        "-P", "--password", default=None, help="the password to connect with"
    )
    ap.add_argument(
        "--prefix",
        default="",
        help="the topic prefix to use when publishing readings, i.e. 'lounge/enviroplus'",
    )
    ap.add_argument(
        "--room", default="LivingRoom", help="the room covered by this sensor, i.e. 'lounge'"
    )
    ap.add_argument(
        "--client-id",
        default=get_serial_number(),
        help="the MQTT client identifier to use when connecting",
    )
    ap.add_argument(
        "--interval", type=int, default=5, help="the duration in seconds between updates"
    )
    ap.add_argument(
        "--delay",
        type=int,
        default=15,
        help="the duration in seconds to allow the sensors to stabilise before starting to publish readings",
    )
    ap.add_argument(
        "--use-pms5003",
        action="store_true",
        help="if set, PM readings will be taken from the PMS5003 sensor",
    )
    ap.add_argument(
        "--remove-config",
        action="store_true",
        help="if set, will remove config topics",
    )
    ap.add_argument(
        "--help", action="help", help="print this help message and exit"
    )
    return vars(ap.parse_args())


def main() -> None:
    args = parse_args()

    logger = EnvLogger(
        client_id=args["client_id"],
        host=args["host"],
        port=args["port"],
        username=args["username"],
        password=args["password"],
        room=args["room"],
        prefix=args["prefix"],
        use_pms5003=args["use_pms5003"],
        num_samples=args["interval"],
    )

    if args["remove_config"]:
        logger.remove_sensor_config()
        logger.destroy()
        sys.exit("Configs removed")

    # Warm-up window: take readings without publishing so sensors can stabilise.
    publish_start_time = time.time() + args["delay"]
    while time.time() < publish_start_time:
        logger.update(publish_readings=False)
        time.sleep(1)

    next_sample_time = time.time()
    next_publish_time = time.time() + args["interval"]

    while True:
        if logger.connection_error is not None:
            sys.exit(f"Connecting to the MQTT server failed: {logger.connection_error}")

        should_publish = time.time() >= next_publish_time
        if should_publish:
            next_publish_time += args["interval"]
            logger.sensor_config()
        logger.update(publish_readings=should_publish)

        next_sample_time += 1
        sleep_duration = max(next_sample_time - time.time(), 0)
        time.sleep(sleep_duration)


if __name__ == "__main__":
    main()
