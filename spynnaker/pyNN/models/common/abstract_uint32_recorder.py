import numpy
import logging

from spinn_utilities.progress_bar import ProgressBar
from data_specification.enums import DataType
from spinn_front_end_common.utilities import globals_variables

logger = logging.getLogger(__name__)


class AbstractUInt32Recorder(object):
    N_BYTES_PER_NEURON = 4
    N_CPU_CYCLES_PER_NEURON = 4

    def __init__(self):
        pass

    @staticmethod
    def get_data(
            label, buffer_manager, region, placements, graph_mapper,
            application_vertex, machine_time_step, variable,
            n_machine_time_steps):
        """
        DEPRICATED!

        method for reading a uint32 mapped to time and neuron ids from\
        the SpiNNaker machine

        :param label: vertex label
        :param buffer_manager: the manager for buffered data
        :param region: the dsg region id used for this data
        :param placements: the placements object
        :param graph_mapper: the mapping between application and machine\
            vertices
        :param application_vertex:
        :param machine_time_step:
        :param variable:
        :param n_machine_time_steps:
        :return:
        """
        pop = 1/0
        vertices = graph_mapper.get_machine_vertices(application_vertex)
        ms_per_tick = machine_time_step / 1000.0
        data = list()
        missing_str = ""
        all_times = numpy.arange(0, n_machine_time_steps)

        progress = ProgressBar(
                vertices, "Getting {} for {}".format(variable, label))
        for vertex in progress.over(vertices):
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
            record_membrane_potential = (
                split_record[2] / float(DataType.S1615.scale))

            part_data = numpy.dstack(
                [record_ids, record_time, record_membrane_potential])
            part_data = numpy.reshape(part_data, [-1, 3])
            data.append(part_data)

            # Fill in any missing data
            if missing_data:
                records_without_data = all_times[numpy.invert(
                    numpy.isin(all_times, split_record[0].flatten()))]
                times_without_data = numpy.repeat(
                    records_without_data, vertex_slice.n_atoms).reshape(
                        (-1, vertex_slice.n_atoms))
                ids_without_data = numpy.tile(
                    numpy.arange(
                        vertex_slice.lo_atom, vertex_slice.hi_atom + 1),
                    len(records_without_data)).reshape(
                            (-1, vertex_slice.n_atoms))
                values_without_data = numpy.repeat(
                    numpy.nan,
                    len(records_without_data) * vertex_slice.n_atoms).reshape(
                        (-1, vertex_slice.n_atoms))
                missing_values = numpy.dstack(
                    [ids_without_data, times_without_data,
                     values_without_data])
                missing_values = numpy.reshape(missing_values, [-1, 3])
                data.append(missing_values)

        if len(missing_str) > 0:
            logger.warn(
                "Population {} is missing {} data in region {}"
                " from the following cores: {}".format(
                    label, variable, region, missing_str))
        data = numpy.vstack(data)
        order = numpy.lexsort((data[:, 1], data[:, 0]))
        result = data[order]
        return result

    def n_neurons_recording(self, variable, vertex_slice):
        return vertex_slice.n_atoms

    def neurons_recording(self, variable, vertex_slice):
        return range(vertex_slice.lo_atom, vertex_slice.hi_atom + 1)

    def sampling_interval(self, variable):
        return globals_variables.get_simulator().machine_time_step

    def get_matrix_data(
            self, label, buffer_manager, region, placements, graph_mapper,
            application_vertex, variable, n_machine_time_steps):
        """ method for reading a uint32 mapped to time and neuron ids from\
        the SpiNNaker machine

        :param label: vertex label
        :param buffer_manager: the manager for buffered data
        :param region: the dsg region id used for this data
        :param placements: the placements object
        :param graph_mapper: the mapping between application and machine\
            vertices
        :param application_vertex:
        :param variable: PyNN name for the variable (V, gsy_ihn ect
        :type variable: str
        :param n_machine_time_steps:
        :return:
        """
        vertices = graph_mapper.get_machine_vertices(application_vertex)
        progress = ProgressBar(
                vertices, "Getting {} for {}".format(variable, label))
        sampling_interval = self.sampling_interval(variable)
        missing_str = ""
        data = None
        ids = []
        for vertex in progress.over(vertices):
            placement = placements.get_placement_of_vertex(vertex)
            vertex_slice = graph_mapper.get_slice(vertex)
            neurons = self.neurons_recording(variable, vertex_slice)
            n_neurons = len(neurons)
            ids.extend(neurons)
            # for buffering output info is taken form the buffer manager
            neuron_param_region_data_pointer, missing_data = \
                buffer_manager.get_data_for_vertex(
                    placement, region)
            record_raw = neuron_param_region_data_pointer.read_all()
            record_length = len(record_raw)
            row_length = (n_neurons + 1) * self.N_BYTES_PER_NEURON
            # There is one column for time and one for each neuron recording
            n_rows = record_length / row_length
            # Converts bytes to ints and make a matrix
            record = (numpy.asarray(record_raw, dtype="uint8").
                      view(dtype="<i4")).reshape((n_rows, (n_neurons + 1)))
            # Check if you have the expected data
            if missing_data or n_rows != n_machine_time_steps:
                missing_str += "({}, {}, {}); ".format(
                    placement.x, placement.y, placement.p)
                # Start the fragment for this slice empty
                fragment = numpy.empty((n_machine_time_steps, n_neurons))
                for i in xrange(0, n_machine_time_steps):
                    timestep = i * sampling_interval
                    # Check if there is data for this timestep
                    indexes = numpy.where(record[:, 0] == timestep)
                    if len(indexes[0]) > 0:
                        # Set row to data for that timestep
                        fragment[i] = record[indexes[0][0], 1:]
                    else:
                        # Set row to nan
                        fragment[i] = numpy.full(n_neurons, numpy.nan)
            else:
                # Just cut the timestamps off to get the fragment
                fragment = (record[:, 1:] / float(DataType.S1615.scale))
            if data is None:
                data = fragment
            else:
                # Add the slice fragment on axis 1 which is ids/ channel_index
                data = numpy.append(data, fragment, axis=1)
        return (data, ids, sampling_interval)

    @staticmethod
    def pynn7_format(data, ids, sampling_interval):
        n_machine_time_steps = len(data)
        n_neurons = len(ids)
        column_length = n_machine_time_steps * n_neurons
        times = [i * sampling_interval for i in
                 xrange(0, n_machine_time_steps)]
        pynn7 = numpy.empty((column_length, 3))
        pynn7[:, 0] = numpy.repeat(times, n_neurons, 0).\
            reshape(1, column_length)
        pynn7[:, 1] = numpy.tile(ids, n_machine_time_steps).\
            reshape(1, column_length)
        pynn7[:, 2] = data.reshape(1, column_length)
        return pynn7


if __name__ == '__main__':
    import quantities
    n_neurons = 3
    n_machine_time_steps = 4
    sampling_interval = .5
    ms_per_tick = 1 * quantities.ms
    good = numpy.array([[0, 62, 62, 62],
                       [1, 65, 65, 65],
                       [2, 63, 63, 64],
                       [3, 64, 62, 64]])
    fragment = (
        good[:, 1:] / float(DataType.S1615.scale))
    print fragment

    bad = numpy.array([[0, 62, 62.2, 62.3],
                       [1.5, 63, 63.2, 64]])
    full = numpy.array([[i * sampling_interval]
                        for i in xrange(0, n_machine_time_steps)])
    fragment = numpy.empty((n_machine_time_steps, n_neurons))
    ids = range(n_neurons)
    for i in xrange(0, n_machine_time_steps):
        timestep = i * sampling_interval
        indexes = numpy.where(bad[:, 0] == timestep)
        if len(indexes[0]) > 0:
            fragment[i] = bad[indexes[0][0], 1:]
        else:
            fragment[i] = numpy.full(n_neurons, numpy.nan)
    print fragment
    print AbstractUInt32Recorder.pynn7_format(fragment, ids, sampling_interval)
