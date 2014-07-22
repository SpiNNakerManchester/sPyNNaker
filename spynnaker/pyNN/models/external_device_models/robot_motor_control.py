from spynnaker.pyNN.models.abstract_models.abstract_component_vertex \
    import AbstractComponentVertex
from spynnaker.pyNN.models.abstract_models.abstract_data_specable_vertex import \
    AbstractDataSpecableVertex
from spynnaker.pyNN.models.external_device_models.external_motor_device import \
    ExternalMotorDevice
from spynnaker.pyNN.utilities import packet_conversions
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.utilities.conf import config


from pacman.model.graph.edge import Edge
from pacman.model.resources.cpu_cycles_per_tick_resource import \
    CPUCyclesPerTickResource
from pacman.model.resources.dtcm_resource import DTCMResource
from pacman.model.resources.sdram_resource import SDRAMResource


from data_specification.data_specification_generator import \
    DataSpecificationGenerator
from data_specification.file_data_writer import FileDataWriter


import os


class RobotMotorControl(AbstractComponentVertex, AbstractDataSpecableVertex):

    PARAMS = 2
    SYSTEM_SIZE = 16
    PARAMS_SIZE = 7 * 4

    CORE_APP_IDENTIFIER = constants.ROBOT_MOTER_CONTROL_CORE_APPLICATION_ID

    def __init__(self, virtual_chip_coords, connected_chip_coords,
                 connected_chip_edge,
                 speed=30, sample_time=4096,
                 update_time=512, delay_time=5, delta_threshold=23,
                 continue_if_not_different=True, label="RobotMotorControl"):
        """
        constructor that depends upon the Component vertex
        """
        AbstractComponentVertex.__init__(self, label)
        AbstractDataSpecableVertex.__init(n_atoms=6, label=label,
                                          constraints=None)
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

    def generate_data_spec(self, processor, subvertex):
        """
        Model-specific construction of the data blocks necessary to build a
        single external retina device.
        """
        # Create new DataSpec for this processor:
        binary_file_name = self.get_binary_file_name(processor)

        data_writer = FileDataWriter(binary_file_name)
        spec = DataSpecificationGenerator(data_writer)

        self._write_basic_setup_info(spec, RobotMotorControl.CORE_APP_IDENTIFER)

        spec.comment("\n*** Spec for robot motor control ***\n\n")

         # Rebuild executable name
        common_binary_path = os.path.join(config.get("SpecGeneration",
                                                     "common_binary_folder"))

        binary_name = os.path.join(common_binary_path,
                                   'robot_motor_control.aplx')

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
        return binary_name, list(), list()

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

    def get_resources_used_by_atoms(self, lo_atom, hi_atom):
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