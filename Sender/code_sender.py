import board
from python.pool_temp.system_lib import Sensor, Communicator
import time
from digitalio import DigitalInOut, Direction
from board import D13, RFM9X_CS, RFM9X_RST

SENSOR_ONE_ID = bytes([40, 170, 73, 65, 64, 20, 1, 64])
SENSOR_TWO_ID = bytes([40, 170, 188, 49, 64, 20, 1, 156])

TRANSMISSION_INTERVAL = 2  # secs


def main():
    sensor = Sensor(board.D5, SENSOR_ONE_ID, SENSOR_TWO_ID)
    communicator = Communicator(cs=RFM9X_CS, rst=RFM9X_RST, tx_power=23)
    led = DigitalInOut(D13)
    led.direction = Direction.OUTPUT
    import gc
    while True:
        led.value = True
        data = sensor.pack()
        communicator.send_packed(data)
        led.value = False

        print("Free Memory", gc.mem_free())
        print("Packed Data", data)
        print("Uptime", time.monotonic())
        print()
        gc.collect()
        time.sleep(TRANSMISSION_INTERVAL)


while True:
    try:
        main()

    except Exception as e:
        print(e)
        time.sleep(5)
