APP = $(notdir $(CURDIR))

NEURON_MODEL = models/neuron_model_lif_impl.c
NEURON_MODEL_H = models/neuron_model_lif_impl.h
INPUT_TYPE_H = input_types/input_type_current.h
THRESHOLD_TYPE_H = threshold_types/threshold_type_static.h
SYNAPSE_TYPE_H = synapse_types/synapse_types_dual_excitatory_exponential_impl.h
SYNAPSE_DYNAMICS = plasticity/synapse_dynamics_static_impl.c

include ../neural_build.mk
