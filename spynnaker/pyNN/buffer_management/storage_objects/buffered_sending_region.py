import bisect


class BufferedSendingRegion(object):
    """ A set of keys to be sent at given timestamps for a given region of\
        data.  Note that keys must be added in timestamp order or else an\
        exception will be raised
    """

    def __init__(self):
        """

        :param buffer_size: The size of the buffer for this region
        :type buffer_size: int
        """

        # A dictionary of timestamp -> list of keys
        self._buffer = dict()

        # A list of timestamps
        self._timestamps = list()

        # The current position in the list of timestamps
        self._current_timestamp_pos = 0

        self._buffer_size = 0

    @property
    def buffer_size(self):
        return self._buffer_size

    @buffer_size.setter
    def buffer_size(self, buffer_size):
        self._buffer_size = buffer_size

    def add_key(self, timestamp, key):
        """ Add a key to be sent at a given time

        :param timestamp: The time at which the key is to be sent
        :type timestamp: int
        :param key: The key to send
        :type key: int
        """
        if timestamp not in self._buffer:
            bisect.insort(self._timestamps, timestamp)
            self._buffer[timestamp] = list()
        self._buffer[timestamp].append(key)

    def add_keys(self, timestamp, keys):
        """ Add a set of keys to be sent at the given time

        :param timestamp: The time at which the keys are to be sent
        :type timestamp: int
        :param keys: The keys to send
        :type keys: iterable of int
        """
        for key in keys:
            self.add_key(timestamp, key)

    @property
    def n_timestamps(self):
        """ The number of timestamps available

        :rtype: int
        """
        return len(self._timestamps)

    @property
    def timestamps(self):
        """ The timestamps for which there are keys

        :rtype: iterable of int
        """
        return self._timestamps

    def get_n_keys(self, timestamp):
        """ Get the number of keys for a given timestamp
        """
        if timestamp in self._buffer:
            return len(self._buffer[timestamp])
        return 0

    @property
    def is_next_timestamp(self):
        """ Determines if the region is empty
        :return: True if the region is empty, false otherwise
        :rtype: bool
        """
        return self._current_timestamp_pos < len(self._timestamps)

    @property
    def next_timestamp(self):
        """ The next timestamp of the data to be sent, or None if no more data

        :rtype: int or None
        """
        if self.is_next_timestamp:
            return self._timestamps[self._current_timestamp_pos]
        return None

    def is_next_key(self, timestamp):
        """ Determine if there is another key for the given timestamp

        :rtype: bool
        """
        if timestamp in self._buffer:
            return len(self._buffer[timestamp]) > 0
        return False

    @property
    def next_key(self):
        """ The next key to be sent

        :rtype: int
        """
        next_timestamp = self.next_timestamp
        keys = self._buffer[next_timestamp]
        key = keys.pop()
        if len(keys) == 0:
            del self._buffer[next_timestamp]
            self._current_timestamp_pos += 1
        return key
