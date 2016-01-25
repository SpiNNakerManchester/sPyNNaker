# spynnaker imports
from pacman.model.resources.cpu_cycles_per_tick_resource import \
    CPUCyclesPerTickResource
from pacman.model.resources.dtcm_resource import DTCMResource
from pacman.model.resources.resource_container import ResourceContainer
from pacman.model.resources.sdram_resource import SDRAMResource
from spinn_front_end_common.interface.abstract_recordable_interface import \
    AbstractRecordableInterface
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.abstract_models.abstract_mappable \
    import AbstractMappable
from spynnaker.pyNN.models.common.simple_population_settable \
    import SimplePopulationSettable
from spynnaker.pyNN.models.common.eieio_spike_recorder \
    import EIEIOSpikeRecorder
from spynnaker.pyNN.models.common.abstract_spike_recordable \
    import AbstractSpikeRecordable
from spynnaker.pyNN.utilities.conf import config
from spynnaker.pyNN.models.abstract_models\
    .abstract_has_first_machine_time_step\
    import AbstractHasFirstMachineTimeStep


# spinn front end common imports
from spinn_front_end_common.abstract_models.\
    abstract_provides_outgoing_edge_constraints import \
    AbstractProvidesOutgoingEdgeConstraints
from spinn_front_end_common.utility_models.reverse_ip_tag_multi_cast_source \
    import ReverseIpTagMultiCastSource
from spinn_front_end_common.utilities import constants as \
    front_end_common_constants
from spinn_front_end_common.utilities import exceptions
from spinn_front_end_common.utility_models\
    .reverse_ip_tag_multicast_source_partitioned_vertex \
    import ReverseIPTagMulticastSourcePartitionedVertex


# general imports
import logging
import sys

logger = logging.getLogger(__name__)


