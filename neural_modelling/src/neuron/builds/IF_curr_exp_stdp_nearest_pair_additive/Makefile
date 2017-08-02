APP = $(notdir $(CURDIR))
BUILD_DIR = build/

NEURON_MODEL = $(SOURCE_DIR)/neuron/models/neuron_model_lif_impl.c
NEURON_MODEL_H = $(SOURCE_DIR)/neuron/models/neuron_model_lif_impl.h
INPUT_TYPE_H = $(SOURCE_DIR)/neuron/input_types/input_type_current.h
THRESHOLD_TYPE_H = $(SOURCE_DIR)/neuron/threshold_types/threshold_type_static.h
SYNAPSE_TYPE_H = $(SOURCE_DIR)/neuron/synapse_types/synapse_types_exponential_impl.h
SYNAPSE_DYNAMICS = $(SOURCE_DIR)/neuron/plasticity/stdp/synapse_dynamics_stdp_impl.c
TIMING_DEPENDENCE = $(SOURCE_DIR)/neuron/plasticity/stdp/timing_dependence/timing_nearest_pair_impl.c
TIMING_DEPENDENCE_H = $(SOURCE_DIR)/neuron/plasticity/stdp/timing_dependence/timing_nearest_pair_impl.h
WEIGHT_DEPENDENCE = $(SOURCE_DIR)/neuron/plasticity/stdp/weight_dependence/weight_additive_one_term_impl.c
WEIGHT_DEPENDENCE_H = $(SOURCE_DIR)/neuron/plasticity/stdp/weight_dependence/weight_additive_one_term_impl.h

include ../common.mk
