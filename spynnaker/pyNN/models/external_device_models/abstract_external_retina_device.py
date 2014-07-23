from spynnaker.pyNN.models.external_device_models.abstract_external_device \
    import ExternalDevice
from pacman.model.constraints.placer_chip_and_core_constraint \
    import PlacerChipAndCoreConstraint
from pacman.model.constraints.partitioner_maximum_size_constraint\
    import PartitionerMaximumSizeConstraint


class AbstractExternalRetinaDevice(ExternalDevice):

    UP_POLARITY = "UP"
    DOWN_POLARITY = "DOWN"
    MERGED_POLARITY = "MERGED"

    def __init__(self, n_neurons, virtual_chip_coords, connected_node_coords,
                 connected_node_edge, polarity, label=None):

        ExternalDevice.__init__(
            self, n_neurons, virtual_chip_coords, connected_node_coords,
            connected_node_edge, label=label,
            max_atoms_per_core=self._get_max_atoms_per_core())

        self._get_max_atoms_per_core()
        self.polarity = polarity

    @property
    def requires_retina_page(self):
        return True

    @property
    def requires_multi_cast_source(self):
        return True

    def add_constraints_to_subverts(self, subverts):
        ordered_subverts = sorted(subverts, key=lambda x: x.lo_atom)

        start_point = 0
        if self.polarity == AbstractExternalRetinaDevice.UP_POLARITY:
            start_point = 8

        for subvert in ordered_subverts:
            constraint = \
                PlacerChipAndCoreConstraint(self._virtual_chip_coords['x'],
                                            self._virtual_chip_coords['y'],
                                            start_point)
            subvert.add_constraint(constraint)
            start_point += 1

    def _get_max_atoms_per_core(self):
        if (self.atoms >> 11) <= 0:  # if the keys dont touce p,
                                     # then just 1 subvert is needed
            return 1
        else:
            return self.atoms >> 11
