# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from spinn_utilities.overrides import overrides
from data_specification.enums import DataType
from spinn_front_end_common.utilities.constants import (
    MICRO_TO_MILLISECOND_CONVERSION)
from .abstract_neuron_model import AbstractNeuronModel
from .abstract_input_type import AbstractInputType
from spynnaker.pyNN.models.neuron.implementations import (
    AbstractStandardNeuronComponent)

###--Syn and connect params--###
PCONNEC = "pconnec"
Q_EXC = "q_exc"
Q_INH = "q_inh"
TSYN_EXC = "Tsyn_exc"
TSYN_INH = "Tsyn_inh"
EREV_EXC = "Erev_exc"
EREV_INH = "Erev_inh"
NTOT = "Ntot"
GEI = "gei"
EXT_DRIVE = "ext_drive"
AFFERENT_EXC_FRACTION = "afferent_exc_fraction"

GL = "Gl"
CM = "Cm"
EL = "El"

###--transfert function inputs from 'data_test/'+NRN1+'_'+NTWK+'_fit.npy' --###
P0 = "p0"
P1 = "p1"
P2 = "p2"
P3 = "p3"
P4 = "p4"
P5 = "p5"
P6 = "p6"
P7 = "p7"
P8 = "p8"
P9 = "p9"
P10 = "p10"

MUV = "muV"
MUV0 = "muV0"
DMUV0 = "DmuV0"

SV = "sV"
SV0 = "sV0"
DSV0 = "DsV0"

MUGN = "muGn"

TVN = "TvN"
TVN0 = "TvN0"
DTVN0 = "DTvN0"

VTHRE = "Vthre"

FOUT_TH = "Fout_th"

UNITS = {
    ###--Syn connec--###
    PCONNEC: "",
    Q_EXC: "nS",
    Q_INH: "nS",
    TSYN_EXC: "",
    TSYN_INH: "",
    EREV_EXC: "mV",
    EREV_INH: "mV",
    NTOT: "",
    GEI: "",
    EXT_DRIVE: "",
    AFFERENT_EXC_FRACTION: "",
    GL: "Gl",
    CM: "pF",
    EL: "mV",    
    #TF inputs
    P0 : "",
    P1 : "",
    P2 : "",
    P3 : "",
    P4 : "",
    P5 : "",
    P6 : "",
    P7 : "",
    P8 : "",
    P9 : "",
    P10 : "",
    VTHRE: "mV",
    MUV : "",
    MUV0 : "",
    DMUV0 : "",
    SV : "",
    SV0 : "",
    DSV0 : "",
    MUGN : "",
    TVN : "",
    TVN0 : "",
    DTVN0 : "",
    VTHRE : "",
    FOUT_TH : "",
}


