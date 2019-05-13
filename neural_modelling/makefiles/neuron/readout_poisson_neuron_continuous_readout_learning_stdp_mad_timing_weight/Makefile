APP = $(notdir $(CURDIR))

OTHER_SOURCES = $(NEURON_DIR)/neuron/models/neuron_model_lif_poisson_readout_impl.c
NEURON_IMPL_H = $(NEURON_DIR)/neuron/implementations/neuron_impl_poisson_readout_non_spike_learning.h
SYNAPSE_DYNAMICS = $(NEURON_DIR)/neuron/plasticity/stdp/synapse_dynamics_stdp_mad_erbp_readout_impl.c

TIMING_DEPENDENCE = $(NEURON_DIR)/neuron/plasticity/stdp/timing_dependence/timing_erbp_impl.c
TIMING_DEPENDENCE_H = $(NEURON_DIR)/neuron/plasticity/stdp/timing_dependence/timing_erbp_impl.h
WEIGHT_DEPENDENCE = $(NEURON_DIR)/neuron/plasticity/stdp/weight_dependence/weight_erbp_impl.c
WEIGHT_DEPENDENCE_H = $(NEURON_DIR)/neuron/plasticity/stdp/weight_dependence/weight_erbp_impl.h


include ../neural_build.mk
