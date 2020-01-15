from collections import defaultdict

from spynnaker.pyNN.models.neuron import AbstractPopulationVertex
from spynnaker.pyNN.models.utility_models.delays import DelayExtensionVertex


class SynapticDataTracker(object):

    def _store(
            self, total_sdram_per_board, chip, placement,
            synaptic_matrix_size):

        total_sdram_per_board[
            (chip.nearest_ethernet_x,
             chip.nearest_ethernet_y)] += synaptic_matrix_size

        # print
        print("chip {}:{}:{} has sdram size {}".format(
            placement.x, placement.y, placement.p,
            synaptic_matrix_size))

    def __call__(self, placements, graph_mapper, machine, application_graph,
                 machine_time_step):
        total_sdram_per_board = defaultdict(int)
        sum_of_sdram_total = 0
        for placement in placements.placements:
            associated_vertex = graph_mapper.get_application_vertex(
                placement.vertex)
            chip = machine.get_chip_at(placement.x, placement.y)

            if isinstance(associated_vertex, AbstractPopulationVertex):
                synaptic_matrix_size = \
                    associated_vertex.get_synaptic_matrix_size(
                        application_graph, machine_time_step, graph_mapper,
                        placement.vertex)

                # update trackers
                sum_of_sdram_total += synaptic_matrix_size
                self._store(
                    total_sdram_per_board, chip, placement,
                    synaptic_matrix_size)

            if isinstance(associated_vertex, DelayExtensionVertex):
                synaptic_matrix_size = \
                    associated_vertex.delay_param_region_size(
                        graph_mapper.get_slice(placement.vertex))

                # update trackers
                sum_of_sdram_total += synaptic_matrix_size
                self._store(
                    total_sdram_per_board, chip, placement,
                    synaptic_matrix_size)

        for (x, y) in total_sdram_per_board:
            print("for board {}:{} total sdram {}".format(
                x, y, total_sdram_per_board[(x, y)]))

        print(
            "total sdram for synaptic data for entire machine is {}".format(
                sum_of_sdram_total))