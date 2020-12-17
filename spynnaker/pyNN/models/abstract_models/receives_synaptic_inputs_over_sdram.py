from pacman.model.graphs import AbstractSupportsSDRAMEdges


class ReceivesSynapticInputsOverSDRAM(AbstractSupportsSDRAMEdges):
    """ A marker interface for an object that receives synaptic inputs over
        SDRAM
    """
