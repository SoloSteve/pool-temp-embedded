import gc
import struct
import time
from adafruit_rfm9x import RFM9x


class Communicator:
    SYSTEM_FORMAT = 'dLL'  # uptime, mem alloc, mem free
    SYSTEM_FORMAT_LENGTH = 16

    def __init__(self, cs, rst, tx_power=13):
        from board import MOSI, MISO, SCK
        from busio import SPI
        from digitalio import DigitalInOut

        spi = SPI(SCK, MOSI=MOSI, MISO=MISO)
        cs = DigitalInOut(cs)
        reset = DigitalInOut(rst)

        self.rfm9x = RFM9x(spi, cs, reset, 433.0)
        self.rfm9x.tx_power = tx_power

    def send_temperatures(self, *temperatures):
        """
        :param tuple[float] temperatures:
        """
        packed_temperature = struct.pack("B" + "f" * len(temperatures), len(temperatures), *temperatures)
        self.rfm9x.send(packed_temperature)

    def receive_temperatures(self, timeout=0.5):
        """
        :param timeout:
        :return tuple[float] or None: temperatures
        """
        packed_temperature = self.rfm9x.receive(timeout)
        if packed_temperature is None:
            return None
        number_of_temperatures = struct.unpack('B', packed_temperature[0])[0]
        temperatures = struct.unpack("B" + "f" * number_of_temperatures, packed_temperature)
        return temperatures

    def send_packed(self, packed):
        packed = struct.pack(Communicator.SYSTEM_FORMAT, time.monotonic(), gc.mem_alloc(), gc.mem_free()) + packed
        self.rfm9x.send(packed)

    def recv_packed(self, timeout=0.5):
        packed = self.rfm9x.receive(timeout)
        if packed is None:
            return None
        system_info = struct.unpack(Communicator.SYSTEM_FORMAT, packed[:Communicator.SYSTEM_FORMAT_LENGTH])
        return {
            "uptime": system_info[0],
            "mem_alloc": system_info[1],
            "mem_free": system_info[2],
            "rssi": self.rfm9x.rssi,
            "sensors": Sensor.unpack(packed[Communicator.SYSTEM_FORMAT_LENGTH:])
        }


class Sensor:
    ID_TEMPERATURE_FORMAT = 'f' + 'B' + ('B' * 8)
    ID_TEMPERATURE_FORMAT_LENGTH = 13

    def __init__(self, pin, *sensor_ids):
        """
        :param microcontroller.pin pin: The OneWire Pin (board.D5).
        :param bytes sensor_ids: The sensors to init.
        :return dict: Key is bytes and value is the DS18X20 object.
        """
        from adafruit_ds18x20 import DS18X20
        from adafruit_onewire.bus import OneWireBus, OneWireAddress

        self.sensor_map = {}

        ow_bus = OneWireBus(pin)
        for sensor in sensor_ids:
            self.sensor_map[sensor] = DS18X20(ow_bus, OneWireAddress(sensor))

    def get_temperature(self, sensor_id):
        return self.sensor_map[sensor_id].temperature

    def pack(self):
        packed = []
        for key, value in self.sensor_map.items():
            sensor_pack = struct.pack(Sensor.ID_TEMPERATURE_FORMAT, value.temperature, value.resolution, *key)
            packed.extend(sensor_pack)
        return bytes(packed)

    @staticmethod
    def unpack(packed):
        if len(packed) % Sensor.ID_TEMPERATURE_FORMAT_LENGTH != 0:
            raise RuntimeError("Unable To Parse")

        sensor_map = {}
        num_of_sensors = len(packed) / Sensor.ID_TEMPERATURE_FORMAT_LENGTH

        for i in range(int(num_of_sensors)):
            single_packed = packed[
                            i * Sensor.ID_TEMPERATURE_FORMAT_LENGTH:i * Sensor.ID_TEMPERATURE_FORMAT_LENGTH + Sensor.ID_TEMPERATURE_FORMAT_LENGTH]
            single_unpacked = struct.unpack(Sensor.ID_TEMPERATURE_FORMAT, single_packed)
            sensor_map[single_unpacked[2:]] = single_unpacked[0]

        return sensor_map
