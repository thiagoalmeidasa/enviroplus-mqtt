import argparse
import sys
import time
from subprocess import check_output

import ST7735
from fonts.ttf import RobotoMedium as UserFont
from PIL import Image, ImageDraw, ImageFont

from logger import EnvLogger


# Get Raspberry Pi serial number to use as ID
def get_serial_number():
    with open("/proc/cpuinfo", "r") as f:
        for line in f:
            if line[0:6] == "Serial":
                return line.split(":")[1].strip()


def parse_args():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("-h",
                    "--host",
                    required=True,
                    help="the MQTT host to connect to")
    ap.add_argument("-p",
                    "--port",
                    type=int,
                    default=1883,
                    help="the port on the MQTT host to connect to")
    ap.add_argument("-U",
                    "--username",
                    default=None,
                    help="the MQTT username to connect with")
    ap.add_argument("-P",
                    "--password",
                    default=None,
                    help="the password to connect with")
    ap.add_argument(
        "--prefix",
        default="",
        help=
        "the topic prefix to use when publishing readings, i.e. 'lounge/enviroplus'"
    )
    ap.add_argument("--room",
                    default="LivingRoom",
                    help="the room covered by this sensor, i.e. 'lounge'")
    ap.add_argument("--client-id",
                    default=get_serial_number(),
                    help="the MQTT client identifier to use when connecting")
    ap.add_argument("--interval",
                    type=int,
                    default=5,
                    help="the duration in seconds between updates")
    ap.add_argument(
        "--delay",
        type=int,
        default=15,
        help=
        "the duration in seconds to allow the sensors to stabilise before starting to publish readings"
    )
    ap.add_argument(
        "--use-pms5003",
        action="store_true",
        help="if set, PM readings will be taken from the PMS5003 sensor")
    #ap.add_argument("--config", action="store_true", help="if set, will create config topics")
    ap.add_argument("--remove-config",
                    action="store_true",
                    help="if set, will remove config topics")
    ap.add_argument("--help",
                    action="help",
                    help="print this help message and exit")
    return vars(ap.parse_args())


def main():
    args = parse_args()

    # Initialise the logger
    logger = EnvLogger(client_id=args["client_id"],
                       host=args["host"],
                       port=args["port"],
                       username=args["username"],
                       password=args["password"],
                       room=args["room"],
                       prefix=args["prefix"],
                       use_pms5003=args["use_pms5003"],
                       num_samples=args["interval"])

    # Create LCD instance
    disp = ST7735.ST7735(port=0,
                         cs=1,
                         dc=9,
                         backlight=12,
                         rotation=270,
                         spi_speed_hz=10000000)


    if args["remove_config"]:
        logger.remove_sensor_config()
        logger.destroy()
        sys.exit("Configs removed")

    # Take readings without publishing them for the specified delay period,
    # to allow the sensors time to warm up and stabilise
    publish_start_time = time.time() + args["delay"]
    while time.time() < publish_start_time:
        logger.update(publish_readings=False)
        time.sleep(1)

    # Start taking readings and publishing them at the specified interval
    next_sample_time = time.time()
    next_publish_time = time.time() + args["interval"]

    while True:
        if logger.connection_error is not None:
            sys.exit(
                f"Connecting to the MQTT server failed: {logger.connection_error}"
            )

        display_status(disp, args["host"])

        should_publish = time.time() >= next_publish_time
        if should_publish:
            next_publish_time += args["interval"]
            logger.sensor_config()
        logger.update(publish_readings=should_publish)

        next_sample_time += 1
        sleep_duration = max(next_sample_time - time.time(), 0)
        time.sleep(sleep_duration)

    logger.destroy()


# Check for Wi-Fi connection
def wifi_status():
    try:
        output = check_output(['iwgetid', '-s']).rstrip()
        return output
    except Exception:
        return False

def display_status(disp, mqtt_broker):

    wifi_ssid = wifi_status() if wifi_status() else "disconnected"

    # Width and height to calculate text position
    WIDTH = disp.width
    HEIGHT = disp.height

    # Text settings
    font_size = 12
    font = ImageFont.truetype(UserFont, font_size)

    device_serial_number = get_serial_number()

    text_colour = (255, 255, 255)
    back_colour = (85, 15, 15) if wifi_ssid == "disconnected" else (0, 170, 170)

    message = f"Wi-Fi: {wifi_ssid}\nMQTT: {mqtt_broker}"


    img = Image.new("RGB", (WIDTH, HEIGHT), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    size_x, size_y = draw.textsize(message, font)
    x = (WIDTH - size_x) / 2
    y = (HEIGHT / 2) - (size_y / 2)
    draw.rectangle((0, 0, 160, 80), back_colour)
    draw.text((x, y), message, font=font, fill=text_colour)
    disp.display(img)

if __name__ == "__main__":
    main()

