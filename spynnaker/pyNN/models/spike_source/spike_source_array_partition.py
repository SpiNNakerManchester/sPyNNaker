from .spike_source_array_vertex import SpikeSourceArrayVertex

# Hard-coded here, but to be moved outside as param
N_PARTITIONS = 2

class SpikeSourceArrayPartition():
    __slots__ = [
        "_vertices",
        "_n_atoms"]

    def __init__(self, n_neurons, spike_times, constraints, label, max_atoms):

        self._n_atoms = n_neurons
        self._vertices = list()

        for i in range(N_PARTITIONS):
            self._vertices.append(SpikeSourceArrayVertex(
                n_neurons/N_PARTITIONS, spike_times, constraints, label, max_atoms, self))