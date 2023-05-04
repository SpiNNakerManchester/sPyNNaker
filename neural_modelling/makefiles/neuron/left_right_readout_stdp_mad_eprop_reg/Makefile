APP = $(notdir $(CURDIR))

#OTHER_SOURCES = $(NEURON_DIR)/neuron/models/neuron_model_left_right_readout_impl.c
NEURON_IMPL_H = $(NEURON_DIR)/neuron/implementations/neuron_impl_left_right_readout.h

#SYNAPSE_DYNAMICS = $(NEURON_DIR)/neuron/plasticity/synapse_dynamics_static_impl.c
SYNAPSE_DYNAMICS = $(NEURON_DIR)/neuron/plasticity/stdp/synapse_dynamics_left_right_readout_impl.c
#SYNAPSE_DYNAMICS = $(NEURON_DIR)/neuron/plasticity/stdp/synapse_dynamics_eprop_adaptive_impl.c

TIMING_DEPENDENCE = $(NEURON_DIR)/neuron/plasticity/stdp/timing_dependence/timing_eprop_impl.c
TIMING_DEPENDENCE_H = $(NEURON_DIR)/neuron/plasticity/stdp/timing_dependence/timing_eprop_impl.h
WEIGHT_DEPENDENCE = $(NEURON_DIR)/neuron/plasticity/stdp/weight_dependence/weight_eprop_reg_impl.c
WEIGHT_DEPENDENCE_H = $(NEURON_DIR)/neuron/plasticity/stdp/weight_dependence/weight_eprop_reg_impl.h

include ../neural_build.mk


