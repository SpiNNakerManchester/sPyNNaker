from pacman.model.resources import SpecificChipSDRAMResource, \
    PreAllocatedResourceContainer
from spinn_utilities.progress_bar import ProgressBar


class PreAllocateForBitFieldRouterCompressor(object):

    SIZE_OF_SDRAM_ADDRESS_IN_BYTES = 4

    def __call__(self, machine, pre_allocated_resources=None):
        """
        :param pre_allocated_resources: other pre allocated resources
        :param machine: the SpiNNaker machine as discovered
        :return: pre allocated resources
        """

        progress_bar = ProgressBar(
            machine.n_chips, "Pre allocating resources for chip power monitor")

        # for every Ethernet connected chip, get the resources needed by the
        # live packet gatherers
        sdrams = list()

        for chip in progress_bar.over(machine.chips):
            sdrams.append(
                SpecificChipSDRAMResource(
                    chip,
                    (self.SIZE_OF_SDRAM_ADDRESS_IN_BYTES *
                     chip.n_user_processors)))

        # create pre allocated resource container
        pre_allocated_resource_container = PreAllocatedResourceContainer(
            specific_sdram_usage=sdrams)

        # add other pre allocated resources
        if pre_allocated_resources is not None:
            pre_allocated_resource_container.extend(
                pre_allocated_resources)

        # return pre allocated resources
        return pre_allocated_resource_container
