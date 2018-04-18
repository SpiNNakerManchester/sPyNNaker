APP = $(notdir $(CURDIR))

NEURON_MODEL = models/neuron_model_lif_impl.c
NEURON_MODEL_H = models/neuron_model_lif_impl.h
INPUT_TYPE_H = input_types/input_type_current.h
THRESHOLD_TYPE_H = threshold_types/threshold_type_static.h
SYNAPSE_TYPE_H = synapse_types/synapse_types_exponential_impl.h
SYNAPSE_DYNAMICS = plasticity/stdp/synapse_dynamics_stdp_mad_impl.c
TIMING_DEPENDENCE = plasticity/stdp/timing_dependence/timing_recurrent_dual_fsm_impl.c
TIMING_DEPENDENCE_H = plasticity/stdp/timing_dependence/timing_recurrent_dual_fsm_impl.h
WEIGHT_DEPENDENCE = plasticity/stdp/weight_dependence/weight_multiplicative_impl.c
WEIGHT_DEPENDENCE_H = plasticity/stdp/weight_dependence/weight_multiplicative_impl.h

include ../neural_build.mk