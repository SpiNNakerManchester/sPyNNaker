from spynnaker.pyNN.models.neural_properties.synapse_dynamics.abstract_rules.\
    abstract_time_dependency import AbstractTimeDependency
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.models.neural_properties.synapse_dynamics.abstract_rules.\
    abstract_voltage_dependency import AbstractVoltageDependency
from spynnaker.pyNN.models.neural_properties.synapse_dynamics.abstract_rules.\
    abstract_weight_dependency import AbstractWeightDependency


class STDPMechanism(object):

    def __init__(self, timing_dependence=None, weight_dependence=None,
                 voltage_dependence=None):
        if timing_dependence is not None and \
                not isinstance(timing_dependence, AbstractTimeDependency):
            raise exceptions.ConfigurationException(
                "The timing dependency handed is not a supported time "
                "dependency. Please rectify and try again")
        if weight_dependence is not None and \
                not isinstance(weight_dependence, AbstractWeightDependency):
            raise exceptions.ConfigurationException(
                "The weight dependency handed is not a supported weight "
                "dependency. Please rectify and try again")
        if voltage_dependence is not None and \
                not isinstance(voltage_dependence, AbstractVoltageDependency):
            raise exceptions.ConfigurationException(
                "The voltage dependency handed is not a supported voltage "
                "dependency. Please rectify and try again")

        self.weight_dependence = weight_dependence
        self.timing_dependence = timing_dependence
        self.voltage_dependence = voltage_dependence

    def __eq__(self, other):
        if (other is None) or (not isinstance(other, self.__class__)):
            return False
        return ((self.timing_dependence == other.timing_dependence)
                and (self.weight_dependence == other.weight_dependence)
                and (self.voltage_dependence == other.voltage_dependence)
                and self.equals(other))
        
    def get_synapse_row_io(self):
        if self.timing_dependence is not None:
            return self.timing_dependence.get_synapse_row_io()
        else:
            return None
        
    def equals(self, other):
        """
        Determines if an object is equal to this object
        """
        raise NotImplementedError
    
    def get_vertex_executable_suffix(self):
        name = "stdp"
        if self.timing_dependence is not None:
            name += "_" + self.timing_dependence.get_vertex_executable_suffix()
        if self.weight_dependence is not None:
            name += "_" + self.weight_dependence.get_vertex_executable_suffix()
        return name

    def get_params_size(self):
        """
        Gets the size of the STDP parameters in bytes for a range of atoms
        """
        size = 0
        if self.weight_dependence is not None:
            size += self.weight_dependence.get_params_size_bytes()

        if self.timing_dependence is not None:
            size += self.timing_dependence.get_params_size_bytes()
        
        return size
    
    def write_plastic_params(self, spec, region, machine_time_step, weight_scale):
        spec.comment("Writing Plastic Parameters")
        
        # Switch focus to the region:
        spec.switch_write_focus(region)

        # Write weight dependence information to region
        if self.weight_dependence is not None:
            self.weight_dependence.write_plastic_params(spec, machine_time_step,
                                                        weight_scale)

        if self.timing_dependence is not None:
            self.timing_dependence.write_plastic_params(spec, machine_time_step,
                                                        weight_scale)

    # **TEMP** timing and weight components should be able to contribute their 
    # own components
    def _get_synaptic_row_header_words(self):
        num_words = 0

        # Allow weight dependance and timing dependance to add to these
        if self.weight_dependence is not None:
            num_words += self.weight_dependence.get_synaptic_row_header_words()

        if self.timing_dependence is not None:
            num_words += self.timing_dependence.get_synaptic_row_header_words()

        return num_words