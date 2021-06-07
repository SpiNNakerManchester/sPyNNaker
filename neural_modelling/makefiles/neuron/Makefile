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

MODELS = IF_curr_exp \
         IF_cond_exp \
         IZK_curr_exp \
         IZK_cond_exp \
         IF_curr_exp_dual \
         IF_curr_exp_stdp_mad_pair_additive \
         IF_curr_exp_stdp_mad_pair_multiplicative \
         IF_cond_exp_stdp_mad_pair_additive \
         external_device_lif_control \
         IF_cond_exp_stoc \
         IF_curr_exp_stdp_mad_recurrent_pre_stochastic_multiplicative \
         IF_curr_exp_stdp_mad_recurrent_dual_fsm_multiplicative \
         IF_curr_exp_stdp_mad_vogels_2011_additive \
         IF_curr_delta \
         IF_curr_exp_ca2_adaptive \
         IF_curr_exp_ca2_adaptive_stdp_mad_pair_additive \
         IF_curr_exp_stdp_mad_nearest_pair_additive \
         IF_curr_exp_stdp_mad_nearest_pair_multiplicative \
         IF_curr_exp_stdp_mad_pfister_triplet_additive \
         IF_cond_exp_stdp_mad_nearest_pair_additive \
	     IF_curr_alpha \
	     IF_curr_alpha_stdp_mad_pair_additive \
         IF_cond_exp_structural_last_neuron_distance_weight \
         IF_curr_exp_structural_last_neuron_distance_weight \
         IF_curr_exp_structural_random_distance_weight \
         IF_curr_exp_sEMD \
         IZK_curr_exp_stdp_mad_pair_additive \
         IZK_cond_exp_stdp_mad_pair_additive \
#         IF_curr_exp_stdp_mad_pair_additive_structural_last_neuron_distance_weight \
#         IF_curr_exp_stdp_mad_pair_additive_structural_random_distance_weight \
#         IF_cond_exp_stdp_mad_nearest_pair_additive_structural_last_neuron_distance_weight \
#         IF_cond_exp_stdp_mad_pair_additive_structural_last_neuron_distance_weight \
#         IF_cond_exp_stdp_mad_pair_additive_structural_random_distance_weight

all:
	for d in $(MODELS); do $(MAKE) -C $$d || exit $$?; done

clean:
	for d in $(MODELS); do $(MAKE) -C $$d clean || exit $$?; done
