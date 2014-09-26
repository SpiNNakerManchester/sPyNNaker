from abc import ABCMeta
from math import ceil
from six import add_metaclass
import logging

from pacman.model.constraints.\
    partitioner_same_size_as_vertex_constraint import \
    PartitionerSameSizeAsVertexConstraint

from spynnaker.pyNN.models.abstract_models.abstract_recordable_vertex import \
    AbstractRecordableVertex
from spynnaker.pyNN.models.abstract_models.abstract_population_data_spec \
    import AbstractPopulationDataSpec
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.utilities import constants


logger = logging.getLogger(__name__)


@add_metaclass(ABCMeta)
class AbstractPopulationVertex(AbstractRecordableVertex,
                               AbstractPopulationDataSpec):
    """
    Underlying AbstractConstrainedVertex model for Neural Populations.
    """

    def __init__(self, n_neurons, n_params, binary, label, max_atoms_per_core,
                 machine_time_step, constraints=None):

        AbstractRecordableVertex.__init__(self, machine_time_step, label)
        AbstractPopulationDataSpec.__init__(
            self, binary, n_neurons, label, constraints,
            machine_time_step=machine_time_step,
            max_atoms_per_core=max_atoms_per_core)
        self._delay_vertex = None
        self._n_params = n_params

    @property
    def delay_vertex(self):
        return self._delay_vertex

    @delay_vertex.setter
    def delay_vertex(self, delay_vertex):
        if self._delay_vertex is None:
            self._delay_vertex = delay_vertex
            self.add_constraint(
                PartitionerSameSizeAsVertexConstraint(self._delay_vertex))
        else:
            raise exceptions.ConfigurationException(
                "cannot set a vertex's delay vertex once its already been set")

    def get_spikes(self, txrx, placements, graph_mapper,
                   compatible_output=False):

        # Spike sources store spike vectors optimally
        # so calculate min words to represent
        sub_vertex_out_spike_bytes_function = \
            lambda subvertex, subvertex_slice: int(ceil(
                    subvertex_slice.n_atoms / 32.0)) * 4

        # Use standard behaviour to read spikes
        return self._get_spikes(
            graph_mapper=graph_mapper, placements=placements, transciever=txrx,
            compatible_output=compatible_output,
            sub_vertex_out_spike_bytes_function=
                sub_vertex_out_spike_bytes_function,
            spike_recording_region=
            constants.POPULATION_BASED_REGIONS.SPIKE_HISTORY.value)

    def get_v(self, has_ran, graph_mapper, placements,
              txrx, machine_time_step, compatible_output=False):
        """
        Return a 3-column numpy array containing cell ids, time, and Vm for
        recorded cells.

        :param bool gather:
            not used - inserted to match PyNN specs
        :param bool compatible_output:
            not used - inserted to match PyNN specs
        """
        logger.info("Getting v for {}".format(self.label))
        if not has_ran:
            raise exceptions.SpynnakerException(
                "The simulation has not yet ran, therefore v cannot be "
                "retrieved")
        return self.get_neuron_parameter(
            region=constants.POPULATION_BASED_REGIONS.POTENTIAL_HISTORY.value,
            compatible_output=compatible_output, has_ran=has_ran,
            machine_time_step=machine_time_step, graph_mapper=graph_mapper,
            placements=placements, txrx=txrx)

    def get_gsyn(self, has_ran, graph_mapper, placements, txrx,
                 machine_time_step, compatible_output=False):
        """
        Return a 3-column numpy array containing cell ids and synaptic
        conductances for recorded cells.

        :param compatible_output:
        """
        logger.info("Getting gsyn for {}".format(self.label))
        if not has_ran:
            raise exceptions.SpynnakerException(
                "The simulation has not yet ran, therefore gsyn cannot be "
                "retrieved")
        return self.get_neuron_parameter(
            region=constants.POPULATION_BASED_REGIONS.GSYN_HISTORY.value,
            compatible_output=compatible_output, has_ran=has_ran,
            machine_time_step=machine_time_step, graph_mapper=graph_mapper,
            placements=placements, txrx=txrx)

    def get_synaptic_data(self, presubvertex, pre_n_atoms, postsubvertex,
                          synapse_io):
        """
        helper method to add other data for get weights via syanptic manager
        """
        return self._get_synaptic_data(
            presubvertex, pre_n_atoms, postsubvertex,
            constants.POPULATION_BASED_REGIONS.MASTER_POP_TABLE.value,
            synapse_io,
            constants.POPULATION_BASED_REGIONS.SYNAPTIC_MATRIX.value)
