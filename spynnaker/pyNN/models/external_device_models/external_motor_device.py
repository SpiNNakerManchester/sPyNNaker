from spynnaker.pyNN.models.external_device_models.abstract_external_device \
    import ExternalDevice
from pacman.model.constraints.partitioner_maximum_size_constraint\
    import PartitionerMaximumSizeConstraint


class ExternalMotorDevice(ExternalDevice):
    MANAGEMENT_BIT = 0x400
    RATE_CODING_ACTUATORS_ENABLE = 0x40

    def __init__(self, n_neurons, virtual_chip_coords, connected_chip_coords,
                 connected_chip_edge, label=None, neuron_controlled=True):
        super(ExternalMotorDevice, self).__init__(n_neurons,
                                                  virtual_chip_coords,
                                                  connected_chip_coords,
                                                  connected_chip_edge,
                                                  label=label,
                                                  max_atoms_per_core=1)
        self.neuron_controlled = neuron_controlled

    @property
    def model_name(self):
        return "external motor device"

    def get_commands(self, last_runtime_tic):
        return list()
