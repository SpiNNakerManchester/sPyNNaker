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

MODELS = IF_curr_exp_neuron\
         IZK_curr_exp_neuron\
         IF_cond_exp_neuron\
         IZK_cond_exp_neuron\
         IF_curr_exp_ca2_adaptive_neuron\
         IF_curr_exp_dual_neuron\
         IF_curr_exp_sEMD_neuron\
         IF_curr_delta_neuron\
         IF_curr_alpha_neuron\
         IF_cond_exp_stoc_neuron\
         external_device_lif_control_neuron

all:
	for d in $(MODELS); do $(MAKE) -C $$d || exit $$?; done

clean:
	for d in $(MODELS); do $(MAKE) -C $$d clean || exit $$?; done