from spynnaker.pyNN.models.common.abstract_gsyn_recordable import \
    AbstractGSynRecordable
from spynnaker.pyNN.models.common.abstract_spike_recordable import \
    AbstractSpikeRecordable
from spynnaker.pyNN.models.common.abstract_v_recordable import \
    AbstractVRecordable

import numpy
import logging

logger = logging.getLogger(__name__)


class SpyNNakerRecordingExtractor(object):
    """
    SpyNNakerRecordingExtractor: the extractor for application graph spynnaker
     supports for recording parameters
    """

    def __call__(
            self, partitionable_graph, transciever, placements,
            runtime_in_machine_time_steps, graph_mapper):

        logger.info(
            "Extracting recorded data from the PyNN application space for "
            "the last run")
        # search through populations for vertices which need to have their
        # recorded data extracted
        for vertex in partitionable_graph.vertices:
            if (isinstance(vertex, AbstractSpikeRecordable)
                    and vertex.is_recording_spikes()):
                vertex.get_spikes(
                    transciever, runtime_in_machine_time_steps, placements,
                    graph_mapper, False)
            if (isinstance(vertex, AbstractVRecordable)
                    and vertex.is_recording_v()):
                vertex.get_v(
                    transciever, runtime_in_machine_time_steps, placements,
                    graph_mapper, False)
            if (isinstance(vertex, AbstractGSynRecordable)
                    and vertex.is_recording_gsyn()):
                vertex.get_gsyn(
                    transciever, runtime_in_machine_time_steps, placements,
                    graph_mapper, False)

        for edge in partitionable_graph.edges:
            # TODO fix this for recording weights and delay changes
            # (or whatever edge recordings there are)
            pass
