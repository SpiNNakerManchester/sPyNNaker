from abc import ABCMeta, abstractmethod
from math import ceil
from six import add_metaclass
import logging

from spynnaker.pyNN.models.abstract_models.abstract_recordable_vertex \
    import AbstractRecordableVertex
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
                 machine_time_step, timescale_factor, spikes_per_second,
                 ring_buffer_sigma, weight_scale=1.0, constraints=None):

        AbstractRecordableVertex.__init__(self, machine_time_step, label)
        AbstractPopulationDataSpec.__init__(
            self, binary, n_neurons, label, constraints,
            machine_time_step=machine_time_step,
            timescale_factor=timescale_factor,
            max_atoms_per_core=max_atoms_per_core,
            spikes_per_second=spikes_per_second,
            ring_buffer_sigma=ring_buffer_sigma)
        self._n_params = n_params
        self._weight_scale = weight_scale

    @abstractmethod
    def is_population_vertex(self):
        pass

    @property
    def weight_scale(self):
        return self._weight_scale

    def get_spikes(self, txrx, placements, graph_mapper,
                   compatible_output=False):

        # Spike sources store spike vectors optimally
        # so calculate min words to represent
        out_spike_bytes_function = \
            lambda subvertex, subvertex_slice: int(ceil(
                subvertex_slice.n_atoms / 32.0)) * 4

        # Use standard behaviour to read spikes
        return self._get_spikes(
            graph_mapper=graph_mapper, placements=placements, transciever=txrx,
            compatible_output=compatible_output,
            sub_vertex_out_spike_bytes_function=out_spike_bytes_function,
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

    def __str__(self):
        return "{} with {} atoms".format(self._label, self.n_atoms)

    def __repr__(self):
        return self.__str__()
