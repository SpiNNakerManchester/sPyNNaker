from visualiser_framework.visualiser_thread import VisualiserThread
from spynnaker.pyNN.utilities import conf
from spynnaker.pyNN.visualiser_package.visualiser_pages.machine_page \
    import MachinePage
from spynnaker.pyNN.visualiser_package.visualiser_pages.configuration_page \
    import ConfigPage


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
            #add basic machine page
            machine_page = MachinePage(True, scope, machine, placements,
                                       router_tables, graph_mapper)
            pages.append(machine_page)
            #visualiser_framework.add_page(machine_page, machine_page.label)
            machine_page.show()
            #add configuration page
            config_page = ConfigPage(visualiser_vertex_to_page_mapping,
                                     visualiser_vertices, graph, visualiser,
                                     transceiver, has_board, sim_run_time,
                                     machine_time_step, subgraph, placements,
                                     graph_mapper)
            config_page.show()
            pages.append(config_page)
            #visualiser_framework.add_page(config_page, config_page.label)
            visualiser = VisualiserThread(has_board, pages=pages)
            if wait_for_run:  # add run now button if required
                visualiser.add_menu_item("Run Now!", self._run_item_selected)

        return visualiser, visualiser_vertex_to_page_mapping

    def _run_item_selected(self):
        pass

    def set_visulaiser_port(self, port):
        pass