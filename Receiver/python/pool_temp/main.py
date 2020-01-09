import argparse
import json
import board

from sanic import Sanic, response
from pool_temp.system_lib import Communicator

app = Sanic(name="PoolTemp")


class Receiver(object):
    def __init__(self, timeout=None, recurring=False):
        self.recurring = recurring
        self.communicator = Communicator(cs=board.CE1, rst=board.D25)
        self.timeout = timeout or 10
        self.cached = {}

    def get_raw(self):
        data = self.communicator.recv_packed(self.timeout)
        self.cached = data if data else self.cached
        return data

    def get_dict(self):
        data = self.get_raw()
        if data:
            data["sensors"] = {":".join([str(seg) for seg in sensor_id]): value for (sensor_id, value) in
                               data["sensors"].items()}
        return data

    def get_json(self):
        return json.dumps(self.get_dict())

    def yield_json(self):
        if not self.recurring:
            yield self.get_json()
            return
        while True:
            yield self.get_json()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--recurring", action="store_true")
    parser.add_argument("-t", "--timeout", type=int)
    parser.add_argument("-s", "--server", action="store_true")
    args = parser.parse_args()

    r = Receiver(args.timeout, args.recurring)

    if args.server:
        @app.route("/")
        def root(request):
            return response.json(r.get_dict())

        @app.route("/cache")
        def cache(request):
            return response.json(r.cached)

        app.run(host="0.0.0.0", port=8000)
    else:
        for message in r.yield_json():
            if message:
                print(message)


if __name__ == '__main__':
    main()
