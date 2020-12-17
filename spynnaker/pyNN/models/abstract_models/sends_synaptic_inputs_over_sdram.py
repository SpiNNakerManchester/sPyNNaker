from pacman.model.graphs import AbstractSupportsSDRAMEdges


class SendsSynapticInputsOverSDRAM(AbstractSupportsSDRAMEdges):
    """ A marker interface for an object that sends synaptic inputs over SDRAM
    """
