APP = $(notdir $(CURDIR))
BUILD_DIR = build/
SOURCE_DIR = $(NEURAL_MODELLING_DIRS)/src
MODEL_OBJS = $(SOURCE_DIR)/neuron/models/neuron_model_lif_curr_impl.o \
             $(SOURCE_DIR)/neuron/plasticity/common/post_events.o \
             $(SOURCE_DIR)/neuron/plasticity/stdp/synapse_dynamics_stdp_impl.o \
             $(SOURCE_DIR)/neuron/plasticity/common/maths.o \
             $(SOURCE_DIR)/neuron/plasticity/stdp/timing_dependence/timing_pair_impl.o \
             $(SOURCE_DIR)/neuron/plasticity/stdp/weight_dependence/weight_additive_one_term_impl.o
NEURON_MODEL_H = ../../models/neuron_model_lif_curr_impl.h
SYNAPSE_TYPE_H = ../../synapse_types/synapse_types_exponential_impl.h
TIMING_DEPENDENCE_H = ../../plasticity/stdp/timing_dependence/timing_pair_impl.h
WEIGHT_DEPENDENCE_H = ../../plasticity/stdp/weight_dependence/weight_additive_one_term_impl.h
APPLICATION_MAGIC_NUMBER = 0xAC1

include ../Makefile.common
