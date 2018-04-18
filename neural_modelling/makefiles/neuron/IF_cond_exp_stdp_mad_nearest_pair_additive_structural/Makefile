APP = $(notdir $(CURDIR))

NEURON_MODEL = neuron/models/neuron_model_lif_impl.c
NEURON_MODEL_H = neuron/models/neuron_model_lif_impl.h
INPUT_TYPE_H = neuron/input_types/input_type_conductance.h
THRESHOLD_TYPE_H = neuron/threshold_types/threshold_type_static.h
SYNAPSE_TYPE_H = neuron/synapse_types/synapse_types_exponential_impl.h
SYNAPSE_DYNAMICS = neuron/plasticity/stdp/synapse_dynamics_stdp_mad_impl.c
TIMING_DEPENDENCE = neuron/plasticity/stdp/timing_dependence/timing_nearest_pair_impl.c
TIMING_DEPENDENCE_H = neuron/plasticity/stdp/timing_dependence/timing_nearest_pair_impl.h
WEIGHT_DEPENDENCE = neuron/plasticity/stdp/weight_dependence/weight_additive_one_term_impl.c
WEIGHT_DEPENDENCE_H = neuron/plasticity/stdp/weight_dependence/weight_additive_one_term_impl.h
SYNAPTOGENESIS_DYNAMICS = neuron/structural_plasticity/synaptogenesis/topographic_map_impl.c

include ../neural_build.mk
