# See Notes in sPyNNaker/neural_modelling/CHANGES_April_2018

# Copyright (c) 2014-2023 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# If SPINN_DIRS is not defined, this is an error!
ifndef SPINN_DIRS
    $(error SPINN_DIRS is not set.  Please define SPINN_DIRS (possibly by running "source setup" in the spinnaker package folder))
endif

# If NEURAL_MODELLING_DIRS is not defined, this is an error!
ifndef NEURAL_MODELLING_DIRS
    $(error NEURAL_MODELLING_DIRS is not set.  Please define NEURAL_MODELLING_DIRS (possibly by running "source setup" in the sPyNNaker folder))
endif
#Check NEURAL_MODELLING_DIRS
MAKEFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
CHECK_PATH := $(NEURAL_MODELLING_DIRS)/makefiles/synapse_only/synapse_build.mk
ifneq ($(CHECK_PATH), $(MAKEFILE_PATH))
    $(error Please check NEURAL_MODELLING_DIRS as based on that this file is at $(CHECK_PATH) when it is actually at $(MAKEFILE_PATH))
endif

# Set logging levels
ifeq ($(SPYNNAKER_DEBUG), DEBUG)
    SYNAPSE_DEBUG = LOG_DEBUG
    PLASTIC_DEBUG = LOG_DEBUG
endif

ifndef SYNAPSE_DEBUG
    SYNAPSE_DEBUG = LOG_INFO
endif

ifndef PLASTIC_DEBUG
    PLASTIC_DEBUG = LOG_INFO
endif

#POPULATION_TABLE_IMPL := fixed
POPULATION_TABLE_IMPL := binary_search

# Add source directory

# Define the directories
# Path flag to replace with the modified dir  (abspath drops the final /)
NEURON_DIR := $(abspath $(NEURAL_MODELLING_DIRS)/src)
MODIFIED_DIR :=$(dir $(abspath $(NEURON_DIR)))modified_src/
SOURCE_DIRS += $(NEURON_DIR)

# Define a rule to find the source directory of the given file.
# This attempts to find each of SOURCE_DIRS within the given file name; the
# first one that matches is then returned.  If none match, an empty string
# will be returned.
define get_source_dir#(file)
$(firstword $(strip $(foreach d, $(sort $(SOURCE_DIRS)), $(findstring $(d), $(1)))))
endef

# Define rule to strip any SOURCE_DIRS from source_file to allow use via local.mk.
# If no match is found, the value is returned untouched 
# (though this will probably fail later).
define strip_source_dirs#(source_file)
$(or $(patsubst $(call get_source_dir, $(1))/%,%,$(1)), $(1))
endef

# Define a rule to replace any SOURCE_DIRS from header_file with the modified_src folder.
define replace_source_dirs#(header_file)
$(patsubst $(call get_source_dir, $(1))%, $(dir $(call get_source_dir, $(1)))modified_src%, $(1))
endef

# Need to build each neuron seperately or complier gets confused
# BUILD_DIR and APP_OUTPUT_DIR end with a / for historictical/ shared reasons
ifndef BUILD_DIR
    BUILD_DIR := $(NEURAL_MODELLING_DIRS)/builds/$(APP)/
endif
ifndef APP_OUTPUT_DIR
    APP_OUTPUT_DIR :=  $(NEURAL_MODELLING_DIRS)/../spynnaker/pyNN/model_binaries
endif

ifndef SYNAPSE_DYNAMICS
    $(error SYNAPSE_DYNAMICS is not set.  Please select a synapse dynamics implementation)
else
    SYNAPSE_DYNAMICS_C := $(call replace_source_dirs,$(SYNAPSE_DYNAMICS))
    SYNAPSE_DYNAMICS := $(call strip_source_dirs,$(SYNAPSE_DYNAMICS))
    SYNAPSE_DYNAMICS_O := $(BUILD_DIR)$(SYNAPSE_DYNAMICS:%.c=%.o)
    
    SYNAPSE_DYNAMICS_STATIC := neuron/plasticity/synapse_dynamics_static_impl.c
    STDP_ENABLED = 0
    ifneq ($(SYNAPSE_DYNAMICS), $(SYNAPSE_DYNAMICS_STATIC))
        STDP_ENABLED = 1

        ifndef TIMING_DEPENDENCE_H
            $(error TIMING_DEPENDENCE_H is not set which is required when SYNAPSE_DYNAMICS ($(SYNAPSE_DYNAMICS_C)) != $(SYNAPSE_DYNAMICS_STATIC))
        endif
        ifndef WEIGHT_DEPENDENCE_H
            $(error WEIGHT_DEPENDENCE_H is not set which is required when SYNAPSE_DYNAMICS ($(SYNAPSE_DYNAMICS_C)) != $(SYNAPSE_DYNAMICS_STATIC))
        endif
    endif
endif

