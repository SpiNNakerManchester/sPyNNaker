class STDPMechanism(object):
    def __init__(self, timing_dependence=None, weight_dependence=None,
                 voltage_dependence=None, dendritic_delay_fraction=1.0):
        self.timing_dependence = timing_dependence
        self.weight_dependence = weight_dependence
        self.voltage_dependence = voltage_dependence
        self.dendritic_delay_fraction = dendritic_delay_fraction
        
        if self.dendritic_delay_fraction < 0.5 or self.dendritic_delay_fraction > 1.0:
            raise NotImplementedError("SpiNNaker only supports dendritic delay fractions in the interval [0.5, 1.0]")
        
        if self.voltage_dependence is not None:
            raise NotImplementedError("voltage_dependence not implemented")

    def __eq__(self, other):
        if (other is None) or (not isinstance(other, self.__class__)):
            return False
        return ((self.timing_dependence == other.timing_dependence)
                and (self.weight_dependence == other.weight_dependence)
                and (self.voltage_dependence == other.voltage_dependence)
                and (self.dendritic_delay_fraction == other.dendritic_delay_fraction)
                and self.equals(other))
        
    def get_synapse_row_io(self):
        if self.timing_dependence is not None:
            return self.timing_dependence.get_synapse_row_io(self.dendritic_delay_fraction)
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
    
    def are_weights_signed(self):
        return False
    
    def get_max_weight(self):
        if self.weight_dependence != None:
            return self.weight_dependence.w_max
        else:
            return 0.0

    def get_params_size(self):
        """
        Gets the size of the STDP parameters in bytes for a range of atoms
        """
        size = 0
        num_terms = 1
        if self.timing_dependence is not None:
            size += self.timing_dependence.get_params_size_bytes()
            num_terms = self.timing_dependence.get_num_terms()

        if self.weight_dependence is not None:
            size += self.weight_dependence.get_params_size_bytes(num_terms)    
        
        return size
    
    def write_plastic_params(self, spec, region, machine_time_step, weight_scale):
        spec.comment("Writing Plastic Parameters")
        
        # Switch focus to the region:
        spec.switch_write_focus(region)

        num_terms = 1
        if self.timing_dependence is not None:
            self.timing_dependence.write_plastic_params(spec, machine_time_step, weight_scale)
            num_terms = self.timing_dependence.get_num_terms()

        # Write weight dependence information to region
        if self.weight_dependence is not None:
            self.weight_dependence.write_plastic_params(spec, machine_time_step, weight_scale, num_terms)

       
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