from pacman.utilities.progress_bar import ProgressBar

from spynnaker.pyNN.utilities import constants

import numpy


class GsynRecorder(object):

    def __init__(self, machine_time_step):
        self._machine_time_step = machine_time_step
        self._record_gsyn = False

    @property
    def record_gsyn(self):
        return self._record_gsyn

    @record_gsyn.setter
    def record_gsyn(self, record_gsyn):
        self._record_gsyn = record_gsyn

    def get_sdram_usage_in_bytes(self, n_neurons, n_machine_time_steps):
        if not self._record_gsyn:
            return 0

        # size computed without buffering out technique
        # return recording_utils.get_recording_region_size_in_bytes(
        #     n_machine_time_steps, 8 * n_neurons)

        # size computed for buffering out technique
        return constants.GSYN_BUFFER_SIZE_BUFFERING_OUT

    def get_dtcm_usage_in_bytes(self):
        if not self._record_gsyn:
            return 0
        return 4

    def get_n_cpu_cycles(self, n_neurons):
        if not self._record_gsyn:
            return 0
        return n_neurons * 8

    def get_gsyn(self, label, n_atoms, buffer_manager, region, state_region,
                 n_machine_time_steps, placements, graph_mapper,
                 partitionable_vertex):

        ms_per_tick = self._machine_time_step / 1000.0

        subvertices = \
            graph_mapper.get_subvertices_from_vertex(partitionable_vertex)

        data = list()

        progress_bar = ProgressBar(
            len(subvertices), "Getting conductance for {}".format(label))
        for subvertex in subvertices:

            vertex_slice = graph_mapper.get_subvertex_slice(subvertex)
            placement = placements.get_placement_of_subvertex(subvertex)

            x = placement.x
            y = placement.y
            p = placement.p

            # for buffering output info is taken form the buffer manager
            neuron_param_region_data_pointer = buffer_manager.\
                get_data_for_vertex(x, y, p, region, state_region)
            
            record_raw = neuron_param_region_data_pointer.read_all()
            record_length = len(record_raw)
            n_rows = record_length / (((vertex_slice.n_atoms * 2) + 1) * 4)
            record = (numpy.asarray(record_raw, dtype="uint8").
                      view(dtype="<i4")).reshape(
                (n_rows, ((vertex_slice.n_atoms * 2) + 1)))
            split_record = numpy.array_split(record, [1, 1], 1)
            record_time = numpy.repeat(
                split_record[0] * float(ms_per_tick),
                vertex_slice.n_atoms, 1)
            record_ids = numpy.tile(
                numpy.arange(vertex_slice.lo_atom, vertex_slice.hi_atom + 1),
                len(record_time)).reshape((-1, vertex_slice.n_atoms))
            record_gsyn = (split_record[2] / 32767.0).reshape(
                [-1, vertex_slice.n_atoms, 2])

            part_data = numpy.dstack([record_ids, record_time, record_gsyn])
            part_data = numpy.reshape(part_data, [-1, 4])
            data.append(part_data)
            progress_bar.update()

        progress_bar.end()

        data = numpy.vstack(data)
        order = numpy.lexsort((data[:, 1], data[:, 0]))
        result = data[order]
        return result
