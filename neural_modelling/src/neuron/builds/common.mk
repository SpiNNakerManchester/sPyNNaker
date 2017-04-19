# ==================== GENERAL VARIABLES YOU MAY SET ====================
#
# EXTRA_SOURCE_DIRS - Colon-separated list of extra directories to search for
#                     source code. Can be the root of a directory tree provided
#                     all the sources are referred to using paths that are
#                     relative to that root.
#
# OTHER_SOURCES - Space-separated list of other source files that need to be
#                 built to make the particular overall neuron/synapse model
#                 implementation.
#
# APP - The name of the application instance, which usually corresponds to the
#       name of the model in PyNN, e.g., IF_cond_exp.
#
# ================== NEURON MODEL VARIABLES YOU MAY SET ==================
#
# NEURON_MODEL - Name of file containing the implementation of the neuron model
#                implementation. Assumed to end with .c.
#
# NEURON_MODEL_H - Name of file containing the headers of the neuron model
#                  implementation. Assumed to end with .h.
#
# INPUT_TYPE_H - Name of file containing the headers of the input type
#                implementation. Assumed to end with .h. Standard supplied ones
#                are input_type_conductance.h and input_type_current.h, in the
#                neuron/input_types directory.
#
# SYNAPSE_TYPE_H - Name of file containing the headers of the synapse type
#                  implementation. Assumed to end with .h. Standard supplied
#                  ones are synapse_types_dual_excitatory_exponential_impl.h
#                  and synapse_types_exponential_impl.h, in the
#                  neuron/synapse_types directory.
#
# SYNAPSE_DYNAMICS - Name of implementation of the synapse dynamics. Assumed to
#                    end with .c. The following files are provided for use:
#                        neuron/plasticity/synapse_dynamics_static_impl.c
#                        neuron/plasticity/stdp/synapse_dynamics_stdp_impl.c
#                        neuron/plasticity/stdp/synapse_dynamics_stdp_mad_impl.c
#
# THRESHOLD_TYPE_H - Name of file containing the headers of the thresholding
#                    algorithm implementation. Assumed to end with .h. Only one
#                    standard one is available;
#                    neuron/threshold_types/threshold_type_static.h
#
# TIMING_DEPENDENCE_H - Name of file containing the headers of the STDP timing
#                       dependence rule implementation. Assumed to end with .h.
#
# TIMING_DEPENDENCE - Name of implementation of the STDP timing dependence rule.
#                     Assumed to end with .c. SHOULD be omitted if
#                     SYNAPSE_DYNAMICS is set to a non-STDP rule (e.g., static).
#
# WEIGHT_DEPENDENCE_H - Name of file containing the headers of the STDP weight
#                       dependence rule implementation. Assumed to end with .h.
#
# WEIGHT_DEPENDENCE - Name of implementation of the STDP weight dependence rule.
#                     Assumed to end with .c. SHOULD be omitted if
#                     SYNAPSE_DYNAMICS is set to a non-STDP rule (e.g., static).
#

$(info ---------------------------------------------------------------------)
$(info Build configuration: $(CURDIR)/Makefile)
$(info )

ifndef NEURAL_MODELLING_DIRS
    NEURAL_MODELLING_DIRS := $(abspath $(dir $(abspath $(lastword $(MAKEFILE_LIST))))/../../..)
endif

include $(NEURAL_MODELLING_DIRS)/src/paths.mk
include $(NEURAL_MODELLING_DIRS)/src/neuron/builds/neural_build.mk
include $(NEURAL_MODELLING_DIRS)/src/neuron/builds/classes.mk
