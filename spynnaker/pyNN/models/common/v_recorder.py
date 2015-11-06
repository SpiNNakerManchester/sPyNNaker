from pacman.utilities.utility_objs.progress_bar import ProgressBar
from spynnaker.pyNN.models.common import recording_utils

import numpy
import tempfile


class VRecorder(object):

    def __init__(self, machine_time_step):
        self._record_v = False
        self._machine_time_step = machine_time_step
        # set up cache files for recording of parameters
        self._vs_cache_file = None
        # position params for knowing how much data has been extracted
        self._extracted_v_machine_time_steps = 0
        # number of times the v have been loaded to the temp file
        self._no_v_loads = 0

    @property
    def record_v(self):
        return self._record_v

    @record_v.setter
    def record_v(self, record_v):
        self._record_v = record_v

    def get_sdram_usage_in_bytes(
            self, n_neurons, n_machine_time_steps):
        if not self._record_v:
            return 0

        return recording_utils.get_recording_region_size_in_bytes(
            n_machine_time_steps, 4 * n_neurons)

    def get_dtcm_usage_in_bytes(self):
        if not self._record_v:
            return 0
        return 4

    def get_n_cpu_cycles(self, n_neurons):
        if not self._record_v:
            return 0
        return n_neurons * 4

    def reset(self):
        self._extracted_v_machine_time_steps = 0
        self._vs_cache_file = None
        self._no_v_loads = 0

    def get_v(self, label, n_atoms, transceiver, region, n_machine_time_steps,
              placements, graph_mapper, partitionable_vertex, return_data=True):

        if self._vs_cache_file is None:
            self._vs_cache_file = tempfile.NamedTemporaryFile(mode='a+b')

        if n_machine_time_steps == self._extracted_v_machine_time_steps:
            if return_data:
                return recording_utils.pull_off_cached_lists(
                    self._no_v_loads, self._vs_cache_file)
        else:
            to_extract_n_machine_time_steps = \
                n_machine_time_steps - self._extracted_v_machine_time_steps

            subvertices = \
                graph_mapper.get_subvertices_from_vertex(partitionable_vertex)

            ms_per_tick = self._machine_time_step / 1000.0

            tempfilehandle = tempfile.NamedTemporaryFile()
            data = numpy.memmap(
                tempfilehandle.file,
                shape=(to_extract_n_machine_time_steps, n_atoms),
                dtype="float64,float64,float64")
            data["f0"] = (numpy.arange(
                n_atoms * to_extract_n_machine_time_steps) % n_atoms).reshape(
                    (to_extract_n_machine_time_steps, n_atoms))
            # sort out times
            data["f1"] = numpy.repeat(numpy.arange(
                self._extracted_v_machine_time_steps,
                (self._extracted_v_machine_time_steps +
                 to_extract_n_machine_time_steps) * ms_per_tick, ms_per_tick),
                n_atoms).reshape((to_extract_n_machine_time_steps, n_atoms))

            progress_bar = \
                ProgressBar(len(subvertices),
                            "Getting membrane voltage for {}".format(label))

            for subvertex in subvertices:

                vertex_slice = graph_mapper.get_subvertex_slice(subvertex)
                placement = placements.get_placement_of_subvertex(subvertex)

                region_size = \
                    recording_utils.get_recording_region_size_in_bytes(
                        to_extract_n_machine_time_steps,
                        4 * vertex_slice.n_atoms)
                neuron_param_region_data = recording_utils.get_data(
                    transceiver, placement, region, region_size)

                numpy_data = (numpy.asarray(
                    neuron_param_region_data, dtype="uint8").view(dtype="<i4") /
                    32767.0).reshape((to_extract_n_machine_time_steps,
                                      vertex_slice.n_atoms))
                data["f2"][:, vertex_slice.lo_atom:vertex_slice.hi_atom + 1] =\
                    numpy_data
                progress_bar.update()

            progress_bar.end()
            data.shape = n_atoms * to_extract_n_machine_time_steps

            # Sort the data - apparently, using lexsort is faster, but it might
            # consume more memory, so the option is left open for sort-in-place
            order = numpy.lexsort((data["f1"], data["f0"]))
            # data.sort(order=['f0', 'f1'], axis=0)

            vs = data.view(dtype="float64").reshape(
                (n_atoms * to_extract_n_machine_time_steps, 3))[order]

             # extract old data
            cached_v = recording_utils.pull_off_cached_lists(
                self._no_v_loads, self._vs_cache_file)

            # cache the data just pulled off
            numpy.save(self._vs_cache_file, vs)
            self._no_v_loads += 1

            # concat extracted with cached
            if len(cached_v) != 0:
                all_vs = numpy.concatenate((cached_v, vs))
            else:
                all_vs = vs

            self._extracted_v_machine_time_steps += \
                to_extract_n_machine_time_steps

            # return all spikes
            return all_vs
