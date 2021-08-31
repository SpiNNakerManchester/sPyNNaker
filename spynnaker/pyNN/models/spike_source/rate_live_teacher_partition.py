import math

from .rate_live_teacher_vertex import RateLiveTeacherVertex
from spynnaker.pyNN.models.common import SimplePopulationSettable
from spinn_front_end_common.abstract_models import AbstractChangableAfterRun
from spinn_utilities.overrides import overrides

from pacman.model.graphs.application.application_edge \
    import ApplicationEdge

from spynnaker.pyNN.utilities import constants


class RateLiveTeacherPartition(SimplePopulationSettable, AbstractChangableAfterRun):

    __slots__ = [
        "__vertices",
        "__n_atoms",
        "__partitions",
        "__refresh_rate",
        "__injector_vertex",
        "__atoms_per_partition",
        "__machine_vertices",
        "__dataset",
        "__dataset_len",
        "__epochs"]

    def __init__(self, sources, constraints, label, rate_live_teacher,
                 partitions, refresh_rate, dataset, dataset_len, epochs):

        self.__n_atoms = sources
        self.__vertices = list()
        self.__partitions = partitions
        self.__refresh_rate = refresh_rate
        self.__dataset = dataset
        self.__dataset_len = dataset_len
        self.__epochs = epochs

        self.__vertices.append(RateLiveTeacherVertex(
            sources, constraints, sources, label,
            rate_live_teacher, refresh_rate, dataset,
            dataset_len, epochs))

    @property
    def n_atoms(self):
        return self.__n_atoms

    @property
    def out_vertices(self):
        return self.__vertices

    @property
    def partitions(self):
        return self.__partitions

    def add_internal_edges_and_vertices(self, spinnaker_control):

        for v in self.__vertices:

            spinnaker_control.add_application_vertex(v)

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