__author__ = 'stokesa6'
from pacman103.front.common.population_vertex import PopulationVertex
from pacman103.front.common.external_motor_device import ExternalMotorDevice
from pacman103.lib import data_spec_constants, data_spec_gen, lib_map
from pacman103.lib.graph.edge import Edge
from pacman103.core.utilities import packet_conversions
from pacman103.core import exceptions
import os

INFINITE_SIMULATION = 4294967295


class RobotMotorControl(PopulationVertex):

    SYSTEM_REGION = 1
    PARAMS = 2
    SYSTEM_SIZE = 16
    PARAMS_SIZE = 7 * 4

    core_app_identifier = \
        data_spec_constants.EXTERNAL_RETINA_SETUP_DEVICE_CORE_APPLICATION_ID

    '''
    constructor that depends upon the Component vertex
    '''
    def __init__(self, n_neurons, virtual_chip_coords, connected_chip_coords,
                 connected_chip_edge, speed = 30, sample_time = 4096,
                 update_time = 512, delay_time = 5, delta_threshold = 23,
                 continue_if_not_different = True, label="RobotMotorControl"):
        super(RobotMotorControl, self).__init__(n_neurons = 6, n_params = 3,
            binary = "robot_motor_control.aplx", label=label)

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



    """
        Model-specific construction of the data blocks necessary to build a
        single external retina device.
    """
    def generateDataSpec(self, processor, subvertex, dao):

        # Create new DataSpec for this processor:
        spec = data_spec_gen.DataSpec(processor=processor, dao=dao)
        spec.initialise(self.core_app_identifier, dao) # User specified identifier

        spec.comment("\n*** Spec for robot motor control ***\n\n")

        # Load the expected executable to the list of load targets for this core
        # and the load addresses:
        x, y, p = processor.get_coordinates()
        file_path = os.path.join(dao.get_common_binaries_directory(),
                                 'robot_motor_control.aplx')
        executable_target = lib_map.ExecutableTarget(file_path, x, y, p)
        memory_write_targets = list()

        simulationTimeInTicks = INFINITE_SIMULATION
        if dao.run_time is not None:
            simulationTimeInTicks = int((dao.run_time * 1000.0) 
                    /  dao.machineTimeStep)
        user1Addr = 0xe5007000 + 128 * p + 116 # User1 location reserved for core p
        memory_write_targets.append(lib_map.MemWriteTarget(x, y, p, user1Addr,
                                                           simulationTimeInTicks))

        #reserve regions
        self.reserve_memory_regions(spec)
        
        #write system info
        spec.switchWriteFocus(region = self.SYSTEM_REGION)
        spec.write(data = 0xBEEF0000)
        spec.write(data = 0)
        spec.write(data = 0)
        spec.write(data = 0)
        edge_key = None
        #locate correct subedge for key
        for subedge in subvertex.out_subedges:
            if subedge.edge == self.out_going_edge:
                edge_key = subedge.key


        #write params to memory

        spec.switchWriteFocus(region=self.PARAMS)
        spec.write(data=edge_key)
        spec.write(data=self.speed)
        spec.write(data=self.sample_time)
        spec.write(data=self.update_time)
        spec.write(data=self.delay_time)
        spec.write(data=self.delta_threshold)
        if (self.continue_if_not_different):
            spec.write(data=1)
        else:
            spec.write(data=0)

        # End-of-Spec:
        spec.endSpec()
        spec.closeSpecFile()
        load_targets = list()

        # Return list of executables, load files:
        return executable_target, load_targets, memory_write_targets

    """
        Reserve SDRAM space for memory areas:
        1) Area for information on what data to record
        2) area for start commands
        3) area for end commands
    """
    def reserve_memory_regions(self, spec):
        spec.comment("\nReserving memory space for data regions:\n\n")

        # Reserve memory:
        spec.reserveMemRegion(region=self.SYSTEM_REGION,
                              size=self.SYSTEM_SIZE,
                              label='setup')
        
        spec.reserveMemRegion(region=self.PARAMS,
                              size=self.PARAMS_SIZE,
                              label='params')

    '''
    returns the maximum number of atoms needed for the multi-cast source
    '''
    def get_maximum_atoms_per_core(self):
        return 6

    '''
    returns the name of the model
    '''
    def model_name(self):
        return "Robot Motor Control"

    '''
    returns the resources of the multi-cast source
    '''
    def get_resources_for_atoms(self, lo_atom, hi_atom, no_machine_time_steps,
                                machine_time_step_us, partition_data_object):
        return lib_map.Resources(0, 0, self.SYSTEM_SIZE + self.PARAMS_SIZE)

    '''
    overload component method and returns virtual chip key for routing info
    '''
    def generate_routing_info(self, subedge):
        x, y, p = subedge.postsubvertex.placement.processor.get_coordinates()
        key = packet_conversions.get_key_from_coords(x, y, p)
        return key, 0xffff0000
