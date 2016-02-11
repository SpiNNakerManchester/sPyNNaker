
# pacman imports
from pacman.interfaces.abstract_provides_provenance_data import \
    AbstractProvidesProvenanceData

# spinn front end common imports
from pacman.utilities.utility_objs.provenance_data_item import \
    ProvenanceDataItem
from spinn_front_end_common.interface.buffer_management.buffer_models.\
    abstract_receive_buffers_to_host import \
    AbstractReceiveBuffersToHost
from spinn_front_end_common.utilities import helpful_functions
from spinn_front_end_common.utility_models.\
    provides_provenance_partitioned_vertex import \
    ProvidesProvenancePartitionedVertex
from spinn_front_end_common.utilities import constants as common_constants

# data spec imports
from data_specification import utility_calls as data_specification_utilities

# spynnaker imports
from spynnaker.pyNN.utilities import constants

# general imports
import struct


class FAKEIFCurrExpPartitioned(
        AbstractReceiveBuffersToHost, ProvidesProvenancePartitionedVertex):
    """ Represents a sub-set of atoms from a AbstractConstrainedVertex
    """

    def __init__(
            self, buffering_output, resources_required, label,
            no_machine_time_steps, constraints=None):
        """
        :param buffering_output: True if the vertex is set to buffer output,\
                    False otherwise
        :param resources_required: The approximate resources needed for\
                    the vertex
        :type resources_required:\
                    :py:class:`pacman.models.resources.resource_container.ResourceContainer`
        :param label: The name of the subvertex
        :type label: str
        :param no_machine_time_steps: the number of machine time steps this
                model should run for.
        :type no_machine_time_steps: int
        :param constraints: The constraints of the subvertex
        :type constraints: iterable of\
                    :py:class:`pacman.model.constraints.abstract_constraint\
                    .AbstractConstraint`
        :raise pacman.exceptions.PacmanInvalidParameterException:
                    * If one of the constraints is not valid
        """
        AbstractReceiveBuffersToHost.__init__(self)

        ProvidesProvenancePartitionedVertex.__init__(
            self, resources_required=resources_required, label=label,
            constraints=constraints, provenance_region_id=
            constants.POPULATION_BASED_REGIONS.PROVENANCE_DATA.value)
        AbstractProvidesProvenanceData.__init__(self)

        self._buffering_output = buffering_output
        self._no_machine_time_step = no_machine_time_steps

    def buffering_output(self):
        return self._buffering_output

    def is_receives_buffers_to_host(self):
        return True

    def get_provenance_data_items(
            self, transceiver, placement=None):
        """ Write the provenance data using XML
        :param transceiver: the SpinnMan interface object
        :param placement: the placement object for this subvertex or None if\
                    the system does not require a placement object
        :return: None
        """

        basic_provenance_entries = ProvidesProvenancePartitionedVertex.\
            get_provenance_data_items(self, transceiver, placement)

        # TODO this needs to be moved, once sergio's and rowley's branches are merged.
        # Get the App Data base address for the core
        # (location where this cores memory starts in sdram and region table)
        app_data_base_address = transceiver.get_cpu_information_from_core(
            placement.x, placement.y, placement.p).user[0]
        provenance_data_region_base_address = \
            data_specification_utilities.get_region_base_address_offset(
                app_data_base_address,
                constants.POPULATION_BASED_REGIONS.PROVENANCE_DATA.value)
        provenance_data_region_base_address_offset = \
            helpful_functions.read_data(
                placement.x, placement.y, provenance_data_region_base_address,
                4, "<I", transceiver)

        # deduce the base address location for the provenance data region in
        # sdram
        provenance_data_base_address =\
            provenance_data_region_base_address_offset + app_data_base_address
        # compensate for basic prov reading
        provenance_data_base_address += \
            common_constants.PROVENANCE_DATA_REGION_SIZE_IN_BYTES

        # todo this was a function call, but alas the call only returned the first
        # get data from the machine
        data = buffer(transceiver.read_memory(
            placement.x, placement.y, provenance_data_base_address,
            constants.PROVENANCE_DATA_REGION_SIZE_IN_BYTES))
        provenance_data = struct.unpack_from("<IIII", data)

        # translate into provenance data items
        basic_provenance_entries.append(ProvenanceDataItem(
            name="Times_synaptic_weights_have_saturated",
            item=provenance_data[
                constants.PROVENANCE_DATA_ENTRIES.SATURATION_COUNT.value],
            needs_reporting_to_end_user=provenance_data[
                constants.PROVENANCE_DATA_ENTRIES.SATURATION_COUNT.value] > 0,
            message_to_end_user=
            "The weights from the synapses saturated on {} occasions. "
            "If this is not expected, you can increase the "
            "\"spikes_per_second\" and / or \"ring_buffer_sigma\" "
            "values located within the .spynnaker.cfg file."
            .format(provenance_data[
                constants.PROVENANCE_DATA_ENTRIES.SATURATION_COUNT.value])))
        basic_provenance_entries.append(ProvenanceDataItem(
            name="Times_the_input_buffer_lost_packets",
            item=provenance_data[
                constants.PROVENANCE_DATA_ENTRIES.BUFFER_OVERFLOW_COUNT.value],
            needs_reporting_to_end_user=provenance_data[
                constants.PROVENANCE_DATA_ENTRIES.
                BUFFER_OVERFLOW_COUNT.value] > 0,
            message_to_end_user=
            "The input buffer lost packets on {} occasions. This is "
            "often a sign that the system is running too quickly for the"
            " number of neurons per core, please increase the timer_tic "
            "or time_scale_factor or decrease the number of neurons "
            "per core.".format(provenance_data[
                constants.PROVENANCE_DATA_ENTRIES.
                BUFFER_OVERFLOW_COUNT.value])))
        basic_provenance_entries.append(ProvenanceDataItem(
            name="Total_pre_synaptic_events",
            item=provenance_data[constants.PROVENANCE_DATA_ENTRIES.
                                 PRE_SYNAPTIC_EVENT_COUNT.value],
            needs_reporting_to_end_user=False))
        last_timer_tic = provenance_data[
            constants.PROVENANCE_DATA_ENTRIES.CURRENT_TIMER_TIC.value]
        basic_provenance_entries.append(ProvenanceDataItem(
            name="Last_timer_tic_the_core_ran_to",
            item=last_timer_tic,
            needs_reporting_to_end_user=
            last_timer_tic != (self._no_machine_time_step / 10),
            message_to_end_user=
            "The core at {}:{}:{} was at timer tic {} when it should have been"
            " at timer tic {}. It was forcefully closed".format(
                placement.x, placement.y, placement.p, last_timer_tic,
                (self._no_machine_time_step / 10))))
        return basic_provenance_entries

