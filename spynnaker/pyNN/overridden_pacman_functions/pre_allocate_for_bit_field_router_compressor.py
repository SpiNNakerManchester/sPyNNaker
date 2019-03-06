from pacman.model.resources import SpecificChipSDRAMResource, \
    PreAllocatedResourceContainer
from spinn_utilities.progress_bar import ProgressBar
from spynnaker.pyNN.overridden_pacman_functions.compression\
    .machine_bit_field_router_compressor import \
    SIZE_OF_SDRAM_ADDRESS_IN_BYTES


class PreAllocateForBitFieldRouterCompressor(object):

    def __call__(self, machine, sdram_to_pre_alloc_for_bit_fields,
                 pre_allocated_resources=None):
        """
        :param pre_allocated_resources: other pre allocated resources
        :param sdram_to_pre_alloc_for_bit_fields: sdram end user managed to \
        help with bitfield compressions
        :param machine: the SpiNNaker machine as discovered
        :return: pre allocated resources
        """

        progress_bar = ProgressBar(
            machine.n_chips, "Pre allocating resources for bit field ")

        # for every Ethernet connected chip, get the resources needed by the
        # live packet gatherers
        sdrams = list()

        for chip in progress_bar.over(machine.chips):
            sdrams.append(
                SpecificChipSDRAMResource(
                    chip,
                    (SIZE_OF_SDRAM_ADDRESS_IN_BYTES *
                     chip.n_user_processors) +
                    sdram_to_pre_alloc_for_bit_fields))

        # create pre allocated resource container
        pre_allocated_resource_container = PreAllocatedResourceContainer(
            specific_sdram_usage=sdrams)

        # add other pre allocated resources
        if pre_allocated_resources is not None:
            pre_allocated_resource_container.extend(
                pre_allocated_resources)

        # return pre allocated resources
        return pre_allocated_resource_container
