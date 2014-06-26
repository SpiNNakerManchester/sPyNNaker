class AbstractConnector(object):
    """
    Abstract class which connectors extend
    """
        
    def generate_synapse_list(self, prevertex, postvertex, delay_scale, 
                              synapse_type):
        """
        Generate a list of synapses that can be queried for information and
        connectivity.  Note that this doesn't actually have to store the
        explicit information, as long as it produces the correct information!
        """
        raise NotImplementedError

