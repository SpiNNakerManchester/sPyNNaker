import numpy
import logging

from spinn_machine.utilities.progress_bar import ProgressBar

logger = logging.getLogger(__name__)


class AbstractUInt32Recorder(object):
    N_BYTES_PER_NEURON = 4
    N_CPU_CYCLES_PER_NEURON = 8

    def __init__(self):
        pass

    @staticmethod
    def get_data(
            label, buffer_manager, region, placements, graph_mapper,
            application_vertex, machine_time_step, variable):
        """ method for reading a uint32 mapped to time and neuron ids from
        the SpiNNaker machine

        :param label: vertex label
        :param buffer_manager: the manager for buffered data
        :param region: the dsg region id used for this data
        :param placements: the placements object
        :param graph_mapper: the mapping between application and machine
        vertices
        :param application_vertex:
        :param machine_time_step:
        :param variable:
        :return:
        """

        vertices = graph_mapper.get_machine_vertices(application_vertex)

        ms_per_tick = machine_time_step / 1000.0

        data = list()
        missing_str = ""

        progress_bar = \
            ProgressBar(
                len(vertices), "Getting {} for {}".format(variable, label))

        for vertex in vertices:

            vertex_slice = graph_mapper.get_slice(vertex)
            placement = placements.get_placement_of_vertex(vertex)

            x = placement.x
            y = placement.y
            p = placement.p

            # for buffering output info is taken form the buffer manager
            neuron_param_region_data_pointer, missing_data = \
                buffer_manager.get_data_for_vertex(
                    placement, region)
            if missing_data:
                missing_str += "({}, {}, {}); ".format(x, y, p)
            record_raw = neuron_param_region_data_pointer.read_all()
            record_length = len(record_raw)
            n_rows = record_length / ((vertex_slice.n_atoms + 1) * 4)
            record = (numpy.asarray(record_raw, dtype="uint8").
                      view(dtype="<i4")).reshape((n_rows,
                                                  (vertex_slice.n_atoms + 1)))
            split_record = numpy.array_split(record, [1, 1], 1)
            record_time = numpy.repeat(
                split_record[0] * float(ms_per_tick), vertex_slice.n_atoms, 1)
            record_ids = numpy.tile(
                numpy.arange(vertex_slice.lo_atom, vertex_slice.hi_atom + 1),
                len(record_time)).reshape((-1, vertex_slice.n_atoms))
            record_membrane_potential = split_record[2] / 32767.0

            part_data = numpy.dstack(
                [record_ids, record_time, record_membrane_potential])
            part_data = numpy.reshape(part_data, [-1, 3])
            data.append(part_data)
            progress_bar.update()

        progress_bar.end()
        if len(missing_str) > 0:
            logger.warn(
                "Population {} is missing {} data in region {}"
                " from the following cores: {}".format(
                    label, variable, region, missing_str))
        data = numpy.vstack(data)
        order = numpy.lexsort((data[:, 1], data[:, 0]))
        result = data[order]
        return result
