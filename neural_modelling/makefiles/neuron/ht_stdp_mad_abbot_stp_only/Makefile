APP = $(notdir $(CURDIR))

NEURON_MODEL = $(NEURON_DIR)/neuron/models/neuron_model_ht_impl.c
NEURON_MODEL_H = $(NEURON_DIR)/neuron/models/neuron_model_ht_impl.h
INPUT_TYPE_H = $(NEURON_DIR)/neuron/input_types/input_type_ht_conductance.h
NEURON_IMPL_H = $(NEURON_DIR)/neuron/implementations/neuron_impl_standard.h
THRESHOLD_TYPE_H = $(NEURON_DIR)/neuron/threshold_types/threshold_type_ht_dynamic.h
SYNAPSE_TYPE_H = $(NEURON_DIR)/neuron/synapse_types/synapse_types_ht_impl.h
ADDITIONAL_INPUT_H = $(NEURON_DIR)/neuron/additional_inputs/additional_input_ht_currents_impl.h

SYNAPSE_DYNAMICS = $(NEURON_DIR)/neuron/plasticity/stdp/synapse_dynamics_stdp_mad_impl.c
TIMING_DEPENDENCE = $(NEURON_DIR)/neuron/plasticity/stdp/timing_dependence/timing_abbot_impl.c
TIMING_DEPENDENCE_H = $(NEURON_DIR)/neuron/plasticity/stdp/timing_dependence/timing_abbot_impl.h
WEIGHT_DEPENDENCE = $(NEURON_DIR)/neuron/plasticity/stdp/weight_dependence/weight_stp_only_impl.c
WEIGHT_DEPENDENCE_H = $(NEURON_DIR)/neuron/plasticity/stdp/weight_dependence/weight_stp_only_impl.h

include ../neural_build.mk
