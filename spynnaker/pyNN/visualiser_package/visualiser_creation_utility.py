from spynnaker.pyNN.visualiser_package.visualiser_thread import VisualiserThread
from spynnaker.pyNN.utilities import conf


class VisualiserCreationUtility(object):

    def __init__(self):
        pass

    def create_visualiser_interface(self, has_board, transceiver, graph,
                                    visualiser_vertices, machine, subgraph,
                                    placements, router_tables, sim_run_time,
                                    machine_time_step, graph_mapper):
        # Start visuliser if requested
        visualiser = None
        visualiser_vertex_to_page_mapping = dict()
        coord_to_low_atom_mapper = None
        if conf.config.getboolean("Visualiser", "enable"):
            wait_for_run = conf.config.getboolean("Visualiser",
                                                  "pause_before_run")
            scope = conf.config.get("Visualiser", "initial_scope")
            #create vis
            #visualiser_framework = VisualiserThread(has_board)
            pages = list()
            #create basic pages required

            #visualiser_framework.add_page(config_page, config_page.label)
            visualiser = VisualiserThread(
                visualiser_vertex_to_page_mapping, visualiser_vertices, graph,
                visualiser, transceiver, sim_run_time, machine_time_step,
                subgraph, placements, graph_mapper, has_board=has_board)
            if wait_for_run:  # add run now button if required
                visualiser.add_menu_item("Run Now!", self._run_item_selected)

        return visualiser, visualiser_vertex_to_page_mapping

    def _run_item_selected(self):
        pass

    def set_visulaiser_port(self, port):
        pass