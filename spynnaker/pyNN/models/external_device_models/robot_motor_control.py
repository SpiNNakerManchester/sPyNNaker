from spynnaker.pyNN.models.abstract_models.abstract_component_vertex \
    import ComponentVertex
from spynnaker.pyNN.models.external_device_models.external_motor_device import \
    ExternalMotorDevice
from spynnaker.pyNN.utilities import packet_conversions
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.utilities.conf import config


from pacman.model.graph.edge import Edge
from pacman.model.graph.vertex import Vertex
from pacman.model.resources.cpu_cycles_per_tick_resource import \
    CPUCyclesPerTickResource
from pacman.model.resources.dtcm_resource import DTCMResource
from pacman.model.resources.sdram_resource import SDRAMResource


from data_specification.data_specification_generator import \
    DataSpecificationGenerator
from data_specification.file_data_writer import FileDataWriter


import os
import tempfile

INFINITE_SIMULATION = 4294967295


class RobotMotorControl(ComponentVertex, Vertex):

    PARAMS = 2
    SYSTEM_SIZE = 16
    PARAMS_SIZE = 7 * 4

    CORE_APP_IDENTIFIER = constants.ROBOT_MOTER_CONTROL_CORE_APPLICATION_ID

    def __init__(self, virtual_chip_coords, connected_chip_coords,
                 connected_chip_edge, speed=30, sample_time=4096,
                 update_time=512, delay_time=5, delta_threshold=23,
                 continue_if_not_different=True, label="RobotMotorControl"):
        """
        constructor that depends upon the Component vertex
        """
        ComponentVertex.__init__(self, label)
        Vertex.__init(6, label, constraints=None)
        self._binary = "robot_motor_control.aplx"

        self.virtual_chip_coords = virtual_chip_coords
        self.connected_chip_coords = connected_chip_coords
        self.connected_chip_edge = connected_chip_edge
        self.out_going_edge = None

        self.speed = speed
        self.sample_time = sample_time
        self.update_time = update_time
        self.delay_time = delay_time
        self.delta_threshold = delta_threshold
        self.continue_if_not_different = continue_if_not_different

    def get_dependant_vertexes_edges(self):
        virtual_vertexes = list()
        virtual_edges = list()
        virtual_vertexes.append(
            ExternalMotorDevice(1, self.virtual_chip_coords,
                                self.connected_chip_coords,
                                self.connected_chip_edge))

        self.out_going_edge = Edge(self, virtual_vertexes[0])
        virtual_edges.append(self.out_going_edge)
        return virtual_vertexes, virtual_edges

    def generate_data_spec(self, processor, subvertex, machine_time_step,
                           run_time):
        """
        Model-specific construction of the data blocks necessary to build a
        single external retina device.
        """
        # Create new DataSpec for this processor:
        x, y, p = processor.get_coordinates()
        hostname = processor.chip.machine.hostname
        has_binary_folder_set = \
            config.has_option("SpecGeneration", "Binary_folder")
        if not has_binary_folder_set:
            binary_folder = tempfile.gettempdir()
            config.set("SpecGeneration", "Binary_folder", binary_folder)
        else:
            binary_folder = config.get("SpecGeneration", "Binary_folder")

        binary_file_name = \
            binary_folder + os.sep + "{%s}_dataSpec_{%d}_{%d}_{%d}.dat"\
                                     .format(hostname, x, y, p)

        data_writer = FileDataWriter(binary_file_name)

        spec = DataSpecificationGenerator(data_writer)
        self.write_setup_info(spec, machine_time_step)

        spec.comment("\n*** Spec for robot motor control ***\n\n")

        # Load the expected executable to the list of load targets for this core
        # and the load addresses:
        x, y, p = processor.get_coordinates()

         # Rebuild executable name
        common_binary_path = os.path.join(config.get("SpecGeneration",
                                                     "common_binary_folder"))

        binary_name = os.path.join(common_binary_path,
                                   'robot_motor_control.aplx')

        # No memory writes required for this Data Spec:
        memory_write_targets = list()
        simulation_time_in_ticks = constants.INFINITE_SIMULATION
        if run_time is not None:
            simulation_time_in_ticks = \
                int((run_time * 1000.0) / machine_time_step)
        user1_addr = \
            0xe5007000 + 128 * p + 116  # User1 location reserved for core p
        memory_write_targets.append({'address': user1_addr,
                                     'data': simulation_time_in_ticks})

        #reserve regions
        self.reserve_memory_regions(spec)
        
        #write system info
        spec.switch_write_focus(region=self.SYSTEM_REGION)
        spec.write_value(data=0xBEEF0000)
        spec.write_value(data=0)
        spec.write_value(data=0)
        spec.write_value(data=0)
        edge_key = None
        #locate correct subedge for key
        for subedge in subvertex.out_subedges:
            if subedge.edge == self.out_going_edge:
                edge_key = subedge.key

        #write params to memory
        spec.switch_write_focus(region=self.PARAMS)
        spec.write_value(data=edge_key)
        spec.write_value(data=self.speed)
        spec.write_value(data=self.sample_time)
        spec.write_value(data=self.update_time)
        spec.write_value(data=self.delay_time)
        spec.write_value(data=self.delta_threshold)
        if self.continue_if_not_different:
            spec.write_value(data=1)
        else:
            spec.write_value(data=0)

        # End-of-Spec:
        spec.end_specification()
        data_writer.close()

        # Return list of executables, load files:
        return binary_name, list(), memory_write_targets

    @staticmethod
    def write_setup_info(spec, timer_period):

        # Write this to the system region (to be picked up by the simulation):
        spec.switch_write_focus(region=constants.REGIONS.SYSTEM)
        spec.write_value(data=RobotMotorControl.CORE_APP_IDENTIFIER)
        spec.write_value(data=timer_period)

    def reserve_memory_regions(self, spec):
        """
        Reserve SDRAM space for memory areas:
        1) Area for information on what data to record
        2) area for start commands
        3) area for end commands
        """
        spec.comment("\nReserving memory space for data regions:\n\n")

        # Reserve memory:
        spec.reserveMemRegion(region=self.SYSTEM_REGION,
                              size=self.SYSTEM_SIZE,
                              label='setup')
        
        spec.reserveMemRegion(region=self.PARAMS,
                              size=self.PARAMS_SIZE,
                              label='params')

    @property
    def model_name(self):
        return "Robot Motor Control"

    def get_resources_used_by_atoms(self, lo_atom, hi_atom,
                                    no_machine_time_steps):
        resources = list()
        # noinspection PyTypeChecker
        resources.append(CPUCyclesPerTickResource(0))
        resources.append(DTCMResource(0))
        resources.append(SDRAMResource(self.SYSTEM_SIZE + self.PARAMS_SIZE))
        return resources

    def generate_routing_info(self, subedge):
        """
        overload component method and returns virtual chip key for routing info
        """
        x, y, p = subedge.postsubvertex.placement.processor.get_coordinates()
        key = packet_conversions.get_key_from_coords(x, y, p)
        return key, 0xffff0000
