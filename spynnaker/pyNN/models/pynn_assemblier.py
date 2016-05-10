
class Assemblier(object):

    def  __init__(self, populations, label, spinnaker):
        self._populations = populations
        self._label = label
        self._spinnaker = spinnaker

    def __add__(self, other):
        pass

    def __getitem__(self, index):
        pass

    def __iadd__(self, other):
        pass

    def __iter__(self):
        pass

    def __len__(self):
        pass

    def describe(self, template='assembly_default.txt', engine='default'):
        pass

    def get_gsyn(self, gather=True, compatible_output=True):
        pass

    def get_population(self, label):
        pass

    def get_spike_counts(self, gather=True):
        pass

    def get_v(self, gather=True, compatible_output=True):
        pass

    def id_to_index(self, id):
        pass

    def initialize(self, variable, value):
        pass

    def inject(self, current_source):
        pass

    def meanSpikeCount(self, gather=True):
        pass

    def printSpikes(self, file, gather=True, compatible_output=True):
        pass

    def print_gsyn(self, file, gather=True, compatible_output=True):
        pass

    def print_v(self, file, gather=True, compatible_output=True):
        pass

    def record(self, to_file=True):
        pass

    def record_gsyn(self, to_file=True):
        pass

    def record_v(self, to_file=True):
        pass

    def save_positions(self, file):
        pass
