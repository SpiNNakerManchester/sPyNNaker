APP = $(notdir $(CURDIR))
BUILD_DIR = build/

NEURON_MODEL = $(SOURCE_DIR)/neuron/models/neuron_model_HT_impl.c
NEURON_MODEL_H = $(SOURCE_DIR)/neuron/models/neuron_model_HT_impl.h
INPUT_TYPE_H = $(SOURCE_DIR)/neuron/input_types/input_type_HT_conductance.h
THRESHOLD_TYPE_H = $(SOURCE_DIR)/neuron/threshold_types/threshold_type_ht_dynamic.h
SYNAPSE_TYPE_H = $(SOURCE_DIR)/neuron/synapse_types/synapse_types_ht_impl.h
ADDITIONAL_INPUT_H = $(SOURCE_DIR)/neuron/additional_inputs/additional_input_HT_currents_impl.h

SYNAPSE_DYNAMICS = $(SOURCE_DIR)/neuron/plasticity/stdp/synapse_dynamics_stdp_mad_impl.c
TIMING_DEPENDENCE = $(SOURCE_DIR)/neuron/plasticity/stdp/timing_dependence/timing_abbot_impl.c
TIMING_DEPENDENCE_H = $(SOURCE_DIR)/neuron/plasticity/stdp/timing_dependence/timing_abbot_impl.h
WEIGHT_DEPENDENCE = $(SOURCE_DIR)/neuron/plasticity/stdp/weight_dependence/weight_stp_only_impl.c
WEIGHT_DEPENDENCE_H = $(SOURCE_DIR)/neuron/plasticity/stdp/weight_dependence/weight_stp_only_impl.h

include ../common.mk
