APP = $(notdir $(CURDIR))

NEURON_MODEL = $(NEURON_DIR)/neuron/models/neuron_model_lif_impl.c
NEURON_MODEL_H = $(NEURON_DIR)/neuron/models/neuron_model_lif_impl.h
INPUT_TYPE_H = $(NEURON_DIR)/neuron/input_types/input_type_conductance_2E2I.h
NEURON_IMPL_H = $(NEURON_DIR)/neuron/implementations/neuron_impl_standard.h
THRESHOLD_TYPE_H = $(NEURON_DIR)/neuron/threshold_types/threshold_type_static.h
SYNAPSE_TYPE_H = $(NEURON_DIR)/neuron/synapse_types/synapse_types_combined_exponential_2E2I_impl.h
SYNAPSE_DYNAMICS = $(NEURON_DIR)/neuron/plasticity/stdp/synapse_dynamics_stdp_mad_impl_recurrent.c
TIMING_DEPENDENCE = $(NEURON_DIR)/neuron/plasticity/stdp/timing_dependence/timing_recurrent_cyclic_impl.c
TIMING_DEPENDENCE_H = $(NEURON_DIR)/neuron/plasticity/stdp/timing_dependence/timing_recurrent_cyclic_impl.h
WEIGHT_DEPENDENCE = $(NEURON_DIR)/neuron/plasticity/stdp/weight_dependence/weight_multiplicative_impl.c
WEIGHT_DEPENDENCE_H = $(NEURON_DIR)/neuron/plasticity/stdp/weight_dependence/weight_multiplicative_impl.h

include ../neural_build.mk
