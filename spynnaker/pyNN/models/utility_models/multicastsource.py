__author__ = 'stokesa6'
from pacman103.front.common.component_vertex import ComponentVertex
from pacman103.lib import data_spec_constants, data_spec_gen, lib_map
from pacman103.core import exceptions
import os

INFINITE_SIMULATION = 4294967295


class MultiCastSource(ComponentVertex):

    SYSTEM_REGION = 1
    COMMANDS = 2

    core_app_identifier = \
        data_spec_constants.EXTERNAL_RETINA_SETUP_DEVICE_CORE_APPLICATION_ID

    '''
    constructor that depends upon the Component vertex
    '''
    def __init__(self):
        super(MultiCastSource, self).__init__(n_neurons = 1, label="CmdSender")
        self.writes = None
        self.memory_requirements = 0
        self.edge_map = None

    """
        Model-specific construction of the data blocks necessary to build a
        single external retina device.
    """
    def generateDataSpec(self, processor, subvertex, dao):
        #check that all keys for a subedge are the same when masked
        self.check_sub_edge_key_mask_consistancy(self.edge_map, self._app_mask)

        # Create new DataSpec for this processor:
        spec = data_spec_gen.DataSpec(processor=processor, dao=dao)
        spec.initialise(self.core_app_identifier, dao) # User specified identifier

        spec.comment("\n*** Spec for multi case source ***\n\n")

        # Load the expected executable to the list of load targets for this core
        # and the load addresses:
        x, y, p = processor.get_coordinates()
        executable_target = None
        file_path = os.path.join(dao.get_common_binaries_directory(),
                                 'multicast_source.aplx')
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
        self.reserve_memory_regions(spec, self.memory_requirements)
        
        #write system region
        spec.switchWriteFocus(region = self.SYSTEM_REGION)
        spec.write(data = 0xBEEF0000)
        spec.write(data = 0)
        spec.write(data = 0)
        spec.write(data = 0)

        #write commands to memory
        spec.switchWriteFocus(region=self.COMMANDS)
        for write_command in self.writes:
            spec.write(data=write_command)

        # End-of-Spec:
        spec.endSpec()
        spec.closeSpecFile()
        load_targets = list()

        # Return list of executables, load files:
        return executable_target, load_targets, memory_write_targets

    def calculate_memory_requirements(self, no_tics):
        #go through the vertexes at the end of the outgoing edges and ask them
        commands, self.edge_map = self.collect_commands(no_tics)
        #sorts commands by timer tic
        commands = sorted(commands, key=lambda tup: tup['t'])
        #calculate size of region and the order of writes
        self.writes = list()
        self.memory_requirements = 0
        #temporary holder
        commands_in_same_time_slot = list()
        self.memory_requirements += 12 # 3 ints holding coutners of cp, cnp and t
        for start_command in commands:
            # if first command, inltiise counter
            if len(commands_in_same_time_slot) == 0:
                #calculate mem cost of the command based off payload
                self.memory_requirements += self.size_of_message(start_command)
                commands_in_same_time_slot.append(start_command)
                self.writes.append(start_command['t'])
            else:
                # if the next mesage has the same time tic, add to list
                if commands_in_same_time_slot[0]['t'] == start_command['t']:
                    commands_in_same_time_slot.append(start_command)
                    self.memory_requirements += self.size_of_message(start_command)
                else:#if not, then send all preivous messages to region and restart count
                    self.deal_with_command_block(commands_in_same_time_slot)
                    #reset message tracker
                    commands_in_same_time_slot = list()
                    commands_in_same_time_slot.append(start_command)
                    self.memory_requirements += 12 # 3 ints holding coutners of cp, cnp and t
                    self.memory_requirements += self.size_of_message(start_command)
                    self.writes.append(start_command['t'])
        # write the last command block left from the loop
        self.deal_with_command_block(commands_in_same_time_slot)
        #add a counter for the entire memory region
        self.writes.insert(0, self.memory_requirements)
        self.memory_requirements += 4


    '''
    check that all keys for a subedge are the same when masked
    '''
    def check_sub_edge_key_mask_consistancy(self, edge_map, app_mask):
        for subedge in edge_map.keys():
            combo = None
            commands = edge_map[subedge]
            if commands is not None:
                for command in commands:
                    if combo is None:
                        combo = command['key'] & app_mask
                    else:
                        new_combo = command['key'] & app_mask
                        if combo != new_combo:
                            raise exceptions.RallocException("The keys going down a "
                                                             "speicifc subedge are not"
                                                             " consistant")

    '''
    iterates though a collection of commands and counts how many have payloads
    '''
    def calcaulate_no_payload_messages(self, messages):
        count = 0
        for message in messages:
            if message['payload'] is not None:
                count += 1
        return count

    '''
    collects all the commands from its out going edges
    '''
    def collect_commands(self, no_tics):
        commands = list()
        edge_map = dict()
        for outgoing_edge in self.out_edges:
            destination_vertex = outgoing_edge.postvertex
            dv_commands = destination_vertex.get_commands(no_tics)
            if dv_commands is not None:
                edge_map[outgoing_edge] = dv_commands
                commands += dv_commands
            else:
                edge_map[outgoing_edge] = None
        return commands, edge_map

    '''
    writes a command block and keeps memory tracker
    '''
    def deal_with_command_block(self, commands_in_same_time_slot):
        #sort by cp
        commands_in_same_time_slot = \
            sorted(commands_in_same_time_slot, key=lambda tup: tup['cp'])

        payload_mesages = \
            self.calcaulate_no_payload_messages(commands_in_same_time_slot)
        self.writes.append(payload_mesages)
        no_payload_messages = len(commands_in_same_time_slot) - payload_mesages
        counter_messages = 0
        # write each command
        for command in commands_in_same_time_slot:
            if counter_messages < payload_mesages:
                self.writes.append(command['key'])
                self.writes.append(command['payload'])
                if command['repeat'] > 0:
                    command_line = (command['repeat'] << 8) | command['delay']
                    self.writes.append(command_line)

            elif counter_messages == payload_mesages:
                self.writes.append(no_payload_messages)
            elif counter_messages > payload_mesages:
                self.writes.append(command['key'])
                if command['repeat'] > 0:
                    command_line = (command['repeat'] << 8) | command['delay']
                    self.writes.append(command_line)
            else:
                self.writes.append(0)
            counter_messages += 1
        # if no payload messgages, still need to report it for c code
        if no_payload_messages == 0:
            self.writes.append(no_payload_messages)

    '''
    overloaded
    '''
    def generate_routing_info( self, subedge ):
        if self.edge_map[subedge.edge] is not None:
            return self.edge_map[subedge.edge][0]['key'], 0xFFFFFC00
        else:
            # if the subedge doesnt have any predefined messages to send,
            # then treat them with the subedge routing key
            return subedge.key, self._app_mask



    '''
    returns the expected size of the command message
    '''
    def size_of_message(self, start_command):
        count = 0
        if start_command['payload'] is None:
            count += 4
        else:
            count += 8
        if start_command['repeat'] > 0:
            count += 4
        return count

    def reserve_memory_regions(self, spec, command_size):
        """
        Reserve SDRAM space for memory areas:
        1) Area for information on what data to record
        2) area for start commands
        3) area for end commands
        """
        spec.comment("\nReserving memory space for data regions:\n\n")

        # Reserve memory:
        spec.reserveMemRegion(region=self.SYSTEM_REGION,
                              size=16,
                              label='setup')
        if command_size > 0:
            spec.reserveMemRegion(region=self.COMMANDS,
                                  size=command_size,
                                  label='commands')

    def get_maximum_atoms_per_core(self):
        '''
        return the maximum number of atoms needed for the multi-cast source
        '''
        return 1


    def model_name(self):
        '''return the name of the model
        '''
        return "multi_cast_source"

    def get_resources_for_atoms(self, lo_atom, hi_atom, no_machine_time_steps,
                                machine_time_step_us, partition_data_object):
        '''return the resources of the multi-cast source
        '''
        if self.writes is None:
            self.calculate_memory_requirements(no_machine_time_steps)
        return lib_map.Resources(0, 0, self.memory_requirements)
