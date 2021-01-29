from .rate_source_array_vertex import RateSourceArrayVertex
from spynnaker.pyNN.models.common import SimplePopulationSettable
from spinn_front_end_common.abstract_models import AbstractChangableAfterRun
from spinn_utilities.overrides import overrides

class RateSourceArrayPartition(SimplePopulationSettable, AbstractChangableAfterRun):

    __slots__ = [
        "__vertices",
        "__n_atoms",
        "__partitions"]

    def __init__(self, n_neurons, rate_times, rate_values,
        constraints, label, max_atoms, rate_source_array, looping, partitions):

        self.__n_atoms = n_neurons
        self.__vertices = list()
        self.__partitions = partitions

        for i in range(self.__partitions):
            self.__vertices.append(RateSourceArrayVertex(
                self.__n_atoms, rate_times, rate_values, constraints,
                label+str(i), max_atoms, rate_source_array, looping))

    @property
    def n_atoms(self):
        return self.__n_atoms

    @property
    def out_vertices(self):
        return self.__vertices

    @overrides(SimplePopulationSettable.set_value)
    def set_value(self, key, value):
        SimplePopulationSettable.set_value(self, key, value)
        self.__change_requires_neuron_parameters_reload = True

    @property
    @overrides(AbstractChangableAfterRun.requires_mapping)
    def requires_mapping(self):
        return self.__vertices[0].requires_mapping

    @overrides(AbstractChangableAfterRun.mark_no_changes)
    def mark_no_changes(self):
        for i in range(self.__partitions):
            self.__vertices[i].requires_mapping = False