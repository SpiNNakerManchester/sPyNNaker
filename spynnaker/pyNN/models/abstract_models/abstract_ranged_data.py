from spinn_utilities.ranged.range_dictionary import RangeDictionary


class AbstractRangedData(object):

    __slots__ = ("_data", "_n_neurons")

    def __init__(self, n_neurons):
        self._n_neurons = n_neurons
        self._data = RangeDictionary(size=n_neurons)

    def initialize(self, variable, value):
        """
        Sets the variable to the new value

        This method differs to set_data only in the Exception message
        :param variable: variable to set
        :param value: new value
        :raise Exception if variable is not supported
        """
        if variable in self._data:
            self._data[variable] = value
        else:
            raise Exception("Vertex does not support initialisation of"
                            " parameter {}".format(variable))

    def set_data(self, variable, value):
        """
        Sets the variable to the new value

        This method differs to initialize only in the Exception message
        :param variable: variable to set
        :param value: new value
        :raise Exception if variable is not supported
        """
        if variable in self._data:
            self._data[variable] = value
        else:
            raise Exception("Model does not support data of type {}"
                            "".format(variable))
