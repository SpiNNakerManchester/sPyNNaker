from pacman.utilities.utility_objs.progress_bar import ProgressBar
from spynnaker.pyNN.models.common.abstract_gsyn_recordable import \
    AbstractGSynRecordable
from spynnaker.pyNN.models.common.abstract_spike_recordable import \
    AbstractSpikeRecordable
from spynnaker.pyNN.models.common.abstract_v_recordable import \
    AbstractVRecordable

import numpy


class SpyNNakerRecordingExtractor(object):
    """
    SpyNNakerRecordingExtractor: the extractor for application graph spynnaker
     supports for recording parameters
    """

    def __call__(
            self, partitionable_graph, transciever, placements,
            runtime_in_machine_time_steps, graph_mapper):

        progress_bar = ProgressBar(
            len(partitionable_graph.vertices) + len(partitionable_graph.edges),
            "Extracting recorded data from the PyNN application space for "
            "the last run")
        # search through populations for vertices which need to have their
        # recorded data extracted
        for vertex in partitionable_graph.vertices:
            if isinstance(vertex, AbstractSpikeRecordable):
                self._handle_spike_recordings(
                    vertex, runtime_in_machine_time_steps, transciever,
                    placements, graph_mapper)

            if isinstance(vertex, AbstractVRecordable):
                if vertex.is_recording_v:
                    self._handle_v_recordings(
                        vertex, runtime_in_machine_time_steps, transciever,
                        placements, graph_mapper)

            if isinstance(vertex, AbstractGSynRecordable):
                if vertex.is_recording_gsyn:
                    self._handle_gsyn_recordings(
                        vertex, runtime_in_machine_time_steps, transciever,
                        placements, graph_mapper)

            progress_bar.update()

        for edge in partitionable_graph.edges:
            # TODO fix this for recording weights and delay changes
            # (or whatever edge recordings there are)
            progress_bar.update()
        progress_bar.end()

    @staticmethod
    def _handle_spike_recordings(
            vertex, runtime_in_machine_time_steps, transceiver, placements,
            graph_mapper):
        """

        :param vertex:
        :param runtime_in_machine_time_steps:
        :param transceiver:
        :param placements:
        :param graph_mapper:
        :return:
        """
        recording_spikes = vertex.is_recording_spikes
        lastast_recorded_time = vertex.get_last_extracted_spike_time
        equal_to_time = vertex.get_last_extracted_spike_time != runtime_in_machine_time_steps
        if (vertex.is_recording_spikes()
                and vertex.get_last_extracted_spike_time() !=
                runtime_in_machine_time_steps):
            to_extract_machine_time_steps = \
                runtime_in_machine_time_steps - \
                vertex.get_last_extracted_spike_time()
            if to_extract_machine_time_steps != 0:
                spikes = vertex.get_spikes(
                    transceiver, to_extract_machine_time_steps, placements,
                    graph_mapper)
                spike_cache_file = vertex.get_cache_file_for_spike_data()
                numpy.save(spike_cache_file, spikes)

    @staticmethod
    def _handle_v_recordings(
            vertex, runtime_in_machine_time_steps, transceiver, placements,
            graph_mapper):
        """

        :param vertex:
        :param runtime_in_machine_time_steps:
        :param transceiver:
        :param placements:
        :param graph_mapper:
        :return:
        """
        if (vertex.is_recording_v()
                and vertex.get_last_extracted_v_time() !=
                runtime_in_machine_time_steps):
            to_extract_machine_time_steps = \
                runtime_in_machine_time_steps - \
                vertex.get_last_extracted_v_time()
            if to_extract_machine_time_steps != 0:
                vs = vertex.get_v(
                    transceiver, to_extract_machine_time_steps, placements,
                    graph_mapper)
                v_cache_file = vertex.get_cache_file_for_v_data()
                numpy.save(v_cache_file, vs)

    @staticmethod
    def _handle_gsyn_recordings(
            vertex, runtime_in_machine_time_steps, transceiver, placements,
            graph_mapper):
        """

        :param vertex:
        :param runtime_in_machine_time_steps:
        :param transceiver:
        :param placements:
        :param graph_mapper:
        :return:
        """
        if (vertex.is_recording_gsyn()
                and vertex.get_last_extracted_gsyn_time() !=
                runtime_in_machine_time_steps):
            to_extract_machine_time_steps = \
                runtime_in_machine_time_steps - \
                vertex.get_last_extracted_gsyn_time()
            if to_extract_machine_time_steps != 0:
                gsyns = vertex.get_gsyn(
                    transceiver, to_extract_machine_time_steps, placements,
                    graph_mapper)
                gsyn_cache_file = vertex.get_cache_file_for_gsyn_data()
                numpy.save(gsyn_cache_file, gsyns)
