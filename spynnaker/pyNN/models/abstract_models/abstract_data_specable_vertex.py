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

    def __init__(self, n_atoms, label, machine_time_step, constraints=None):
        Vertex.__init__(self, n_atoms, label, constraints)
        self._machine_time_step = machine_time_step
        self._application_runtime = None
        self._no_machine_time_steps = None

    def _write_basic_setup_info(self, spec, core_app_identifier):

        # Write this to the system region (to be picked up by the simulation):
        spec.switch_write_focus(
            region=constants.POPULATION_BASED_REGIONS.SYSTEM.value)
        spec.write_value(data=core_app_identifier)
        spec.write_value(data=self._machine_time_step)
        spec.write_value(data=self._no_machine_time_steps)

    @abstractmethod
    def generate_data_spec(self, processor_chip_x, processor_chip_y,
                           processor_id, subvertex, sub_graph, graph,
                           routing_info, hostname, graph_subgraph_mapper):
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
    def no_machine_time_steps(self):
        return self._no_machine_time_steps

    @property
    def application_run_time(self):
        return self._application_runtime

    def set_application_runtime(self, new_runtime):
        if self._application_runtime is None:
            self._application_runtime = new_runtime
        else:
            raise exceptions.ConfigurationException(
                "cannot set the runtime of a given model once it has"
                "already been set")

    def set_no_machine_time_steps(self, new_no_machine_time_steps):
        if self._no_machine_time_steps is None:
            self._no_machine_time_steps = new_no_machine_time_steps
        else:
            raise exceptions.ConfigurationException(
                "cannot set the number of machine time steps of a given"
                " model once it has already been set")



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
            binary_folder + os.sep + "{}_dataSpec_{}_{}_{}.dat"\
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
            binary_folder + os.sep + "{}_appData_{}_{}_{}.dat"\
                                     .format(hostname, processor_chip_x,
                                             processor_chip_y,
                                             processor_id)

    @staticmethod
    def get_mem_write_base_address(processor_id):
        return 0xe5007000 + 128 * processor_id + 112
