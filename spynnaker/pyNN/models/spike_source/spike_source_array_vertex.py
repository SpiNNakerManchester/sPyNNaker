import logging
import sys

from spinn_utilities.overrides import overrides
from spinn_front_end_common.utility_models import ReverseIpTagMultiCastSource
from spinn_front_end_common.utilities.constants \
    import MAX_SIZE_OF_BUFFERED_REGION_ON_CHIP
from spinn_front_end_common.utilities import exceptions
from spinn_front_end_common.utilities import helpful_functions
from spinn_front_end_common.abstract_models import AbstractChangableAfterRun
from spinn_front_end_common.abstract_models.impl\
    import ProvidesKeyToAtomMappingImpl
from spinn_front_end_common.utilities import globals_variables

from spynnaker.pyNN.models.common import AbstractSpikeRecordable
from spynnaker.pyNN.models.common import EIEIOSpikeRecorder
from spynnaker.pyNN.models.common import SimplePopulationSettable
from spynnaker.pyNN.utilities import constants

logger = logging.getLogger(__name__)


class SpikeSourceArrayVertex(
        ReverseIpTagMultiCastSource, AbstractSpikeRecordable,
        SimplePopulationSettable, AbstractChangableAfterRun,
        ProvidesKeyToAtomMappingImpl):
    """ Model for play back of spikes
    """

    SPIKE_RECORDING_REGION_ID = 0

    def __init__(
            self, n_neurons, spike_times, port, tag,   ip_address,
            board_address, max_on_chip_memory_usage_for_spikes_in_bytes,
            space_before_notification, constraints, label,
            spike_recorder_buffer_size, buffer_size_before_receive,
            max_atoms_per_core, model):
        # pylint: disable=too-many-arguments
        self._model_name = "SpikeSourceArray"
        self._model = model

        config = globals_variables.get_simulator().config
        self._ip_address = ip_address
        if ip_address is None:
            self._ip_address = config.get("Buffers", "receive_buffer_host")
        self._port = port
        if port is None:
            self._port = helpful_functions.read_config_int(
                config, "Buffers", "receive_buffer_port")
        if spike_times is None:
            spike_times = []

        super(SpikeSourceArrayVertex, self).__init__(
            n_keys=n_neurons, label=label, constraints=constraints,
            max_atoms_per_core=max_atoms_per_core,
            board_address=board_address,
            receive_port=None, receive_tag=None,
            virtual_key=None, prefix=None, prefix_type=None, check_keys=False,
            send_buffer_times=spike_times,
            send_buffer_partition_id=constants.SPIKE_PARTITION_ID,
            send_buffer_max_space=max_on_chip_memory_usage_for_spikes_in_bytes,
            send_buffer_space_before_notify=space_before_notification,
            buffer_notification_ip_address=self._ip_address,
            buffer_notification_port=self._port,
            buffer_notification_tag=tag)

        # handle recording
        self._spike_recorder = EIEIOSpikeRecorder()
        self._spike_recorder_buffer_size = spike_recorder_buffer_size
        self._buffer_size_before_receive = buffer_size_before_receive

        # Keep track of any previously generated buffers
        self._send_buffers = dict()
        self._spike_recording_region_size = None
        self._machine_vertices = list()

        # used for reset and rerun
        self._requires_mapping = True
        self._last_runtime_position = 0

        self._max_on_chip_memory_usage_for_spikes = \
            max_on_chip_memory_usage_for_spikes_in_bytes
        self._space_before_notification = space_before_notification
        if self._max_on_chip_memory_usage_for_spikes is None:
            self._max_on_chip_memory_usage_for_spikes = \
                MAX_SIZE_OF_BUFFERED_REGION_ON_CHIP

        # check the values do not conflict with chip memory limit
        if self._max_on_chip_memory_usage_for_spikes < 0:
            raise exceptions.ConfigurationException(
                "The memory usage on chip is either beyond what is supportable"
                " on the spinnaker board being supported or you have requested"
                " a negative value for a memory usage. Please correct and"
                " try again")

        if (self._max_on_chip_memory_usage_for_spikes <
                self._space_before_notification):
            self._space_before_notification =\
                self._max_on_chip_memory_usage_for_spikes

    @property
    @overrides(AbstractChangableAfterRun.requires_mapping)
    def requires_mapping(self):
        return self._requires_mapping

    @overrides(AbstractChangableAfterRun.mark_no_changes)
    def mark_no_changes(self):
        self._requires_mapping = False

    @property
    def spike_times(self):
        """ The spike times of the spike source array
        """
        return self.send_buffer_times

    @spike_times.setter
    def spike_times(self, spike_times):
        """ Set the spike source array's spike times. Not an extend, but an\
            actual change

        """
        self.send_buffer_times = spike_times

    @overrides(AbstractSpikeRecordable.is_recording_spikes)
    def is_recording_spikes(self):
        return self._spike_recorder.record

    @overrides(AbstractSpikeRecordable.set_recording_spikes)
    def set_recording_spikes(
            self, new_state=True, sampling_interval=None, indexes=None):
        if sampling_interval is not None:
            logger.warning("Sampling interval currently not supported for "
                           "SpikeSourceArray so being ignored")
        if indexes is not None:
            logger.warning("Indexes currently not supported for "
                           "SpikeSourceArray so being ignored")
        self.enable_recording(
            self._spike_recorder_buffer_size,
            self._buffer_size_before_receive)
        self._requires_mapping = not self._spike_recorder.record
        self._spike_recorder.record = new_state

    @overrides(AbstractSpikeRecordable.get_spikes_sampling_interval)
    def get_spikes_sampling_interval(self):
        return globals_variables.get_simulator().machine_time_step

    @overrides(AbstractSpikeRecordable.get_spikes)
    def get_spikes(
            self, placements, graph_mapper, buffer_manager, machine_time_step):

        return self._spike_recorder.get_spikes(
            self.label, buffer_manager, 0,
            placements, graph_mapper, self,
            lambda vertex:
                vertex.virtual_key
                if vertex.virtual_key is not None
                else 0,
            machine_time_step)

    @overrides(AbstractSpikeRecordable.clear_spike_recording)
    def clear_spike_recording(self, buffer_manager, placements, graph_mapper):
        machine_vertices = graph_mapper.get_machine_vertices(self)
        for machine_vertex in machine_vertices:
            placement = placements.get_placement_of_vertex(machine_vertex)
            buffer_manager.clear_recorded_data(
                placement.x, placement.y, placement.p,
                SpikeSourceArrayVertex.SPIKE_RECORDING_REGION_ID)

    @staticmethod
    def set_model_max_atoms_per_core(new_value=sys.maxsize):
        SpikeSourceArrayVertex._model_based_max_atoms_per_core = new_value

    @staticmethod
    def get_max_atoms_per_core():
        return SpikeSourceArrayVertex._model_based_max_atoms_per_core

    def describe(self):
        """ Returns a human-readable description of the cell or synapse type.

        The output may be customised by specifying a different template\
        together with an associated template engine\
        (see ``pyNN.descriptions``).

        If template is None, then a dictionary containing the template\
        context will be returned.
        """

        parameters = dict()
        for parameter_name in self._model.default_parameters:
            parameters[parameter_name] = self.get_value(parameter_name)

        context = {
            "name": self._model_name,
            "default_parameters": self._model.default_parameters,
            "default_initial_values": self._model.default_parameters,
            "parameters": parameters,
        }
        return context
