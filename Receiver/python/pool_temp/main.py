import argparse
import json
import statistics

import board
import datetime
import time

from sanic import Sanic, response
from sanic_cors import CORS, cross_origin
from pool_temp.system_lib import Communicator
import threading

app = Sanic(__name__)
CORS(app)


class MaxStack:
    def __init__(self, max):
        self.stack = []
        self.max = max

    def push(self, val):
        self.stack.append(val)
        if len(self.stack) > self.max:
            self.stack.pop(0)

    def get(self):
        return self.stack


class Receiver(object):
    def __init__(self, timeout=None, recurring=False, always_listening=False):
        self.recurring = recurring
        self.communicator = Communicator(cs=board.CE1, rst=board.D25)
        self.timeout = timeout or 10
        self.cached = {}
        self.stack = MaxStack(60)  # 15 minute history
        self.growth_interval = 15

        if always_listening:
            self.constant_update()

    def get_raw(self):
        data = self.communicator.recv_packed(self.timeout)
        self.cached = data if data else self.cached
        return data

    def get_growth(self, stack):
        try:
            avg = statistics.mean([(stack[i + 1] - stack[i]) for i in range(len(stack) - 1)])
            avg_hour = avg * 60 * 60 / self.growth_interval
            return round(avg_hour, 3)
        except statistics.StatisticsError:
            return -1

    def get_dict(self):
        data = self.get_raw()
        if data:
            data["sensors"] = {":".join([str(seg) for seg in sensor_id]): value for (sensor_id, value) in
                               data["sensors"].items()}
            data["time"] = {
                "readable": datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                "unix": datetime.datetime.now().timestamp()
            }
            data["growth"] = {
                "sample_size": len(self.stack.get()),
                "value": self.get_growth(self.stack.get())
            }
        return data

    def get_json(self):
        return json.dumps(self.get_dict())

    def yield_data(self):
        if not self.recurring:
            yield self.get_dict()
            return
        while True:
            res = self.get_dict()
            if res:
                yield res

    def constant_update(self):
        def update_cache(_self):
            while True:
                try:
                    for result in _self.yield_data():
                        _self.cached = result
                except Exception as e:
                    print(e)

        def growth_update(_self):
            while True:
                try:
                    _self.stack.push(_self.cached["sensors"]["40:170:188:49:64:20:1:156"])
                    time.sleep(_self.growth_interval)
                except Exception as e:
                    print(e)

        threading.Thread(target=update_cache, args=(self,)).start()
        threading.Thread(target=growth_update, args=(self,)).start()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--recurring", action="store_true")
    parser.add_argument("-t", "--timeout", type=int)
    parser.add_argument("-s", "--server", action="store_true")
    args = parser.parse_args()

    r = Receiver(args.timeout, args.recurring, args.server)

    if args.server:
        @app.route("/data", methods=["GET", "OPTIONS"])
        def root(request):
            return response.json(r.cached)

        @app.route("/no-cache")
        def cache(request):
            return response.json(r.get_dict())

        app.run(host="0.0.0.0", port=8000, debug=False, access_log=False)

        import time
        while True:
            time.sleep(2)
    else:
        for message in r.yield_data():
            if message:
                print(message)


if __name__ == '__main__':
    main()
