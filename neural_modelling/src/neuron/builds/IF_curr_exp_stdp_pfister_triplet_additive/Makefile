APP = $(notdir $(CURDIR))
BUILD_DIR = build/


MODEL_PATH = $(SOURCE_DIRS)/neuron/models/neuron_model_lif_curr_impl
SYNAPSE_TYPE_PATH = $(SOURCE_DIRS)/neuron/synapse_types/synapse_types_exponential_impl
SYNAPSE_DYNAMICS_PATH =  $(SOURCE_DIRS)/neuron/synapse_dynamics/stdp/synapse_dynamics_stdp_impl

USES_STDP = TRUE
STDP_TIMING_PATH = $(SOURCE_DIRS)/neuron/synapse_dynamics/stdp/timing_dependence/timing_pfister_triplet_impl
STDP_WEIGHT_PATH = $(SOURCE_DIRS)/neuron/synapse_dynamics/stdp/weight_dependence/weight_additive_two_term_impl
PLASTIC_STRUCTURE_PATH = $(SOURCE_DIRS)/neuron/synapse_dynamics/stdp/synapse_structure/synapse_structure_weight_impl

include ../Makefile.common
