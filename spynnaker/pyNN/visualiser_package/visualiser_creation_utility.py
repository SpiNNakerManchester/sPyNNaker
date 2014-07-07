__author__ = 'stokesa6'
import gtk
from visualiser.visualiser_thread import VisualiserThread
from spynnaker.pyNN.visualiser_package.visualiser_pages.machine_page \
    import MachinePage
from spynnaker.pyNN.visualiser_package.visualiser_pages.configuration_page \
    import ConfigPage
from spynnaker.pyNN.utilities import conf


class VisualiserCreationUtility(object):

    def __init__(self, spinnaker):
        self._spinnaker = spinnaker

    def _create_visualiser_interface(self, has_board, transciever,
                                     visualiser_vertices, machine, placements,
                                     router_tables, sim_run_time,
                                     machine_time_step):
        # Start visuliser if requested
        visualiser = None
        #TODO need to make this mapping for the topological pages ABS
        coord_to_low_atom_mapper = None
        if conf.config.getboolean("Visualiser", "enable"):
            wait_for_run = conf.config.getboolean("Visualiser",
                                                  "pause_before_run")
            scope = conf.config.get("Visualiser", "initial_scope")
            x_dim, y_dim = transciever.get_board_dimenions_of_machine()
            #create vis
            visualiser = VisualiserThread(has_board)
            #create basic pages required
            #add basic machine page
            machine_page = MachinePage(True, scope, machine, placements,
                                       router_tables)
            visualiser.add_page(machine_page, machine_page.label)
            #add configuration page
            config_page = ConfigPage(dict(), visualiser_vertices, visualiser,
                                     transciever, has_board, sim_run_time,
                                     machine_time_step,
                                     coord_to_low_atom_mapper)
            visualiser.add_page(config_page, config_page.label)

            if wait_for_run:  # add run now button if required
                visualiser.add_menu_item("Run Now!", self._run_item_selected)

            visualiser.start()
        return visualiser

    def _run_item_selected(self):
        pass

    def _set_visulaiser_port(self, port):
        pass