class ParamsFromNetwork(AbstractInputType):
    """ Model of neuron due to Eugene M. Izhikevich et al
    """
    __slots__ = [
        "__pconnec", "_q_exc", "_q_inh", "_Tsyn_exc", "_Tsyn_inh",
        "_Erev_exc", "_Erev_inh", "_Ntot",
        "_gei", "_ext_drive", "_afferent_exc_fraction",
        "_Gl", "_Cm", "_El",
        "_p0", "_p1", "_p2", "_p3", "_p4", "_p5",
        "_p6", "_p7", "_p8", "_p9", "_p10",
        "_Vthre", "_muV", "_muV0", "_DmuV0", "_sV", "_sV0", "_DsV0",
        "_muGn", "_TvN", "_TvN0", "_DTvN0", "_Vthre", "_Fout_th",
    ]

    def __init__(self, pconnec,
                 q_exc, q_inh,
                 Tsyn_exc, Tsyn_inh,
                 Erev_exc, Erev_inh,
                 Ntot, gei, ext_drive,
                 afferent_exc_fraction,
                 Gl, Cm, El,
                 p0, p1, p2, p3, p4, p5,
                 p6, p7, p8, p9, p10,
                 muV, muV0,DmuV0,
                 sV, sV0, DsV0,
                 muGn,
                 TvN, TvN0, DTvN0,
                 Vthre, Fout_th):
        """
        :param a: :math:`a`
        :type a: float, iterable(float), ~pyNN.random.RandomDistribution or
            (mapping) function
        :param b: :math:`b`
        :type b: float, iterable(float), ~pyNN.random.RandomDistribution or
            (mapping) function
        :param c: :math:`c`
        :type c: float, iterable(float), ~pyNN.random.RandomDistribution or
            (mapping) function
        :param d: :math:`d`
        :type d: float, iterable(float), ~pyNN.random.RandomDistribution or
            (mapping) function
        :param v_init: :math:`v_{init}`
        :type v_init:
            float, iterable(float), ~pyNN.random.RandomDistribution or
            (mapping) function
        :param u_init: :math:`u_{init}`
        :type u_init:
            float, iterable(float), ~pyNN.random.RandomDistribution or
            (mapping) function
        :param i_offset: :math:`I_{offset}`
        :type i_offset:
            float, iterable(float), ~pyNN.random.RandomDistribution or
            (mapping) function
        """
        super().__init__(
            
            [###--syn and connect--###
             DataType.S1615, #pconnec
             DataType.S1615, #q_exc
             DataType.S1615, #q_inh
             DataType.S1615, #Tsyn_exc
             DataType.S1615, #Tsyn_inh
             DataType.S1615, #Erev_exc
             DataType.S1615, #Erev_inh
             DataType.UINT32, #Ntot
             DataType.S1615, #gei
             DataType.S1615, #ext_drive
             DataType.S1615, #afferent_exc_fraction
             DataType.S1615, #Gm
             DataType.S1615, #Cl
             DataType.S1615, #El
             ###--TF inputs--###
             DataType.S031, #p0
             DataType.S031, #p1
             DataType.S031, #p2
             DataType.S031, #p3
             DataType.S031, #p4
             DataType.S031, #p5
             DataType.S031, #p6
             DataType.S031, #p7
             DataType.S031, #p8
             DataType.S031, #p9
             DataType.S031, #p10
             DataType.S1615,   # muV
             DataType.S1615,   # muV0
             DataType.S1615,   # DmuV0
             DataType.S1615,   # sV
             DataType.S1615,   # sV0
             DataType.S1615,   # DsV0
             DataType.S1615,   # muGn
             DataType.S1615,   # TvN
             DataType.S1615,   # TvN0
             DataType.S1615,   # DTvN0
             DataType.S1615,   # Vthre
             DataType.S1615])   # Fout_th
        
        self.__pconnec = pconnec
        self._q_exc = q_exc
        self._q_inh = q_inh
        self._Tsyn_exc = Tsyn_exc
        self._Tsyn_inh = Tsyn_inh
        self._Erev_exc = Erev_exc
        self._Erev_inh = Erev_inh
        self._Ntot = Ntot
        self._gei = gei
        self._ext_drive = ext_drive
        self._afferent_exc_fraction = afferent_exc_fraction
        self._Gl = Gl
        self._Cm = Cm
        self._El = El        
        self._p0 = p0
        self._p1 = p1
        self._p2 = p2
        self._p3 = p3
        self._p4 = p4
        self._p5 = p5
        self._p6 = p6
        self._p7 = p7
        self._p8 = p8
        self._p9 = p9
        self._p10 = p10        
        self._muV = muV
        self._muV0 = muV0
        self._DmuV0 = DmuV0
        self._sV = sV
        self._sV0 = sV0
        self._DsV0 = DsV0
        self._muGn = muGn
        self._TvN = TvN
        self._TvN0 = TvN0
        self._DTvN0 = DTvN0
        self._Vthre = Vthre
        self._Fout_th = Fout_th

    @overrides(AbstractStandardNeuronComponent.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        # A bit of a guess
        return 150 * n_neurons

    @overrides(AbstractStandardNeuronComponent.add_parameters)
    def add_parameters(self, parameters):
        ###--syn and connec--###
        parameters[PCONNEC] = self.__pconnec
        parameters[Q_EXC] = self._q_exc
        parameters[Q_INH] = self._q_inh
        parameters[TSYN_EXC] = self._Tsyn_exc
        parameters[TSYN_INH] = self._Tsyn_inh
        parameters[EREV_EXC] = self._Erev_exc
        parameters[EREV_INH] = self._Erev_inh
        parameters[NTOT] = self._Ntot
        parameters[GEI] = self._gei
        parameters[EXT_DRIVE] = self._ext_drive
        parameters[AFFERENT_EXC_FRACTION] = self._afferent_exc_fraction
        parameters[GL] = self._Gl
        parameters[CM] = self._Cm
        parameters[EL] = self._El
        ###--TF inputs--###
        parameters[P0] = self._p0
        parameters[P1] = self._p1
        parameters[P2] = self._p2
        parameters[P3] = self._p3
        parameters[P4] = self._p4
        parameters[P5] = self._p5
        parameters[P6] = self._p6
        parameters[P7] = self._p7
        parameters[P8] = self._p8
        parameters[P9] = self._p9
        parameters[P10] = self._p10
        #parameters[MUV] = self._muV
        parameters[MUV0] = self._muV0
        parameters[DMUV0] = self._DmuV0
        parameters[SV0] = self._sV0
        parameters[DSV0] = self._DsV0
        parameters[TVN0] = self._TvN0
        parameters[DTVN0] = self._DTvN0

    @overrides(AbstractStandardNeuronComponent.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[MUV] = self._muV
        state_variables[SV] = self._sV
        state_variables[MUGN] = self._muGn
        state_variables[TVN] = self._TvN
        state_variables[VTHRE] = self._Vthre
        state_variables[FOUT_TH] = self._Fout_th

    @overrides(AbstractStandardNeuronComponent.get_units)
    def get_units(self, variable):
        return UNITS[variable]

    @overrides(AbstractStandardNeuronComponent.has_variable)
    def has_variable(self, variable):
        return variable in UNITS

    @overrides(AbstractNeuronModel.get_global_values)
    def get_global_values(self, ts):
        # pylint: disable=arguments-differ
        pass

    @overrides(AbstractStandardNeuronComponent.get_values)
    def get_values(self, parameters, state_variables, vertex_slice, ts):
        """
        :param ts: machine time step
        """
        # pylint: disable=arguments-differ

        # Add the rest of the data
        return [parameters[PCONNEC],###syn and connect
                parameters[Q_EXC],
                parameters[Q_INH],
                parameters[TSYN_EXC],
                parameters[TSYN_INH],
                parameters[EREV_EXC],
                parameters[EREV_INH],
                parameters[NTOT],
                parameters[GEI],
                parameters[EXT_DRIVE],
                parameters[AFFERENT_EXC_FRACTION],
                parameters[GL],
                parameters[CM],
                parameters[EL],
                parameters[P0],#TF input
                parameters[P1],
                parameters[P2],
                parameters[P3],
                parameters[P4],
                parameters[P5],
                parameters[P6],
                parameters[P7],
                parameters[P8],
                parameters[P9],
                parameters[P10],
                state_variables[MUV],
                parameters[MUV0],
                parameters[DMUV0],
                state_variables[SV],
                parameters[SV0],
                parameters[DSV0],
                state_variables[MUGN],
                state_variables[TVN],
                parameters[TVN0],
                parameters[DTVN0],
                state_variables[VTHRE],
                state_variables[FOUT_TH]
        ]

    @overrides(AbstractStandardNeuronComponent.update_values)
    def update_values(self, values, parameters, state_variables):

        # Decode the values
        (__pconnec, _q_exc, _q_inh, _Tsyn_exc, _Tsyn_inh,
        _Erev_exc, _Erev_inh, _Ntot, _gei, _ext_drive,
        _afferent_exc_fraction,
        _Gl, _Cm, _El,
        _p0, _p1, _p2, _p3, _p4,
        _p5, _p6, _p7, _p8, _p9, _p10,
        muV, _muV0, _DmuV0,
        sV, _sV0, _DsV0,
        muGn,
        TvN, _TvN0, _DTvN0,
        Vthre, Fout_th) = values

        # Copy the changed data only
        state_variables[MUV] = muV
        state_variables[SV] = sV
        state_variables[MUGN] = muGn
        state_variables[TVN] = TvN
        state_variables[VTHRE] = Vthre
        state_variables[FOUT_TH] = Fout_th
        
    @overrides(AbstractInputType.get_global_weight_scale)
    def get_global_weight_scale(self):
        return 1024.0

########################
###--syn and connec--###
########################
    @property
    def pconnec(self):
        return self.__pconnec
    
    @property
    def q_exc(self):
        return self._q_exc

    @property
    def q_inh(self):
        return self._q_inh

    @property
    def Tsyn_exc(self):
        return self._Tsyn_exc

    @property
    def Tsyn_inh(self):
        return self._Tsyn_inh

    @property
    def Erev_exc(self):
        return self._Erev_exc

    @property
    def Erev_inh(self):
        return self._Erev_inh

    @Erev_inh.setter
    def Erev_inh(self, Erev_inh):
        self._Erev_inh = Erev_inh

    @property
    def Ntot(self):
        return self._Ntot

    @property
    def gei(self):
        return self._gei

    @property
    def ext_drive(self):
        return self._ext_drive

    @property
    def afferent_exc_fraction(self):
        return self._afferent_exc_fraction
    
    @property
    def Gl(self):
        return self._Gl

    @property
    def Cm(self):
        return self._Cm

    @property
    def El(self):
        return self._El

###################
###--TF inputs--###
###################

    @property
    def p0(self):
        return self._p0
        
    @property
    def p1(self):
        return self._p1

    @property
    def p2(self):
        return self._p2

    @property
    def p3(self):
        return self._p3

    @property
    def p4(self):
        return self._p4

    @property
    def p5(self):
        return self._p5
        
    @property
    def p6(self):
        return self._p6

    @property
    def p6(self):
        return self._p6

    @property
    def p7(self):
        return self._p7

    @property
    def p8(self):
        return self._p8

    @property
    def p9(self):
        return self._p9

    @property
    def p10(self):
        return self._p10
        
        
    @property
    def muV(self):
        """ Settable model parameter: :math:`a`

        :rtype: float
        """
        return self._muV

    @property
    def muV0(self):
        """ Settable model parameter: :math:`b`

        :rtype: float
        """
        return self._muV0

    @property
    def DmuV0(self):
        """ Settable model parameter: :math:`c`

        :rtype: float
        """
        return self._DmuV0

    @property
    def sV(self):
        """ Settable model parameter: :math:`d`

        :rtype: float
        """
        return self._sV
    
    @property
    def sV0(self):
        """ Settable model parameter: :math:`d`

        :rtype: float
        """
        return self._sV0
    
    @property
    def DsV0(self):
        """ Settable model parameter: :math:`d`

        :rtype: float
        """
        return self._DsV0

    @property
    def muGn(self):
        """ Settable model parameter: :math:`d`

        :rtype: float
        """
        return self._muGn
    
    @property
    def TvN(self):
        """ Settable model parameter: :math:`d`

        :rtype: float
        """
        return self._TvN
    
    @property
    def TvN0(self):
        """ Settable model parameter: :math:`d`

        :rtype: float
        """
        return self._TvN0
    
    @property
    def DTvN0(self):
        """ Settable model parameter: :math:`d`

        :rtype: float
        """
        return self._DTvN0
    
    @property
    def Vthre(self):
        """ Settable model parameter: :math:`d`

        :rtype: float
        """
        return self._Vthre

    @property
    def Fout_th(self):
        """ Settable model parameter: :math:`d`

        :rtype: float
        """
        return self._Fout_th