class SpikeSourceArray(
        ReverseIpTagMultiCastSource, AbstractSpikeRecordable,
        SimplePopulationSettable, AbstractMappable,
        AbstractHasFirstMachineTimeStep):
    """ Model for play back of spikes
    """

    _model_based_max_atoms_per_core = sys.maxint

    def __init__(
            self, n_neurons, spike_times, machine_time_step, timescale_factor,
            port=None, tag=None, ip_address=None, board_address=None,
            max_on_chip_memory_usage_for_spikes_in_bytes=(
                constants.SPIKE_BUFFER_SIZE_BUFFERING_IN),
            space_before_notification=640,
            constraints=None, label="SpikeSourceArray",
            spike_recorder_buffer_size=(
                constants.EIEIO_SPIKE_BUFFER_SIZE_BUFFERING_OUT),
            buffer_size_before_receive=(
                constants.EIEIO_BUFFER_SIZE_BEFORE_RECEIVE),
            using_auto_pause_and_resume=False):
        self._ip_address = ip_address
        if ip_address is None:
            self._ip_address = config.get("Buffers", "receive_buffer_host")
        self._port = port
        if port is None:
            self._port = config.getint("Buffers", "receive_buffer_port")

        self._using_auto_pause_and_resume = using_auto_pause_and_resume

        ReverseIpTagMultiCastSource.__init__(
            self, n_keys=n_neurons, machine_time_step=machine_time_step,
            timescale_factor=timescale_factor, label=label,
            constraints=constraints,
            max_atoms_per_core=(SpikeSourceArray.
                                _model_based_max_atoms_per_core),
            board_address=board_address,
            receive_port=None, receive_sdp_port=None, receive_tag=None,
            virtual_key=None, prefix=None, prefix_type=None, check_keys=False,
            send_buffer_times=spike_times,
            send_buffer_max_space=max_on_chip_memory_usage_for_spikes_in_bytes,
            send_buffer_space_before_notify=space_before_notification,
            send_buffer_notification_ip_address=self._ip_address,
            send_buffer_notification_port=self._port,
            send_buffer_notification_tag=tag, extra_static_sdram=config.getint(
                "Recording", "extra_recording_data_for_static_sdram_usage"))
        AbstractSpikeRecordable.__init__(self)
        AbstractProvidesOutgoingEdgeConstraints.__init__(self)
        SimplePopulationSettable.__init__(self)
        AbstractMappable.__init__(self)
        AbstractHasFirstMachineTimeStep.__init__(self)

        # handle recording
        self._spike_recorder = EIEIOSpikeRecorder(machine_time_step)
        self._spike_recorder_buffer_size = spike_recorder_buffer_size
        self._buffer_size_before_receive = buffer_size_before_receive

        # Keep track of any previously generated buffers
        self._send_buffers = dict()
        self._spike_recording_region_size = None
        self._partitioned_vertices = list()
        self._partitioned_vertices_current_max_buffer_size = dict()

        # used for reset and rerun
        self._requires_mapping = True
        self._last_runtime_position = 0

        self._max_on_chip_memory_usage_for_spikes = \
            max_on_chip_memory_usage_for_spikes_in_bytes
        self._space_before_notification = space_before_notification
        if self._max_on_chip_memory_usage_for_spikes is None:
            self._max_on_chip_memory_usage_for_spikes = \
                front_end_common_constants.MAX_SIZE_OF_BUFFERED_REGION_ON_CHIP

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

    def get_number_of_mallocs_used_by_dsg(self, vertex_slice, in_edges):
        mallocs = \
            ReverseIpTagMultiCastSource.get_number_of_mallocs_used_by_dsg(
                self, vertex_slice, in_edges)
        if config.getboolean("SpecExecution", "specExecOnHost"):
            return 1
        else:
            return mallocs

    def get_runtime_sdram_usage_for_atoms(
            self, vertex_slice, partitionable_graph, no_machine_time_steps):
        """
        this should explore the spike table and give the size in sdram to
        store these spikes or the
        :param vertex_slice:
        :param partitionable_graph:
        :param no_machine_time_steps:
        :return:
        """
        # TODO I know this is wrong, but need some way to deduce size correctly
        # and annoyingly SSA just doesnt fit currently. buffered out makes pain
        return 1

    @property
    def requires_mapping(self):
        return self._requires_mapping

    def mark_no_changes(self):
        self._requires_mapping = False

    @property
    def spike_times(self):
        """ The spike times of the spike source array
        :return:
        """
        return self.send_buffer_times

    @spike_times.setter
    def spike_times(self, spike_times):
        """ Set the spike source array's spike times. Not an extend, but an\
            actual change
        :param spike_times:
        :return:
        """
        self.send_buffer_times = spike_times

    # @implements AbstractSpikeRecordable.is_recording_spikes
    def is_recording_spikes(self):
        return self._spike_recorder.record

    # @implements AbstractSpikeRecordable.set_recording_spikes
    def set_recording_spikes(self):
        self.enable_recording(
            self._ip_address, self._port, self._board_address,
            self._send_buffer_notification_tag,
            self._spike_recorder_buffer_size,
            self._buffer_size_before_receive)
        self._requires_mapping = not self._spike_recorder.record
        self._spike_recorder.record = True

    def get_spikes(self, placements, graph_mapper, buffer_manager):
        return self._spike_recorder.get_spikes(
            self.label, buffer_manager,
            (ReverseIPTagMulticastSourcePartitionedVertex.
             _REGIONS.RECORDING_BUFFER.value),
            (ReverseIPTagMulticastSourcePartitionedVertex.
             _REGIONS.RECORDING_BUFFER_STATE.value),
            placements, graph_mapper, self,
            lambda subvertex: subvertex.virtual_key)

    # @implements AbstractPartitionableVertex.get_resources_used_by_atoms
    def get_resources_used_by_atoms(self, vertex_slice, graph):
        """ Get the separate resource requirements for a range of atoms

        :param vertex_slice: the low value of atoms to calculate resources from
        :param graph: A reference to the graph containing this vertex.
        :type vertex_slice: pacman.model.graph_mapper.slice.Slice
        :return: a Resource container that contains a \
                    CPUCyclesPerTickResource, DTCMResource and SDRAMResource
        :rtype: ResourceContainer
        :raise None: this method does not raise any known exception
        """
        cpu_cycles = self.get_cpu_usage_for_atoms(vertex_slice, graph)
        dtcm_requirement = self.get_dtcm_usage_for_atoms(vertex_slice, graph)
        static_sdram_requirement = \
            self.get_static_sdram_usage_for_atoms(vertex_slice, graph)

        # set all to just static sdram for the time being
        all_sdram_usage = static_sdram_requirement

        # check runtime sdram usage if required
        if (not self._using_auto_pause_and_resume and
                isinstance(self, AbstractRecordableInterface)):
            runtime_sdram_usage = self.get_runtime_sdram_usage_for_atoms(
                vertex_slice, graph, self._no_machine_time_steps)
            all_sdram_usage += runtime_sdram_usage

        # noinspection PyTypeChecker
        resources = ResourceContainer(cpu=CPUCyclesPerTickResource(cpu_cycles),
                                      dtcm=DTCMResource(dtcm_requirement),
                                      sdram=SDRAMResource(all_sdram_usage))
        return resources

    @property
    def model_name(self):
        return "SpikeSourceArray"

    @staticmethod
    def set_model_max_atoms_per_core(new_value):
        SpikeSourceArray._model_based_max_atoms_per_core = new_value

    def set_first_machine_time_step(self, first_machine_time_step):
        self.first_machine_time_step = first_machine_time_step
