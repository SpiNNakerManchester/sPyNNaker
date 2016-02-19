
# front end common imports
from pacman.utilities.utility_objs.progress_bar import ProgressBar
from spinn_front_end_common.abstract_models.\
    abstract_data_specable_vertex import \
    AbstractDataSpecableVertex
from spinn_front_end_common.utilities import exceptions as common_exceptions

# spynnaker imports
from spynnaker.pyNN.models.abstract_models.\
    abstract_has_first_machine_time_step import \
    AbstractHasFirstMachineTimeStep
from spynnaker.pyNN.models.common.abstract_gsyn_recordable import \
    AbstractGSynRecordable
from spynnaker.pyNN.models.common.abstract_spike_recordable import \
    AbstractSpikeRecordable
from spynnaker.pyNN.models.common.abstract_v_recordable import \
    AbstractVRecordable

# general imports
import math
import logging

logger = logging.getLogger(__name__)


class SpyNNakerRuntimeUpdator(object):
    """ updates the commuilative ran time
    """

    def __call__(self, run_time, partitionable_graph, current_run_ms,
                 machine_time_step, ran_token=None):

        if ran_token is not None and not ran_token:
            raise common_exceptions.ConfigurationException(
                "This model can only run once the application has ran")

        progress_bar = ProgressBar(len(partitionable_graph.vertices),
                                   "Updating python vertices runtime")

        # calculate number of machine time steps
        total_run_time = self._calculate_number_of_machine_time_steps(
            run_time, current_run_ms, machine_time_step, partitionable_graph)

        # Calculate the first machine time step to start from and set this
        # where necessary
        first_machine_time_step = int(math.ceil(
            (current_run_ms * 1000.0) / machine_time_step))
        for vertex in partitionable_graph.vertices:
            if isinstance(vertex, AbstractHasFirstMachineTimeStep):
                vertex.set_first_machine_time_step(first_machine_time_step)
            progress_bar.update()
        progress_bar.end()

    @staticmethod
    def _calculate_number_of_machine_time_steps(
            next_run_time, current_run_ms, machine_time_step,
            partitionable_graph):
        total_run_time = next_run_time
        if next_run_time is not None:
            total_run_time += current_run_ms
            machine_time_steps = (
                (total_run_time * 1000.0) / machine_time_step)
            if machine_time_steps != int(machine_time_steps):
                logger.warn(
                    "The runtime and machine time step combination result in "
                    "a fractional number of machine time steps")
            no_machine_time_steps = int(math.ceil(machine_time_steps))
        else:
            no_machine_time_steps = None
            for vertex in partitionable_graph.vertices:
                if ((isinstance(vertex, AbstractSpikeRecordable) and
                        vertex.is_recording_spikes()) or
                        (isinstance(vertex, AbstractVRecordable) and
                            vertex.is_recording_v()) or
                        (isinstance(vertex, AbstractGSynRecordable) and
                            vertex.is_recording_gsyn)):
                    raise common_exceptions.ConfigurationException(
                        "recording a population when set to infinite runtime "
                        "is not currently supported")
        for vertex in partitionable_graph.vertices:
            if isinstance(vertex, AbstractDataSpecableVertex):
                vertex.set_no_machine_time_steps(no_machine_time_steps)
        return total_run_time
