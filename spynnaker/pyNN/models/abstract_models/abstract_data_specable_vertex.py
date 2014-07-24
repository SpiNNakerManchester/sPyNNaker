from pacman.model.graph.vertex import Vertex
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.utilities.conf import config
from spynnaker.pyNN import exceptions

from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod

import tempfile
import os


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
    def generate_data_spec(self, processor_chip_x, processor_chip_y,
                           processor_id, subvertex, sub_graph, routing_info,
                           hostname, graph_subgraph_mapper):
        """
        method to determine how to generate their data spec for a non neural
        application
        """

    @abstractmethod
    def get_binary_name(self):
        """
        method to return the binary name for a given dataspecable vertex
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

    @staticmethod
    def get_binary_file_name(processor_chip_x, processor_chip_y,
                             processor_id, hostname):
        has_binary_folder_set = \
            config.has_option("SpecGeneration", "Binary_folder")
        if not has_binary_folder_set:
            binary_folder = tempfile.gettempdir()
            config.set("SpecGeneration", "Binary_folder", binary_folder)
        else:
            binary_folder = config.get("SpecGeneration", "Binary_folder")

        binary_file_name = \
            binary_folder + os.sep + "{%s}_dataSpec_{%d}_{%d}_{%d}.dat"\
                                     .format(hostname, processor_chip_x,
                                             processor_chip_y,
                                             processor_id)
        return binary_file_name

    @staticmethod
    def get_application_data_file_name(processor_chip_x, processor_chip_y,
                                       processor_id, hostname):
        has_binary_folder_set = \
            config.has_option("SpecGeneration", "Binary_folder")
        if not has_binary_folder_set:
            binary_folder = tempfile.gettempdir()
            config.set("SpecGeneration", "Binary_folder", binary_folder)
        else:
            binary_folder = config.get("SpecGeneration", "Binary_folder")

        binary_file_name = \
            binary_folder + os.sep + "{%s}_appData_{%d}_{%d}_{%d}.dat"\
                                     .format(hostname, processor_chip_x,
                                             processor_chip_y,
                                             processor_id)
