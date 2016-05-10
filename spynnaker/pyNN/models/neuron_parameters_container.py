

class NeuronParametersContainer(object):

    def __init__(self):
        self._params = dict()
        self._params["record_spikes"] = False
        self._params["record_v"] = False
        self._params["record_gsyn"] = False

    def add_param(self, key, value):
        self._params[key] = value

    def get_param(self, key):
        return self._params[key]

    def __repr__(self):
        output = ""
        for key in self._params:
            output += "{}:{},".format(key, self._params[key])