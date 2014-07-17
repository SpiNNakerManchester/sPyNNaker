from pacman.model.graph.vertex import Vertex
from spynnaker.pyNN.utilities import constants

from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod

@add_metaclass(ABCMeta)
class AbstractDataSpecableVertex(Vertex):

    def __init__(self, n_atoms, label, constraints=None):
        Vertex.__init__(n_atoms, label, constraints)

    @staticmethod
    def write_basic_setup_info(spec, timer_period, runtime_in_timer_tics,
                               core_app_identifier):

        # Write this to the system region (to be picked up by the simulation):
        spec.switch_write_focus(region=constants.REGIONS.SYSTEM)
        spec.write_value(data=core_app_identifier)
        spec.write_value(data=timer_period)
        spec.write_value(data=runtime_in_timer_tics)

    @abstractmethod
    def generate_data_spec(self, processor, subvertex, machine_time_step,
                           run_time):
        """
        method to determine how to generate their data spec for a non neural
        application
        """