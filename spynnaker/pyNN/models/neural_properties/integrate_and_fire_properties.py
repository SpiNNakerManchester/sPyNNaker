__author__ = 'stokesa6'
import numpy
class IF_Properties(object):

    def initialize_v(self, value):
        self.v_init = self.convert_param(value, self.atoms)

    def r_membrane(self, machineTimeStep):
        return ((1000.0 * self.tau_m) 
                / (self.cm * float(machineTimeStep)))

    def exp_tc(self, machineTimeStep):
        return numpy.exp(float(-machineTimeStep) / (1000.0 * self.tau_m))
        
    def ioffset(self, machineTimeStep):
        return self.i_offset / (1000.0 / float(machineTimeStep))

    @property
    def one_over_tauRC(self):
        return 1.0 / self.tau_m
