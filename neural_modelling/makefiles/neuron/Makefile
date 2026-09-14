# Copyright (c) 2014 The University of Manchester
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

MODELS = IF_curr_exp \
         IF_cond_exp \
         IZK_curr_exp \
         IZK_cond_exp \
         IF_curr_exp_dual \
         IZK_cond_exp_dual \
         IF_curr_delta \
         IF_curr_exp_ca2_adaptive \
         IF_curr_delta_ca2_adaptive \
         stoc_exp \
         stoc_exp_stable \
         stoc_sigma \
         IF_curr_delta_fixed_prob \
         IF_trunc_delta \
         IF_curr_alpha \
         IF_cond_exp_stoc

ifneq ($(SPYNNAKER_DEBUG), DEBUG)
    MODELS += external_device_lif_control \
              IF_curr_exp_stdp_mad_pair_additive \
              IF_curr_exp_stdp_mad_pair_multiplicative \
              IF_cond_exp_stdp_mad_pair_additive \
              IF_curr_exp_stdp_mad_recurrent_dual_fsm_multiplicative \
              IF_curr_exp_stdp_mad_vogels_2011_additive \
              IF_curr_exp_ca2_adaptive_stdp_mad_pair_additive \
              IF_curr_exp_stdp_mad_nearest_pair_additive \
              IF_curr_exp_stdp_mad_nearest_pair_multiplicative \
              IF_cond_exp_stdp_mad_nearest_pair_additive \
              IZK_curr_exp_stdp_mad_pair_additive \
              IZK_cond_exp_stdp_mad_pair_additive \
              IZK_cond_exp_dual_stdp_mad_pair_additive \
              IF_curr_alpha_stdp_mad_pair_additive \
              IF_curr_delta_stdp_mad_pair_additive \
              IF_curr_delta_stdp_mad_nearest_pair_additive \
              IF_curr_exp_stdp_mad_recurrent_pre_stochastic_multiplicative \
              IF_curr_exp_stdp_mad_pfister_triplet_additive \
              IF_curr_exp_weight_change \
              IF_curr_exp_sEMD
endif

all:
	for d in $(MODELS); do $(MAKE) -C $$d || exit $$?; done

clean:
	for d in $(MODELS); do $(MAKE) -C $$d clean || exit $$?; done
