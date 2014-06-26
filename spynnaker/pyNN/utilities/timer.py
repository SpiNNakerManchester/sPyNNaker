from __future__ import print_function
import datetime
import sys


class Timer:

    def __init__(self):
        self._start_time = None

    def start_timing(self):
        self._start_time = datetime.datetime.now()
        print("started timer", file=sys.stderr)

    def take_sample(self):
        time_now = datetime.datetime.now()
        diff = time_now - self._start_time
        print("the difference in time between start and "
              "sample is {}".format(diff), file=sys.stderr)
        return diff