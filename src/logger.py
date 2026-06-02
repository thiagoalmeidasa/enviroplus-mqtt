import collections
import json
import threading
import traceback
from subprocess import PIPE, Popen, check_output

import paho.mqtt.client as mqtt
import ST7735
from fonts.ttf import RobotoMedium as UserFont
from PIL import Image, ImageDraw, ImageFont

try:
    # Transitional fix for breaking change in LTR559
    from ltr559 import LTR559
    ltr559 = LTR559()
except ImportError:
    import ltr559

from bme280 import BME280
from enviroplus import gas
from pms5003 import PMS5003


class EnvLogger:

    def __init__(self, client_id, host, port, username, password, prefix,
                 use_pms5003, room, num_samples):
        self.bme280 = BME280()

        self.client_id = client_id
        self.prefix = prefix
        self.room = room
        self.mqtt_broker = host

        self.connection_error = None
        self.client = mqtt.Client(client_id=client_id)
        self.client.on_connect = self.__on_connect
        self.client.username_pw_set(username, password)
        self.client.connect(host, port)
        self.client.loop_start()

        self.samples = collections.deque(maxlen=num_samples)
        self.latest_pms_readings = {}

        self.use_pms5003 = use_pms5003

        if self.use_pms5003:
            self.pm_thread = threading.Thread(
                target=self.__read_pms_continuously)
            self.pm_thread.daemon = True
            self.pm_thread.start()

        # Create LCD instance
        self.disp = ST7735.ST7735(port=0,
                                  cs=1,
                                  dc=9,
                                  backlight=12,
                                  rotation=270,
                                  spi_speed_hz=10000000)

    def __on_connect(self, _client, _userdata, _flags, rc):
        errors = {
            1: "incorrect MQTT protocol version",
            2: "invalid MQTT client identifier",
            3: "server unavailable",
            4: "bad username or password",
            5: "connection refused"
        }

        if rc > 0:
            self.connection_error = errors.get(rc, "unknown error")

    def __read_pms_continuously(self):
        """Continuously reads from the PMS5003 sensor and stores the most recent values
        in `self.latest_pms_readings` as they become available.

        If the sensor is not polled continously then readings are buffered on the PMS5003,
        and over time a significant delay is introduced between changes in PM levels and
        the corresponding change in reported levels."""

        pms = PMS5003()
        while True:
            try:
                pm_data = pms.read()
                self.latest_pms_readings = {
                    "pm10": pm_data.pm_ug_per_m3(
                        1.0),  #, atmospheric_environment=True),
                    "pm25": pm_data.pm_ug_per_m3(
                        2.5),  #, atmospheric_environment=True),
                    "pm100": pm_data.pm_ug_per_m3(
                        10),  #, atmospheric_environment=True),
                }
            except Exception:
                print("Failed to read from PMS5003. Resetting sensor.")
                traceback.print_exc()
                pms.reset()

    def remove_sensor_config(self):
        """
        Remove previous config topic cretead for each sensor
        """
        print("removed")
        sensors = [
            "proximity",
            "lux",
            "temperature",
            "pressure",
            "humidity",
            "oxidising",
            "reducing",
            "nh3",
            "pm10",
            "pm25",
            "pm100",
        ]

        for sensor in sensors:
            sensor_topic_config = f"sensor/{self.room}/{sensor}/config"
            self.publish(sensor_topic_config, '')

    def sensor_config(self):
        """
        Create config topic for each sensor
        """
        # homeassistant/sensor/livingRoom/temperature/config
        # homeassistant/sensor/livingRoom/temperature/state
        # homeassistant/livingroom/enviroplus/state
        sensors = {
            "proximity": {
                "unit_of_measurement": "cm",
                "value_template": "{{ value_json }}"
            },
            "lux": {
                "device_class": "illuminance",
                "unit_of_measurement": "lx",
                "value_template": "{{ value_json }}",
                "icon": "mdi:weather-sunny"
            },
            "temperature": {
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "value_template": "{{ value_json }}",
                "icon": "mdi:thermometer"
            },
            "pressure": {
                "device_class": "pressure",
                "unit_of_measurement": "hPa",
                "value_template": "{{ value_json }}",
                "icon": "mdi:arrow-down-bold"
            },
            "humidity": {
                "device_class": "humidity",
                "unit_of_measurement": "%",
                "value_template": "{{ value_json }}",
                "icon": "mdi:water-percent"
            },
            "oxidising": {
                "unit_of_measurement": "no2",
                "value_template": "{{ value_json }}",
                "icon": "mdi:thought-bubble"
            },
            "reducing": {
                "unit_of_measurement": "CO",
                "value_template": "{{ value_json }}",
                "icon": "mdi:thought-bubble"
            },
            "nh3": {
                "unit_of_measurement": "nh3",
                "value_template": "{{ value_json }}",
                "icon": "mdi:thought-bubble"
            },
        }

        if self.use_pms5003:
            sensors["pm10"] = {
                "unit_of_measurement": "ug/m3",
                "value_template": "{{ value_json }}",
                "icon": "mdi:thought-bubble-outline",
            }
            sensors["pm25"] = {
                "unit_of_measurement": "ug/m3",
                "value_template": "{{ value_json }}",
                "icon": "mdi:thought-bubble-outline",
            }
            sensors["pm100"] = {
                "unit_of_measurement": "ug/m3",
                "value_template": "{{ value_json }}",
                "icon": "mdi:thought-bubble-outline",
            }
        try:
            for sensor in sensors:
                sensors[sensor]["name"] = f"{self.room} {sensor.capitalize()}"
                sensors[sensor][
                    "state_topic"] = f"{self.prefix}/sensor/{self.room}/{sensor}/state"
                sensors[sensor]["unique_id"] = f"{sensor}-{self.client_id}"

                sensor_topic_config = f"sensor/{self.room}/{sensor}/config"
                self.publish(sensor_topic_config, json.dumps(sensors[sensor]))
            print("Configs added")
        except Exception:
            print("Failed to add configs.")
            traceback.print_exc()

    # Get CPU temperature to use for compensation
    def get_cpu_temperature(self):
        process = Popen(["vcgencmd", "measure_temp"],
                        stdout=PIPE,
                        universal_newlines=True)
        output, _ = process.communicate()
        return float(output[output.index("=") + 1:output.rindex("'")])

    def take_readings(self):
        # Tuning factor for compensation. Decrease this number to adjust the
        # temperature down, and increase to adjust up
        temp_comp_factor = 1.7
        cpu_temp = self.get_cpu_temperature()
        raw_temp = self.bme280.get_temperature()  # float
        comp_temp = raw_temp - ((cpu_temp - raw_temp) / temp_comp_factor)

        hum_comp_factor = 1.3

        gas_data = gas.read_all()
        readings = {
            "proximity": ltr559.get_proximity(),
            "lux": int(ltr559.get_lux()),
            "temperature": round(comp_temp, 1),
            "pressure": round(int(self.bme280.get_pressure() * 100),
                              -1),  # round to nearest 10
            "humidity":
            round(int(self.bme280.get_humidity() * hum_comp_factor), 1),
            "oxidising": int(gas_data.oxidising / 1000),
            "reducing": int(gas_data.reducing / 1000),
            "nh3": int(gas_data.nh3 / 1000),
        }

        readings.update(self.latest_pms_readings)

        return readings

    def publish(self, topic, value):
        topic = self.prefix.strip("/") + "/" + topic
        self.client.publish(topic, str(value))

    def update(self, publish_readings=True):
        readings = self.take_readings()
        self.samples.append(readings)
        if publish_readings:

            display_status(self.disp, self.mqtt_broker, readings)
            for topic in self.samples[0]:
                value_sum = sum([d[topic] for d in self.samples])
                value_avg = round(value_sum / len(self.samples), 1)
                #print(topic, value_avg)
                self.publish(f"sensor/{self.room}/{topic}/state", value_avg)

    def destroy(self):
        self.client.disconnect()
        self.client.loop_stop()


# Check for Wi-Fi connection
def wifi_status():
    try:
        output = check_output(['iwgetid', '-s'], text=True).rstrip()
        return output
    except Exception:
        return False


def display_status(disp, mqtt_broker, readings):

    wifi_ssid = wifi_status() if wifi_status() else "disconnected"

    # Width and height to calculate text position
    WIDTH = disp.width
    HEIGHT = disp.height

    # Text settings
    font_size = 12
    font = ImageFont.truetype(UserFont, font_size)

    text_colour = (255, 255, 255)
    back_colour = (85, 15, 15) if wifi_ssid == "disconnected" else (0, 170,
                                                                    170)

    message = f"Wi-Fi: {wifi_ssid}\nMQTT: {mqtt_broker}\nHumidity: {readings['humidity']}"

    img = Image.new("RGB", (WIDTH, HEIGHT), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    size_x, size_y = draw.textsize(message, font)
    x = (WIDTH - size_x) / 2
    y = (HEIGHT / 2) - (size_y / 2)
    draw.rectangle((0, 0, 160, 80), back_colour)
    draw.text((x, y), message, font=font, fill=text_colour)
    disp.display(img)
