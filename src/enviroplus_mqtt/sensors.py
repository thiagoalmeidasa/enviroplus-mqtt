import threading
import traceback
from subprocess import PIPE, Popen

from bme280 import BME280
from enviroplus import gas
from pms5003 import PMS5003

try:
    # Newer LTR559 ships a class; older versions exposed a module-level API
    from ltr559 import LTR559

    ltr559 = LTR559()
except ImportError:
    import ltr559  # type: ignore[no-redef]


class SensorReader:
    """Reads BME280, LTR559, gas, and (optionally) PMS5003 sensors."""

    def __init__(self, use_pms5003: bool = False):
        self.bme280 = BME280()
        self.use_pms5003 = use_pms5003
        self.latest_pms_readings: dict = {}

        if self.use_pms5003:
            thread = threading.Thread(target=self._read_pms_continuously, daemon=True)
            thread.start()

    def get_cpu_temperature(self) -> float:
        process = Popen(
            ["vcgencmd", "measure_temp"],
            stdout=PIPE,
            universal_newlines=True,
        )
        output, _ = process.communicate()
        return float(output[output.index("=") + 1 : output.rindex("'")])

    def take_readings(self) -> dict:
        # Empirically tuned to cancel CPU-driven heat bias on the Enviro+
        # board. Lower => report cooler, higher => report warmer.
        temp_comp_factor = 1.7
        cpu_temp = self.get_cpu_temperature()
        raw_temp = self.bme280.get_temperature()
        comp_temp = raw_temp - ((cpu_temp - raw_temp) / temp_comp_factor)

        hum_comp_factor = 1.3
        gas_data = gas.read_all()

        readings = {
            "proximity": ltr559.get_proximity(),
            "lux": int(ltr559.get_lux()),
            "temperature": round(comp_temp, 1),
            "pressure": round(int(self.bme280.get_pressure() * 100), -1),
            "humidity": round(int(self.bme280.get_humidity() * hum_comp_factor), 1),
            "oxidising": int(gas_data.oxidising / 1000),
            "reducing": int(gas_data.reducing / 1000),
            "nh3": int(gas_data.nh3 / 1000),
        }
        readings.update(self.latest_pms_readings)
        return readings

    def _read_pms_continuously(self):
        """Poll PMS5003 in a background loop to keep latest_pms_readings fresh.

        Without continuous polling the sensor buffers samples on-device and a
        noticeable lag builds up between real PM-level changes and reported
        values.
        """
        pms = PMS5003()
        while True:
            try:
                pm_data = pms.read()
                self.latest_pms_readings = {
                    "pm10": pm_data.pm_ug_per_m3(1.0),
                    "pm25": pm_data.pm_ug_per_m3(2.5),
                    "pm100": pm_data.pm_ug_per_m3(10),
                }
            except Exception:
                print("Failed to read from PMS5003. Resetting sensor.")
                traceback.print_exc()
                pms.reset()
