class MaxRowInfo(object):
    """ Information about the maximums for rows in a synaptic matrix.
    """

    __slots__ = [
        "__undelayed_max_n_synapses",
        "__delayed_max_n_synapses",
        "__undelayed_max_bytes",
        "__delayed_max_bytes",
        "__undelayed_max_words",
        "__delayed_max_words",
    ]

    def __init__(
            self, undelayed_max_n_synapses, delayed_max_n_synapses,
            undelayed_max_bytes, delayed_max_bytes,
            undelayed_max_words, delayed_max_words):
        self.__undelayed_max_n_synapses = undelayed_max_n_synapses
        self.__delayed_max_n_synapses = delayed_max_n_synapses
        self.__undelayed_max_bytes = undelayed_max_bytes
        self.__delayed_max_bytes = delayed_max_bytes
        self.__undelayed_max_words = undelayed_max_words
        self.__delayed_max_words = delayed_max_words

    @property
    def undelayed_max_n_synapses(self):
        return self.__undelayed_max_n_synapses

    @property
    def delayed_max_n_synapses(self):
        return self.__delayed_max_n_synapses

    @property
    def undelayed_max_bytes(self):
        return self.__undelayed_max_bytes

    @property
    def delayed_max_bytes(self):
        return self.__delayed_max_bytes

    @property
    def undelayed_max_words(self):
        return self.__undelayed_max_words

    @property
    def delayed_max_words(self):
        return self.__delayed_max_words
