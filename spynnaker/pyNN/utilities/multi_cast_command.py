

class MultiCastCommand(object):
    """command object used in conjunction with multicast source and
    vertex_requires_multi_cast_source_constraint
    """

    def __init__(self, time, key, payload=None, repeat=5, delay=100):
        self._time = time
        self._key = key
        self._payload = payload
        self._repeat = repeat
        self._delay = delay

    @property
    def time(self):
        return self._time

    @property
    def key(self):
        return self._key

    @property
    def payload(self):
        return self._payload

    @property
    def repeat(self):
        return self._repeat

    @property
    def delay(self):
        return self._delay
