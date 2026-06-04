import collections
import json
import traceback

import paho.mqtt.client as mqtt

from enviroplus_mqtt.discovery import SENSOR_KEYS, build_sensor_configs
from enviroplus_mqtt.display import Display
from enviroplus_mqtt.sensors import SensorReader
from enviroplus_mqtt.system import wifi_status


class EnvLogger:
    def __init__(
        self,
        client_id,
        host,
        port,
        username,
        password,
        prefix,
        use_pms5003,
        room,
        num_samples,
    ):
        self.client_id = client_id
        self.prefix = prefix
        self.room = room
        self.mqtt_broker = host
        self.use_pms5003 = use_pms5003

        self.connection_error = None
        self.client = mqtt.Client(client_id=client_id)
        self.client.on_connect = self.__on_connect
        self.client.username_pw_set(username, password)
        self.client.connect(host, port)
        self.client.loop_start()

        self.samples: collections.deque = collections.deque(maxlen=num_samples)
        self.sensor_reader = SensorReader(use_pms5003=use_pms5003)
        self.display = Display()

    def __on_connect(self, _client, _userdata, _flags, rc):
        errors = {
            1: "incorrect MQTT protocol version",
            2: "invalid MQTT client identifier",
            3: "server unavailable",
            4: "bad username or password",
            5: "connection refused",
        }
        if rc > 0:
            self.connection_error = errors.get(rc, "unknown error")

    def publish(self, topic: str, value) -> None:
        topic = self.prefix.strip("/") + "/" + topic
        self.client.publish(topic, str(value))

    def sensor_config(self) -> None:
        """Publish Home Assistant discovery config for each enabled sensor."""
        try:
            configs = build_sensor_configs(
                room=self.room,
                prefix=self.prefix,
                client_id=self.client_id,
                use_pms5003=self.use_pms5003,
            )
            for sensor, payload in configs.items():
                self.publish(f"sensor/{self.room}/{sensor}/config", json.dumps(payload))
            print("Configs added")
        except Exception:
            print("Failed to add configs.")
            traceback.print_exc()

    def remove_sensor_config(self) -> None:
        """Remove previously-published HA discovery configs (publish empty payload)."""
        print("removed")
        for sensor in SENSOR_KEYS:
            self.publish(f"sensor/{self.room}/{sensor}/config", "")

    def update(self, publish_readings: bool = True) -> None:
        readings = self.sensor_reader.take_readings()
        self.samples.append(readings)
        if publish_readings:
            self.display.render_status(self.mqtt_broker, readings, wifi_status())
            for topic in self.samples[0]:
                value_sum = sum(d[topic] for d in self.samples)
                value_avg = round(value_sum / len(self.samples), 1)
                self.publish(f"sensor/{self.room}/{topic}/state", value_avg)

    def destroy(self) -> None:
        self.client.disconnect()
        self.client.loop_stop()
