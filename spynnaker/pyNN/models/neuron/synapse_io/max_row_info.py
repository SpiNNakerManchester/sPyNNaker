class MaxRowInfo(object):
    """ Information about the maximums for rows in a synaptic matrix
    """

    __slots__ = [
        "_undelayed_max_n_synapses",
        "_delayed_max_n_synapses",
        "_undelayed_max_bytes",
        "_delayed_max_bytes",
        "_undelayed_max_words",
        "_delayed_max_words",
    ]

    def __init__(
            self, undelayed_max_n_synapses, delayed_max_n_synapses,
            undelayed_max_bytes, delayed_max_bytes,
            undelayed_max_words, delayed_max_words):
        self._undelayed_max_n_synapses = undelayed_max_n_synapses
        self._delayed_max_n_synapses = delayed_max_n_synapses
        self._undelayed_max_bytes = undelayed_max_bytes
        self._delayed_max_bytes = delayed_max_bytes
        self._undelayed_max_words = undelayed_max_words
        self._delayed_max_words = delayed_max_words

    @property
    def undelayed_max_n_synapses(self):
        return self._undelayed_max_n_synapses

    @property
    def delayed_max_n_synapses(self):
        return self._delayed_max_n_synapses

    @property
    def undelayed_max_bytes(self):
        return self._undelayed_max_bytes

    @property
    def delayed_max_bytes(self):
        return self._delayed_max_bytes

    @property
    def undelayed_max_words(self):
        return self._undelayed_max_words

    @property
    def delayed_max_words(self):
        return self._delayed_max_words
