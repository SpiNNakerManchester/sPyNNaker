APP = $(notdir $(CURDIR))
BUILD_DIR = build/

MODEL_PATH = $(SOURCE_DIRS)/neuron/models/neuron_model_lif_curr_impl
SYNAPSE_TYPE_PATH = ../../synapse_types/synapse_types_exponential_impl
SYNAPSE_DYNAMICS_PATH =  $(SOURCE_DIRS)/neuron/plasticity/stdp/synapse_dynamics_stdp_mad_impl

USES_STDP = TRUE
STDP_TIMING_PATH = $(SOURCE_DIRS)/neuron/plasticity/stdp/timing_dependence/timing_nearest_pair_impl
STDP_WEIGHT_PATH = $(SOURCE_DIRS)/neuron/plasticity/stdp/weight_dependence/weight_additive_one_term_impl
PLASTIC_STRUCTURE_PATH = ../../plasticity/stdp/synapse_structure/synapse_structure_weight_impl

include ../Makefile.common
