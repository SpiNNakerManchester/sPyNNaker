APP = $(notdir $(CURDIR))

NEURON_MODEL = neuron/models/neuron_model_lif_impl.c
NEURON_MODEL_H = neuron/models/neuron_model_lif_impl.h
INPUT_TYPE_H = neuron/input_types/input_type_conductance.h
THRESHOLD_TYPE_H = neuron/threshold_types/threshold_type_maass_stochastic.h
SYNAPSE_TYPE_H = neuron/synapse_types/synapse_types_exponential_impl.h
SYNAPSE_DYNAMICS = neuron/plasticity/synapse_dynamics_static_impl.c

include ../neural_build.mk
