from collections import defaultdict


class ExtractedData(object):
    """ data holder for all synaptic data being extracted in parallel.
    @Chimp: play here to hearts content.
    """

    def __init__(self):
        self._data = defaultdict(dict)

    def get(self, projection, attribute):
        """ allows getting data from a given projection and attribute

        :param projection: the projection data was extracted from
        :param attribute: the attribute to retrieve
        :return: the attribute data in a connection holder
        """
        if projection in self._data:
            if attribute in self._data[projection]:
                return self._data[projection][attribute]

    def set(self, projection, attribute, data):
        """ allows the addition of data from a projection and attribute.

        :param projection: the projection data was extracted from
        :param attribute: the attribute to store
        :param data: attribute data in a connection holder
        :rtype: None
        """
        self._data[projection][attribute] = data
