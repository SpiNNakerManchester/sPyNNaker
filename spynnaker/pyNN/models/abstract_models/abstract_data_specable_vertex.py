from pacman.model.graph.vertex import Vertex
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN import exceptions

from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractDataSpecableVertex(Vertex):

    def __init__(self, n_atoms, label, constraints=None):
        Vertex.__init__(n_atoms, label, constraints)
        self._machine_time_step = None
        self._application_runtime = None
        self._no_machine_time_steps = None

    def _write_basic_setup_info(self, spec, core_app_identifier):

        # Write this to the system region (to be picked up by the simulation):
        spec.switch_write_focus(
            region=constants.POPULATION_BASED_REGIONS.SYSTEM)
        spec.write_value(data=core_app_identifier)
        spec.write_value(data=self._machine_time_step)
        spec.write_value(data=self._no_machine_time_steps)

    @abstractmethod
    def generate_data_spec(self, processor, subvertex, sub_graph, routing_info):
        """
        method to determine how to generate their data spec for a non neural
        application
        """

    @property
    def machine_time_step(self):
        return self._machine_time_step

    @property
    def application_run_time(self):
        return self._application_runtime

    def set_machine_time_step(self, new_machine_time_step):
        if self._machine_time_step is None:
            self._machine_time_step = new_machine_time_step
            if (self._no_machine_time_steps is None and
               self._application_runtime is not None):
                self._no_machine_time_steps = \
                    int((self._application_runtime * 1000.0) /
                        self._machine_time_step)
        else:
            raise exceptions.ConfigurationException(
                "cannot set the machine time step of a given model once it has"
                "already been set")

    def set_application_runtime(self, new_runtime):
        if self._application_runtime is None:
            self._application_runtime = new_runtime
            if (self._no_machine_time_steps is None and
               self._application_runtime is not None):
                self._no_machine_time_steps = \
                    int((self._application_runtime * 1000.0) /
                        self._machine_time_step)
        else:
            raise exceptions.ConfigurationException(
                "cannot set the runtime of a given model once it has"
                "already been set")


