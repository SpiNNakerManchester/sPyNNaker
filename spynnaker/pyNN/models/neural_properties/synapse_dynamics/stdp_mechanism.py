'''
Created on 7 Apr 2014

@author: zzalsar4
'''
from additive_weight_dependence import AdditiveWeightDependence
from weight_based_plastic_synapse_row_io import WeightBasedPlasticSynapseRowIo

WEIGHT_FLOAT_TO_FIXED_SCALE = 16.0
NA_TO_PA_SCALE = 1000.0
SCALE = WEIGHT_FLOAT_TO_FIXED_SCALE * NA_TO_PA_SCALE


class STDPMechanism(object):
    
    def __init__(self, timing_dependence = None, weight_dependence = None, 
            voltage_dependence = None):
        self.timing_dependence = timing_dependence
        self.weight_dependence = weight_dependence
        self.voltage_dependence = voltage_dependence
        
        if not isinstance(weight_dependence, AdditiveWeightDependence):
            raise Exception("weight_dependence must be an AdditiveWeightDependence")

        if self.voltage_dependence != None:
            raise NotImplementedError("voltage_dependence not implemented")

    def __eq__(self, other):
        if (other is None) or (not isinstance(other, self.__class__)):
            return False
        return ((self.timing_dependence == other.timing_dependence)
                and (self.weight_dependence == other.weight_dependence)
                and (self.voltage_dependence == other.voltage_dependence)
                and self.equals(other))
        
    def get_synapse_row_io(self):
        return WeightBasedPlasticSynapseRowIo(
                self._get_synaptic_row_header_words())
        
    def equals(self, other):
        """
        Determines if an object is equal to this object
        """
        raise NotImplementedError
    
    def get_vertex_executable_suffix(self):
        name = "stdp_trace"
        if self.timing_dependence != None:
            name = name + "_" + self.timing_dependence.get_vertex_executable_suffix()

        return name

    def get_params_size(self, vertex, lo_atom, hi_atom):
        """
        Gets the size of the STDP parameters in bytes for a range of atoms
        """
        size = 0
        if self.weight_dependence != None:
            size = size + self.weight_dependence.get_params_size_bytes()

        if self.timing_dependence != None:
            size = size + self.timing_dependence.get_params_size_bytes()
        
        return size
    
    def write_plastic_params(self, spec, region, machineTimeStep, subvertex,
            weight_scale):
        spec.comment("Writing Plastic Parameters")
        
        # Switch focus to the region:
        spec.switchWriteFocus(region)

        # Write weight dependence information to region
        if self.weight_dependence != None:
            self.weight_dependence.write_plastic_params(spec, machineTimeStep, 
                    subvertex, weight_scale)

        if self.timing_dependence != None:
            self.timing_dependence.write_plastic_params(spec, machineTimeStep, 
                    subvertex, weight_scale)

    # **TEMP** timing and weight components should be able to contribute their 
    # own components
    def _get_synaptic_row_header_words(self):
        num_words = 0

        # Allow weight dependance and timing dependance to add to these
        if self.weight_dependence != None:
            num_words += self.weight_dependence.get_synaptic_row_header_words()

        if self.timing_dependence != None:
            num_words += self.timing_dependence.get_synaptic_row_header_words()

        return num_words

