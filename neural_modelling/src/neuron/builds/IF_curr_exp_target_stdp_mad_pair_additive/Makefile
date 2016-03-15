APP = $(notdir $(CURDIR))
BUILD_DIR = build/
MODEL_OBJS = $(SOURCE_DIRS)/neuron/models/neuron_model_lif_curr_impl.o \
             $(SOURCE_DIRS)/neuron/plasticity/common/post_events.o \
             $(SOURCE_DIRS)/neuron/plasticity/stdp/synapse_dynamics_stdp_target_impl.o \
             $(SOURCE_DIRS)/neuron/plasticity/common/maths.o \
             $(SOURCE_DIRS)/neuron/plasticity/stdp/timing_dependence/timing_target_pair_impl.o \
             $(SOURCE_DIRS)/neuron/plasticity/stdp/weight_dependence/weight_additive_one_term_impl.o
NEURON_MODEL_H = ../../models/neuron_model_lif_curr_impl.h
SYNAPSE_TYPE_H = ../../synapse_types/synapse_types_exponential_target_impl.h
TIMING_DEPENDENCE_H = ../../plasticity/stdp/timing_dependence/timing_target_pair_impl.h
WEIGHT_DEPENDENCE_H = ../../plasticity/stdp/weight_dependence/weight_additive_one_term_impl.h
PLASTIC_SYNAPSE_STRUCTURE_H = ../../plasticity/stdp/synapse_structure/synapse_structure_weight_target.h
APPLICATION_MAGIC_NUMBER = 0xAC1
CFLAGS += -DSYNAPSE_AXONAL_DELAY_BITS=1
include ../Makefile.common
