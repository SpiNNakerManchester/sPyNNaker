from pacman.utilities.progress_bar import ProgressBar

from spynnaker.pyNN.models.common import recording_utils

import numpy
import tempfile


class GsynRecorder(object):

    def __init__(self, machine_time_step):
        self._machine_time_step = machine_time_step
        self._record_gsyn = False

        # A list of tuples of (placement, vertex_slice)
        self._subvertex_information = list()

    @property
    def record_gsyn(self):
        return self._record_gsyn

    @record_gsyn.setter
    def record_gsyn(self, record_gsyn):
        self._record_gsyn = record_gsyn

    def add_subvertex_information(self, placement, vertex_slice):
        """ Add a subvertex for gsyn retrieval
        """
        self._subvertex_information.append((placement, vertex_slice))

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

    def get_gsyn(self, label, n_atoms, transceiver, region,
                 n_machine_time_steps):

        ms_per_tick = self._machine_time_step / 1000.0

        tempfilehandle = tempfile.NamedTemporaryFile()
        data = numpy.memmap(
            tempfilehandle.file, shape=(n_machine_time_steps, n_atoms),
            dtype="float64,float64,float64,float64")
        data["f0"] = (numpy.arange(
            n_atoms * n_machine_time_steps) % n_atoms).reshape(
                (n_machine_time_steps, n_atoms))
        data["f1"] = numpy.repeat(numpy.arange(
            0, n_machine_time_steps * ms_per_tick, ms_per_tick),
            n_atoms).reshape((n_machine_time_steps, n_atoms))

        progress_bar = ProgressBar(
            len(self._subvertex_information),
            "Getting conductance for {}".format(label))
        for placement, vertex_slice in self._subvertex_information:

            region_size = recording_utils.get_recording_region_size_in_bytes(
                n_machine_time_steps, 8 * vertex_slice.n_atoms)
            neuron_param_region_data = recording_utils.get_data(
                transceiver, placement, region, region_size)

            numpy_data = (numpy.asarray(
                neuron_param_region_data, dtype="uint8").view(dtype="<i4") /
                32767.0).reshape(
                    (n_machine_time_steps, vertex_slice.n_atoms * 2))
            data["f2"][:, vertex_slice.lo_atom:vertex_slice.hi_atom + 1] =\
                numpy_data[:, 0::2]
            data["f3"][:, vertex_slice.lo_atom:vertex_slice.hi_atom + 1] =\
                numpy_data[:, 1::2]
            progress_bar.update()

        progress_bar.end()
        data.shape = n_atoms * n_machine_time_steps

        # Sort the data - apparently, using lexsort is faster, but it might
        # consume more memory, so the option is left open for sort-in-place
        order = numpy.lexsort((data["f1"], data["f0"]))
        # data.sort(order=['f0', 'f1'], axis=0)

        result = data.view(dtype="float64").reshape(
            (n_atoms * n_machine_time_steps, 4))[order]
        return result
