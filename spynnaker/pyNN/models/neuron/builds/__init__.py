# Copyright (c) 2015 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
These are particular configurations of neuron model components. Each of them
is either supported or explicitly not supported.

*Others are possible* but might require an unknown amount of work to get
running on SpiNNaker.
"""

from .eif_cond_alpha_isfa_ista import EIFConductanceAlphaPopulation
from .hh_cond_exp import HHCondExp
from .if_cond_alpha import IFCondAlpha
from .if_cond_exp_base import IFCondExpBase
from .if_curr_alpha import IFCurrAlpha
from .if_curr_dual_exp_base import IFCurrDualExpBase
from .if_curr_exp_base import IFCurrExpBase
from .if_facets_hardware1 import IFFacetsConductancePopulation
from .izk_cond_exp_base import IzkCondExpBase
from .izk_cond_dual_exp_base import IzkCondDualExpBase
from .izk_curr_exp_base import IzkCurrExpBase
from .if_cond_exp_stoc import IFCondExpStoc
from .if_curr_delta import IFCurrDelta
from .if_curr_exp_ca2_adaptive import IFCurrExpCa2Adaptive
from .if_curr_exp_semd_base import IFCurrExpSEMDBase
from .if_curr_delta_ca2_adaptive import IFCurrDeltaCa2Adaptive
from .stoc_exp import StocExp
from .stoc_sigma import StocSigma
from .if_trunc_delta import IFTruncDelta

__all__ = ["EIFConductanceAlphaPopulation", "HHCondExp", "IFCondAlpha",
           "IFCondExpBase", "IFCurrAlpha", "IFCurrDualExpBase",
           "IFCurrExpBase", "IFFacetsConductancePopulation", "IzkCondExpBase",
           "IzkCurrExpBase", "IFCondExpStoc", "IzkCondDualExpBase",
           "IFCurrDelta", "IFCurrExpCa2Adaptive", "IFCurrExpSEMDBase",
           "IFCurrDeltaCa2Adaptive", "StocExp", "StocSigma", "IFTruncDelta"]
