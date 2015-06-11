from spynnaker.pyNN import exceptions
from pacman.utilities.progress_bar import ProgressBar

from data_specification import utility_calls as dsg_utility_calls

import logging
import numpy
import struct

logger = logging.getLogger(__name__)


class AbstractPopulationRecordableVertex(object):
    """ Neural recording
    """

    def __init__(self, machine_time_step, label):
        self._record_v = False
        self._record_gsyn = False

    @property
    def record_v(self):
        return self._record_v

    @property
    def record_gsyn(self):
        return self._record_gsyn

    def set_record_v(self, setted_value):
        self._record_v = setted_value

    def set_record_gsyn(self, setted_value):
        self._record_gsyn = setted_value

    def get_neuron_parameter(
            self, region, compatible_output, has_ran, graph_mapper, placements,
            txrx, machine_time_step):
        if not has_ran:
            raise exceptions.SpynnakerException(
                "The simulation has not yet ran, therefore neuron param "
                "cannot be retrieved")

        times = numpy.zeros(0)
        ids = numpy.zeros(0)
        values = numpy.zeros(0)
        ms_per_tick = self._machine_time_step / 1000.0

        # Find all the sub-vertices that this pynn_population.py exists on
        subvertices = graph_mapper.get_subvertices_from_vertex(self)
        progress_bar = ProgressBar(len(subvertices), "Getting recorded data")
        for subvertex in subvertices:
            placment = placements.get_placement_of_subvertex(subvertex)
            (x, y, p) = placment.x, placment.y, placment.p

            # Get the App Data for the core
            app_data_base_address = txrx.\
                get_cpu_information_from_core(x, y, p).user[0]

            # Get the position of the value buffer
            neuron_param_region_base_address_offset = \
                dsg_utility_calls.get_region_base_address_offset(
                    app_data_base_address, region)
            neuron_param_region_base_address_buf = str(list(txrx.read_memory(
                x, y, neuron_param_region_base_address_offset, 4))[0])
            neuron_param_region_base_address = \
                struct.unpack("<I", neuron_param_region_base_address_buf)[0]
            neuron_param_region_base_address += app_data_base_address

            # Read the size
            number_of_bytes_written_buf = \
                str(list(txrx.read_memory(
                    x, y, neuron_param_region_base_address, 4))[0])

            number_of_bytes_written = \
                struct.unpack_from("<I", number_of_bytes_written_buf)[0]

            # Read the values
            logger.debug("Reading {} ({}) bytes starting at {}".format(
                number_of_bytes_written, hex(number_of_bytes_written),
                hex(neuron_param_region_base_address + 4)))

            neuron_param_region_data = txrx.read_memory(
                x, y, neuron_param_region_base_address + 4,
                number_of_bytes_written)

            vertex_slice = graph_mapper.get_subvertex_slice(subvertex)
            n_atoms = (vertex_slice.hi_atom - vertex_slice.lo_atom) + 1

            bytes_per_time_step = n_atoms * 4

            number_of_time_steps_written = \
                number_of_bytes_written / bytes_per_time_step

            logger.debug("Processing {} timesteps"
                         .format(number_of_time_steps_written))

            data_list = bytearray()
            for data in neuron_param_region_data:
                data_list.extend(data)

            numpy_data = numpy.asarray(data_list, dtype="uint8").view(
                dtype="<i4") / 32767.0
            values = numpy.append(values, numpy_data)
            times = numpy.append(
                times, numpy.repeat(range(numpy_data.size / n_atoms),
                                    n_atoms) * ms_per_tick)
            ids = numpy.append(ids, numpy.add(
                numpy.arange(numpy_data.size) % n_atoms, vertex_slice.lo_atom))
            progress_bar.update()

        progress_bar.end()
        result = numpy.dstack((ids, times, values))[0]
        result = result[numpy.lexsort((times, ids))]
        return result