ifdef WEIGHT_DEPENDENCE
    WEIGHT_DEPENDENCE_H := $(call replace_source_dirs,$(WEIGHT_DEPENDENCE_H))
    WEIGHT_DEPENDENCE_C := $(call replace_source_dirs,$(WEIGHT_DEPENDENCE))
    WEIGHT_DEPENDENCE := $(call strip_source_dirs,$(WEIGHT_DEPENDENCE))
    WEIGHT_DEPENDENCE_O := $(BUILD_DIR)$(WEIGHT_DEPENDENCE:%.c=%.o)
endif

ifdef TIMING_DEPENDENCE
    TIMING_DEPENDENCE_H := $(call replace_source_dirs,$(TIMING_DEPENDENCE_H))
    TIMING_DEPENDENCE_C := $(call replace_source_dirs,$(TIMING_DEPENDENCE))
    TIMING_DEPENDENCE := $(call strip_source_dirs,$(TIMING_DEPENDENCE))
    TIMING_DEPENDENCE_O := $(BUILD_DIR)$(TIMING_DEPENDENCE:%.c=%.o)
endif

SYNGEN_ENABLED = 1
ifndef SYNAPTOGENESIS_DYNAMICS
    SYNAPTOGENESIS_DYNAMICS := neuron/structural_plasticity/synaptogenesis_dynamics_static_impl.c
    SYNAPTOGENESIS_DYNAMICS_C := $(MODIFIED_DIR)$(SYNAPTOGENESIS_DYNAMICS)
    SYNGEN_ENABLED = 0
else
    SYNAPTOGENESIS_DYNAMICS_C := $(call replace_source_dirs,$(SYNAPTOGENESIS_DYNAMICS))
    SYNAPTOGENESIS_DYNAMICS := $(call strip_source_dirs,$(SYNAPTOGENESIS_DYNAMICS))
    ifndef PARTNER_SELECTION
        $(error PARTNER_SELECTION is not set which is required when SYNAPTOGENESIS_DYNAMICS is set)
    endif
    ifndef FORMATION
        $(error FORMATION is not set which is required when SYNAPTOGENESIS_DYNAMICS is set)
    endif
    ifndef ELIMINATION
        $(error ELIMINATION is not set which is required when SYNAPTOGENESIS_DYNAMICS is set)
    endif
endif
SYNAPTOGENESIS_DYNAMICS_O := $(BUILD_DIR)$(SYNAPTOGENESIS_DYNAMICS:%.c=%.o)

ifdef PARTNER_SELECTION
    PARTNER_SELECTION_H := $(call replace_source_dirs,$(PARTNER_SELECTION_H))
    PARTNER_SELECTION_C := $(call replace_source_dirs,$(PARTNER_SELECTION))
    PARTNER_SELECTION := $(call strip_source_dirs,$(PARTNER_SELECTION))
    PARTNER_SELECTION_O := $(BUILD_DIR)$(PARTNER_SELECTION:%.c=%.o)
endif

ifdef FORMATION
    FORMATION_H := $(call replace_source_dirs,$(FORMATION_H))
    FORMATION_C := $(call replace_source_dirs,$(FORMATION))
    FORMATION := $(call strip_source_dirs,$(FORMATION))
    FORMATION_O := $(BUILD_DIR)$(FORMATION:%.c=%.o)
endif

ifdef ELIMINATION
    ELIMINATION_H := $(call replace_source_dirs,$(ELIMINATION_H))
    ELIMINATION_C := $(call replace_source_dirs,$(ELIMINATION))
    ELIMINATION := $(call strip_source_dirs,$(ELIMINATION))
    ELIMINATION_O := $(BUILD_DIR)$(ELIMINATION:%.c=%.o)
endif

OTHER_SOURCES_CONVERTED := $(call strip_source_dirs,$(OTHER_SOURCES))

# List all the sources relative to one of SOURCE_DIRS
SOURCES = neuron/c_main_synapses.c \
          neuron/synapses.c \
          neuron/spike_processing_fast.c \
          neuron/population_table/population_table_$(POPULATION_TABLE_IMPL)_impl.c \
          $(SYNAPSE_DYNAMICS) $(WEIGHT_DEPENDENCE) \
          $(TIMING_DEPENDENCE) $(SYNAPTOGENESIS_DYNAMICS) \
          $(PARTNER_SELECTION) $(FORMATION) $(ELIMINATION) $(OTHER_SOURCES_CONVERTED)

include $(SPINN_DIRS)/make/local.mk

FEC_OPT = $(OTIME)

# Extra compile options
DO_COMPILE = $(CC) -DLOG_LEVEL=$(SYNAPSE_DEBUG) $(CFLAGS) -DSTDP_ENABLED=$(STDP_ENABLED)

$(BUILD_DIR)neuron/synapses.o: $(MODIFIED_DIR)neuron/synapses.c
	#synapses.c
	-@mkdir -p $(dir $@)
	$(DO_COMPILE) -o $@ $<

