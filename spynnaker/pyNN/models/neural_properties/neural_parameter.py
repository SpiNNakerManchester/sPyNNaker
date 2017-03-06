

class NeuronParameter(object):
    def __init__(self, value, datatype, name):
        self._value = value
        self._datatype = datatype
        self._name = name

    def get_value(self):
        return self._value

    def get_dataspec_datatype(self):
        return self._datatype

    def get_name(self):
        return self._name
