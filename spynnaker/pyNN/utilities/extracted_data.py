try:
    from collections.abc import defaultdict
except ImportError:
    from collections import defaultdict


class ExtractedData(object):
    """ Data holder for all synaptic data being extracted in parallel.
    @Chimp: play here to hearts content.
    """
    __slots__ = ["__data"]

    def __init__(self):
        self.__data = defaultdict(dict)

    def get(self, projection, attribute):
        """ Allow getting data from a given projection and attribute

        :param projection: the projection data was extracted from
        :param attribute: the attribute to retrieve
        :return: the attribute data in a connection holder
        """
        if projection in self.__data:
            if attribute in self.__data[projection]:
                return self.__data[projection][attribute]
        return None

    def set(self, projection, attribute, data):
        """ Allow the addition of data from a projection and attribute.

        :param projection: the projection data was extracted from
        :param attribute: the attribute to store
        :param data: attribute data in a connection holder
        :rtype: None
        """
        self.__data[projection][attribute] = data
