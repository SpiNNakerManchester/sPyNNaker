from pacman.utilities.utility_objs.progress_bar import ProgressBar
from spynnaker.pyNN.models.common import recording_utils

import numpy
import tempfile


class GsynRecorder(object):

    def __init__(self, machine_time_step):
        self._machine_time_step = machine_time_step
        self._record_gsyn = False
        # set up cache files for recording of parameters
        self._gsyns_cache_file = None
        # position params for knowing how much data has been extracted
        self._extracted_gsyn_machine_time_steps = 0
        # number of times the gsyn have been loaded to the temp file
        self._no_gsyn_loads = 0

    @property
    def record_gsyn(self):
        return self._record_gsyn

    @record_gsyn.setter
    def record_gsyn(self, record_gsyn):
        self._record_gsyn = record_gsyn

    def get_sdram_usage_in_bytes(
            self, n_neurons, n_machine_time_steps):
        if not self._record_gsyn:
            return 0

        return recording_utils.get_recording_region_size_in_bytes(
            n_machine_time_steps, 8 * n_neurons)

    def get_dtcm_usage_in_bytes(self):
        if not self._record_gsyn:
            return 0
        return 4

    def get_n_cpu_cycles(self, n_neurons):
        if not self._record_gsyn:
            return 0
        return n_neurons * 8

    def reset(self):
        self._extracted_gsyn_machine_time_steps = 0
        self._gsyns_cache_file = None
        self._no_gsyn_loads = 0

    def get_gsyn(self, label, n_atoms, transceiver, region,
                 n_machine_time_steps, placements, graph_mapper,
                 partitionable_vertex, return_data=True):

        if self._gsyns_cache_file is None:
            self._gsyns_cache_file = tempfile.NamedTemporaryFile(mode='a+b')

        if n_machine_time_steps == self._extracted_gsyn_machine_time_steps:
            if return_data:
                return recording_utils.pull_off_cached_lists(
                    self._no_gsyn_loads, self._gsyns_cache_file)
        else:
            to_extract_n_machine_time_steps = \
                n_machine_time_steps - self._extracted_gsyn_machine_time_steps

            ms_per_tick = self._machine_time_step / 1000.0

            subvertices = \
                graph_mapper.get_subvertices_from_vertex(partitionable_vertex)

            tempfilehandle = tempfile.NamedTemporaryFile()
            data = numpy.memmap(
                tempfilehandle.file,
                shape=(to_extract_n_machine_time_steps, n_atoms),
                dtype="float64,float64,float64,float64")
            data["f0"] = (numpy.arange(
                n_atoms * to_extract_n_machine_time_steps) % n_atoms).reshape(
                    (to_extract_n_machine_time_steps, n_atoms))
            data["f1"] = numpy.repeat(numpy.arange(
                (self._extracted_gsyn_machine_time_steps * ms_per_tick),
                (self._extracted_gsyn_machine_time_steps +
                 to_extract_n_machine_time_steps) * ms_per_tick, ms_per_tick),
                n_atoms).reshape((to_extract_n_machine_time_steps, n_atoms))

            progress_bar = ProgressBar(
                len(subvertices), "Getting conductance for {}".format(label))
            for subvertex in subvertices:

                vertex_slice = graph_mapper.get_subvertex_slice(subvertex)
                placement = placements.get_placement_of_subvertex(subvertex)

                region_size = \
                    recording_utils.get_recording_region_size_in_bytes(
                        to_extract_n_machine_time_steps,
                        8 * vertex_slice.n_atoms)
                neuron_param_region_data, number_of_bytes_written = \
                    recording_utils.get_data(
                        transceiver, placement, region, region_size)

                numpy_data = (numpy.asarray(
                    neuron_param_region_data,
                    dtype="uint8").view(dtype="<i4") / 32767.0)

                if number_of_bytes_written > 0:
                    numpy_data = numpy_data.reshape(
                        (to_extract_n_machine_time_steps,
                         vertex_slice.n_atoms * 2))

                    data["f2"][:, vertex_slice.lo_atom:
                                  vertex_slice.hi_atom + 1] =\
                        numpy_data[:, 0::2]
                    data["f3"][:, vertex_slice.lo_atom:
                                vertex_slice.hi_atom + 1] =\
                        numpy_data[:, 1::2]
                progress_bar.update()

            progress_bar.end()
            data.shape = n_atoms * to_extract_n_machine_time_steps

            # extract old data
            cached_gsyn = recording_utils.pull_off_cached_lists(
                self._no_gsyn_loads, self._gsyns_cache_file)

            # cache the data just pulled off
            numpy.save(self._gsyns_cache_file, data)
            self._no_gsyn_loads += 1

            # concat extracted with cached
            if len(cached_gsyn) != 0:
                all_gsyn = numpy.concatenate((cached_gsyn, data))
            else:
                all_gsyn = data

            shaped_gsyn = all_gsyn.view(dtype="float64").reshape(
                (n_atoms * n_machine_time_steps, 4))

            # Sort the data - apparently, using lexsort is faster, but it might
            # consume more memory, so the option is left open for sort-in-place

            # data.sort(order=['f0', 'f1'], axis=0)
            order = numpy.lexsort((all_gsyn["f1"], all_gsyn["f0"]))

            self._extracted_gsyn_machine_time_steps += \
                to_extract_n_machine_time_steps

            # return all gsyn
            return shaped_gsyn[order]
