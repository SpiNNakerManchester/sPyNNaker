APP = $(notdir $(CURDIR))

NEURON_MODEL = $(NEURON_DIR)/synapse/models/neuron_model_lif_impl.c
NEURON_MODEL_H = $(NEURON_DIR)/synapse/models/neuron_model_lif_impl.h
INPUT_TYPE_H = $(NEURON_DIR)/synapse/input_types/input_type_conductance.h
NEURON_IMPL_H = $(NEURON_DIR)/synapse/implementations/neuron_impl_standard.h
THRESHOLD_TYPE_H = $(NEURON_DIR)/synapse/threshold_types/threshold_type_maass_stochastic.h
SYNAPSE_TYPE_H = $(NEURON_DIR)/synapse/synapse_types/synapse_types_exponential_impl.h
SYNAPSE_DYNAMICS = $(NEURON_DIR)/synapse/plasticity/synapse_dynamics_static_impl.c

include ../neural_build.mk
