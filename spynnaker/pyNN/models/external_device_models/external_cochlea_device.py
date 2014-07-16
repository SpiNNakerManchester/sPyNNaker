__author__ = 'stokesa6'
from spynnaker.pyNN.models.abstract_models.abstract_external_device import ExternalDevice


class ExternalCochleaDevice(ExternalDevice):

    def __init__(self, n_neurons, virtual_chip_coords,
                 connected_chip_coords, connected_chip_edge, label=None):
        super(ExternalCochleaDevice, self).__init__(n_neurons,
                                                    virtual_chip_coords,
                                                    connected_chip_coords,
                                                    connected_chip_edge,
                                                    label=label)

    @property
    def model_name(self):
        return "ExternalCochleaDevice:{}".format(self.label)

    def get_resources_for_atoms(self, lo_atom, hi_atom, no_machine_time_steps,
                                machine_time_step_us, partition_data_object):
        raise NotImplementedError