$(BUILD_DIR)neuron/direct_synapses.o: $(MODIFIED_DIR)neuron/direct_synapses.c
	#direct_synapses.c
	-mkdir -p $(dir $@)
	$(DO_COMPILE) -o $@ $<

$(BUILD_DIR)neuron/spike_processing_fast.o: $(MODIFIED_DIR)neuron/spike_processing_fast.c
	#spike_processing_fast.c
	-@mkdir -p $(dir $@)
	$(DO_COMPILE) -o $@ $<

$(BUILD_DIR)neuron/population_table/population_table_binary_search_impl.o: $(MODIFIED_DIR)neuron/population_table/population_table_binary_search_impl.c
	#population_table/population_table_binary_search_impl.c
	-@mkdir -p $(dir $@)
	$(DO_COMPILE) -o $@ $<

SYNGEN_INCLUDES:=
ifeq ($(SYNGEN_ENABLED), 1)
    SYNGEN_INCLUDES:= -include $(PARTNER_SELECTION_H) -include $(FORMATION_H) -include $(ELIMINATION_H)
endif

#STDP Build rules If and only if STDP used
ifeq ($(STDP_ENABLED), 1)
    STDP_INCLUDES:= -include $(WEIGHT_DEPENDENCE_H) -include $(TIMING_DEPENDENCE_H)
    STDP_COMPILE = $(CC) -DLOG_LEVEL=$(PLASTIC_DEBUG) $(CFLAGS) -DSTDP_ENABLED=$(STDP_ENABLED) -DSYNGEN_ENABLED=$(SYNGEN_ENABLED) $(STDP_INCLUDES)

    $(SYNAPSE_DYNAMICS_O): $(SYNAPSE_DYNAMICS_C)
	# SYNAPSE_DYNAMICS_O stdp
	-@mkdir -p $(dir $@)
	$(STDP_COMPILE) -o $@ $<

    $(SYNAPTOGENESIS_DYNAMICS_O): $(SYNAPTOGENESIS_DYNAMICS_C)
	# SYNAPTOGENESIS_DYNAMICS_O stdp
	-@mkdir -p $(dir $@)
	$(STDP_COMPILE) $(SYNGEN_INCLUDES) -o $@ $<

    $(BUILD_DIR)neuron/plasticity/common/post_events.o: $(MODIFIED_DIR)neuron/plasticity/common/post_events.c
	# plasticity/common/post_events.c
	-@mkdir -p $(dir $@)
	$(STDP_COMPILE) -o $@ $<

else
    $(SYNAPTOGENESIS_DYNAMICS_O): $(SYNAPTOGENESIS_DYNAMICS_C)
    # SYNAPTOGENESIS_DYNAMICS_O without stdp
	-@mkdir -p $(dir $@)
	$(DO_COMPILE) $(SYNGEN_INCLUDES) -o $@ $<

    $(SYNAPSE_DYNAMICS_O): $(SYNAPSE_DYNAMICS_C)
    # SYNAPSE_DYNAMICS_O without stdp
	-@mkdir -p $(dir $@)
	$(DO_COMPILE) -o $@ $<

endif

$(WEIGHT_DEPENDENCE_O): $(WEIGHT_DEPENDENCE_C)
	# WEIGHT_DEPENDENCE_O
	-@mkdir -p $(dir $@)
	$(CC) -DLOG_LEVEL=$(PLASTIC_DEBUG) $(CFLAGS) -o $@ $<

$(TIMING_DEPENDENCE_O): $(TIMING_DEPENDENCE_C) $(WEIGHT_DEPENDENCE_H)
	# TIMING_DEPENDENCE_O
	-@mkdir -p $(dir $@)
	$(CC) -DLOG_LEVEL=$(PLASTIC_DEBUG) $(CFLAGS) \
	        -include $(WEIGHT_DEPENDENCE_H) -o $@ $<

$(PARTNER_SELECTION_O): $(PARTNER_SELECTION_C)
	# PARTNER_SELECTION_O
	-mkdir -p $(dir $@)
	$(CC) -DLOG_LEVEL=$(PLASTIC_DEBUG) $(CFLAGS) -o $@ $<

$(FORMATION_O): $(FORMATION_C)
	# FORMATION_O
	-mkdir -p $(dir $@)
	$(CC) -DLOG_LEVEL=$(PLASTIC_DEBUG) $(CFLAGS) -o $@ $<

$(ELIMINATION_O): $(ELIMINATION_C)
	# ELIMINATION_O
	-mkdir -p $(dir $@)
	$(CC) -DLOG_LEVEL=$(PLASTIC_DEBUG) $(CFLAGS) -o $@ $<

.PRECIOUS: $(MODIFIED_DIR)%.c $(MODIFIED_DIR)%.h $(LOG_DICT_FILE) $(EXTRA_PRECIOUS)
