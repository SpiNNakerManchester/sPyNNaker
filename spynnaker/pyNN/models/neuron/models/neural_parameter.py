

class NeuronParameter(object):

    def __init__(self, value, datatype):
        self._value = value
        self._datatype = datatype

    def get_value(self):
        return self._value

    def get_dataspec_datatype(self):
        return self._datatype
