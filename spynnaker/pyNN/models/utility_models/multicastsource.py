import os

from spynnaker.pyNN.models.abstract_models.abstract_recordable_vertex import \
    AbstractRecordableVertex
from spynnaker.pyNN import exceptions
from pacman.model.graph.abstract_partitionable_vertex \
    import AbstractPartitionableVertex
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.utilities.conf import config
from spynnaker.pyNN.models.abstract_models.abstract_data_specable_vertex \
    import AbstractDataSpecableVertex


from pacman.model.constraints.key_allocator_routing_constraint \
    import KeyAllocatorRoutingConstraint


from data_specification.data_specification_generator import \
    DataSpecificationGenerator
from data_specification.file_data_writer import FileDataWriter


class MultiCastSource(AbstractRecordableVertex, AbstractDataSpecableVertex,
                      AbstractPartitionableVertex):

    SYSTEM_REGION = 1
    COMMANDS = 2

    CORE_APP_IDENTIFER = constants.MULTICAST_SOURCE_CORE_APPLICATION_ID

    def __init__(self, machine_time_step):
        """
        constructor that depends upon the Component vertex
        """
        AbstractRecordableVertex.__init__(self, "multi_cast_source_sender")
        AbstractDataSpecableVertex.__init__(self, n_atoms=1,
                                            label="multi_cast_source_sender",
                                            machine_time_step=machine_time_step)
        AbstractPartitionableVertex.__init__(
            self, label="multi_cast_source_sender", n_atoms=1,
            max_atoms_per_core=1)

        self._writes = None
        self._memory_requirements = None
        self._edge_map = dict()
        self._commands = list()

        routing_key_constraint =\
            KeyAllocatorRoutingConstraint(self.generate_routing_info)
        self.add_constraint(routing_key_constraint)

    def generate_data_spec(self, processor_chip_x, processor_chip_y,
                           processor_id, subvertex, sub_graph, graph,
                           routing_info, hostname, graph_subgraph_mapper):
        """
        Model-specific construction of the data blocks necessary to build a
        single external retina device.
        """
        #check that all keys for a subedge are the same when masked
        self.check_sub_edge_key_mask_consistancy(self._edge_map, self._app_mask)
        binary_file_name = self.get_binary_file_name(processor_chip_x,
                                                     processor_chip_y,
                                                     processor_id, hostname)

        # Create new DataSpec for this processor:
        data_writer = FileDataWriter(binary_file_name)
        spec = DataSpecificationGenerator(data_writer)

        self._write_basic_setup_info(spec, MultiCastSource.CORE_APP_IDENTIFER)

        spec.comment("\n*** Spec for multi case source ***\n\n")

        #reserve regions
        self.reserve_memory_regions(spec, self._memory_requirements)
        
        #write system region
        spec.switch_write_focus(region=self.SYSTEM_REGION)
        spec.write_value(data=0xBEEF0000)
        spec.write_value(data=0)
        spec.write_value(data=0)
        spec.write_value(data=0)

        #write commands to memory
        spec.switch_write_focus(region=self.COMMANDS)
        for write_command in self._writes:
            spec.write_value(data=write_command)

        # End-of-Spec:
        spec.end_specification()
        data_writer.close()

    def _calculate_memory_requirements(self):
        #sorts commands by timer tic
        commands = sorted(self._commands, key=lambda tup: tup['t'])
        #calculate size of region and the order of writes
        self._writes = list()
        self._memory_requirements = 0
        #temporary holder
        commands_in_same_time_slot = list()
        self._memory_requirements += 12  # 3 ints holding coutners of cp,
                                        # cnp and t
        for start_command in commands:
            # if first command, inltiise counter
            if len(commands_in_same_time_slot) == 0:
                #calculate mem cost of the command based off payload
                self._memory_requirements += self.size_of_message(start_command)
                commands_in_same_time_slot.append(start_command)
                self._writes.append(start_command['t'])
            else:
                # if the next mesage has the same time tic, add to list
                if commands_in_same_time_slot[0]['t'] == start_command['t']:
                    commands_in_same_time_slot.append(start_command)
                    self._memory_requirements += \
                        self.size_of_message(start_command)
                else:  # if not, then send all preivous messages to
                       # region and restart count
                    self.deal_with_command_block(commands_in_same_time_slot)
                    #reset message tracker
                    commands_in_same_time_slot = list()
                    commands_in_same_time_slot.append(start_command)
                    self._memory_requirements += 12  # 3 ints holding coutners
                                                     #  of cp, cnp and t
                    self._memory_requirements += \
                        self.size_of_message(start_command)
                    self._writes.append(start_command['t'])
        # write the last command block left from the loop
        self.deal_with_command_block(commands_in_same_time_slot)
        #add a counter for the entire memory region
        self._writes.insert(0, self._memory_requirements)
        self._memory_requirements += 4

    def add_commands(self, commands, edge):
        self._edge_map[edge] = commands
        self._commands += commands

    def deal_with_command_block(self, commands_in_same_time_slot):
        """
        writes a command block and keeps memory tracker
        """
        #sort by cp
        commands_in_same_time_slot = \
            sorted(commands_in_same_time_slot, key=lambda tup: tup['cp'])

        payload_mesages = \
            self.calcaulate_no_payload_messages(commands_in_same_time_slot)
        self._writes.append(payload_mesages)
        no_payload_messages = len(commands_in_same_time_slot) - payload_mesages
        counter_messages = 0
        # write each command
        for command in commands_in_same_time_slot:
            if counter_messages < payload_mesages:
                self._writes.append(command['key'])
                self._writes.append(command['payload'])
                if command['repeat'] > 0:
                    command_line = (command['repeat'] << 8) | command['delay']
                    self._writes.append(command_line)

            elif counter_messages == payload_mesages:
                self._writes.append(no_payload_messages)
            elif counter_messages > payload_mesages:
                self._writes.append(command['key'])
                if command['repeat'] > 0:
                    command_line = (command['repeat'] << 8) | command['delay']
                    self._writes.append(command_line)
            else:
                self._writes.append(0)
            counter_messages += 1
        # if no payload messgages, still need to report it for c code
        if no_payload_messages == 0:
            self._writes.append(no_payload_messages)

    def generate_routing_info(self, subedge):
        """
        overloaded from component vertex
        """
        if self._edge_map[subedge.edge] is not None:
            return self._edge_map[subedge.edge][0]['key'], 0xFFFFFC00
        else:
            # if the subedge doesnt have any predefined messages to send,
            # then treat them with the subedge routing key
            return subedge.key, self._app_mask

    def reserve_memory_regions(self, spec, command_size):
        """
        Reserve SDRAM space for memory areas:
        1) Area for information on what data to record
        2) area for start commands
        3) area for end commands
        """
        spec.comment("\nReserving memory space for data regions:\n\n")

        # Reserve memory:
        spec.reserve_memory_region(region=self.SYSTEM_REGION,
                                   size=16,
                                   label='setup')
        if command_size > 0:
            spec.reserve_memory_region(region=self.COMMANDS,
                                       size=command_size,
                                       label='commands')

    @staticmethod
    def size_of_message(start_command):
        """
        returns the expected size of the command message
        """
        count = 0
        if start_command['payload'] is None:
            count += 4
        else:
            count += 8
        if start_command['repeat'] > 0:
            count += 4
        return count

    @staticmethod
    def calcaulate_no_payload_messages(messages):
        """
        iterates though a collection of commands and counts how many have
         payloads
        """
        count = 0
        for message in messages:
            if message['payload'] is not None:
                count += 1
        return count

    @staticmethod
    def check_sub_edge_key_mask_consistancy(edge_map, app_mask):
        """
        check that all keys for a subedge are the same when masked
        """
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
                            raise exceptions.RallocException(
                                "The keys going down a speicifc subedge are not"
                                " consistant")

    @property
    def model_name(self):
        """
        return the name of the model
        """
        return "multi_cast_source"

    #inhirrted from partitionable vertex
    def get_cpu_usage_for_atoms(self, lo_atom, hi_atom):
        return 0

    def get_sdram_usage_for_atoms(self, lo_atom, hi_atom, vertex_in_edges):
        if self._memory_requirements is None:
            self._calculate_memory_requirements()
        return self._memory_requirements

    def get_dtcm_usage_for_atoms(self, lo_atom, hi_atom):
        return 0

    def get_binary_name(self):
        # Rebuild executable name
        common_binary_path = os.path.join(config.get("SpecGeneration",
                                                     "common_binary_folder"))

        binary_name = os.path.join(common_binary_path,
                                   'multicast_source.aplx')
        return binary_name