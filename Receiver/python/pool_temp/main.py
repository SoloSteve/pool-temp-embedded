import argparse
import json
import sys

import board
from pool_temp.system_lib import Communicator


class Receiver(object):
    def __init__(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("-r", "--recurring", action="store_true")
        parser.add_argument("-t", "--timeout", type=int)
        self.args = parser.parse_args()

        self.communicator = Communicator(cs=board.CE1, rst=board.D25)

        self.timeout = self.args.timeout or 10

    def get_raw(self):
        return self.communicator.recv_packed(self.timeout)

    def get_json(self):
        data = self.communicator.recv_packed(self.timeout)
        if data:
            data["sensors"] = {":".join([str(seg) for seg in sensor_id]): value for (sensor_id, value) in data["sensors"].items()}
            return json.dumps(data)
        else:
            return None

    def yield_json(self, timeout=10):
        if not self.args.recurring:
            yield self.get_json()
            return
        while True:
            yield self.get_json()


def main():
    r = Receiver()
    for message in r.yield_json():
        if message:
            sys.stdout.write(message)


if __name__ == '__main__':
    main()
