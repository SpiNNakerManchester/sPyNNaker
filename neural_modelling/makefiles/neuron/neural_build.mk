# See Notes in sPyNNaker/neural_modelling/CHANGES_April_2018

# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
CHECK_PATH := $(NEURAL_MODELLING_DIRS)/makefiles/neuron/neural_build.mk
ifneq ($(CHECK_PATH), $(MAKEFILE_PATH))
    $(error Please check NEURAL_MODELLING_DIRS as based on that this file is at $(CHECK_PATH) when it is actually at $(MAKEFILE_PATH))
endif

# Set logging levels
ifeq ($(SPYNNAKER_DEBUG), DEBUG)
    NEURON_DEBUG = LOG_DEBUG
    SYNAPSE_DEBUG = LOG_DEBUG
    PLASTIC_DEBUG = LOG_DEBUG
endif

ifndef NEURON_DEBUG
    NEURON_DEBUG = LOG_INFO
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

# Check if the neuron implementation is the default one
ifndef NEURON_IMPL_H
    $(error NEURON_IMPL_H is not set.  Please select a neuron implementation)
else
    NEURON_IMPL := $(call strip_source_dirs,$(NEURON_IMPL_H))
    NEURON_IMPL_H := $(call replace_source_dirs,$(NEURON_IMPL_H))
    NEURON_IMPL_STANDARD := neuron/implementations/neuron_impl_standard.h
    NEURON_INCLUDES := -include $(NEURON_IMPL_H)
    ifeq ($(NEURON_IMPL), $(NEURON_IMPL_STANDARD))
        
        # Check required inputs and point them to modified sources
		ifndef ADDITIONAL_INPUT_H
		    ADDITIONAL_INPUT_H = $(MODIFIED_DIR)neuron/additional_inputs/additional_input_none_impl.h
		else
		    ADDITIONAL_INPUT_H := $(call replace_source_dirs,$(ADDITIONAL_INPUT_H))
		endif
		
		ifndef NEURON_MODEL_H
		    $(error NEURON_MODEL_H is not set.  Please select a neuron model header file)
		else
		    NEURON_MODEL_H := $(call replace_source_dirs,$(NEURON_MODEL_H))
		endif
		
		ifndef INPUT_TYPE_H
		    $(error INPUT_TYPE_H is not set.  Please select an input type header file)
		else
		    INPUT_TYPE_H := $(call replace_source_dirs,$(INPUT_TYPE_H))
		endif
		
		ifndef THRESHOLD_TYPE_H
		    $(error THRESHOLD_TYPE_H is not set.  Please select a threshold type header file)
		else
		    THRESHOLD_TYPE_H := $(call replace_source_dirs,$(THRESHOLD_TYPE_H))
		endif
		
		ifndef SYNAPSE_TYPE_H
		    $(error SYNAPSE_TYPE_H is not set.  Please select a synapse type header file)
		else
		    SYNAPSE_TYPE_H := $(call replace_source_dirs,$(SYNAPSE_TYPE_H))
		endif
		
		ifndef CURRENT_SOURCE_H
		    CURRENT_SOURCE_H = $(MODIFIED_DIR)neuron/current_sources/current_source_impl.h
		else
		    CURRENT_SOURCE_H := $(call replace_source_dirs,$(CURRENT_SOURCE_H))
		endif
		
		NEURON_INCLUDE_FILES := \
	      $(NEURON_MODEL_H) \
	      $(SYNAPSE_TYPE_H) \
	      $(INPUT_TYPE_H) \
	      $(THRESHOLD_TYPE_H) \
	      $(ADDITIONAL_INPUT_H) \
	      $(CURRENT_SOURCE_H) \
	      $(NEURON_IMPL_H) 
		NEURON_INCLUDES := $(NEURON_INCLUDE_FILES:%=-include %)
    endif
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
SOURCES = neuron/c_main.c \
          neuron/synapses.c \
          neuron/neuron.c \
          neuron/spike_processing.c \
          neuron/population_table/population_table_$(POPULATION_TABLE_IMPL)_impl.c \
          $(SYNAPSE_DYNAMICS) $(WEIGHT_DEPENDENCE) \
          $(TIMING_DEPENDENCE) $(SYNAPTOGENESIS_DYNAMICS) \
          $(PARTNER_SELECTION) $(FORMATION) $(ELIMINATION) $(OTHER_SOURCES_CONVERTED)

include $(SPINN_DIRS)/make/local.mk

FEC_OPT = $(OTIME)

# Synapse build rules
SYNAPSE_TYPE_COMPILE = $(CC) -DLOG_LEVEL=$(SYNAPSE_DEBUG) $(CFLAGS) -DSTDP_ENABLED=$(STDP_ENABLED)

$(BUILD_DIR)neuron/c_main.o: $(MODIFIED_DIR)neuron/c_main.c
	#c_main.c
	-@mkdir -p $(dir $@)
	$(SYNAPSE_TYPE_COMPILE) -o $@ $<

$(BUILD_DIR)neuron/synapses.o: $(MODIFIED_DIR)neuron/synapses.c
	#synapses.c
	-@mkdir -p $(dir $@)
	$(SYNAPSE_TYPE_COMPILE) -o $@ $<

$(BUILD_DIR)neuron/spike_processing.o: $(MODIFIED_DIR)neuron/spike_processing.c
	#spike_processing.c
	-@mkdir -p $(dir $@)
	$(SYNAPSE_TYPE_COMPILE) -o $@ $<

$(BUILD_DIR)neuron/population_table/population_table_binary_search_impl.o: $(MODIFIED_DIR)neuron/population_table/population_table_binary_search_impl.c
	#population_table/population_table_binary_search_impl.c
	-@mkdir -p $(dir $@)
	$(SYNAPSE_TYPE_COMPILE) -o $@ $<

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
	# $(SYNAPTOGENESIS_DYNAMICS) Synapese
	-@mkdir -p $(dir $@)
	$(SYNAPSE_TYPE_COMPILE) $(SYNGEN_INCLUDES) -o $@ $<

    $(SYNAPSE_DYNAMICS_O): $(SYNAPSE_DYNAMICS_C)
	# SYNAPSE_DYNAMICS_O Synapese
	-@mkdir -p $(dir $@)
	$(SYNAPSE_TYPE_COMPILE) -o $@ $<

endif

$(WEIGHT_DEPENDENCE_O): $(WEIGHT_DEPENDENCE_C) $(SYNAPSE_TYPE_H) $(MAKEFILE_LIST)
	# WEIGHT_DEPENDENCE_O
	-@mkdir -p $(dir $@)
	$(CC) -DLOG_LEVEL=$(PLASTIC_DEBUG) $(CFLAGS) \
	        -o $@ $<

$(TIMING_DEPENDENCE_O): $(TIMING_DEPENDENCE_C) $(SYNAPSE_TYPE_H) \
                        $(WEIGHT_DEPENDENCE_H) $(MAKEFILE_LIST)
	# TIMING_DEPENDENCE_O
	-@mkdir -p $(dir $@)
	$(CC) -DLOG_LEVEL=$(PLASTIC_DEBUG) $(CFLAGS) \
	        -include $(WEIGHT_DEPENDENCE_H) -o $@ $<

$(PARTNER_SELECTION_O): $(PARTNER_SELECTION_C) $(SYNAPSE_TYPE_H) $(MAKEFILE_LIST)
	# PARTNER_SELECTION_O
	-mkdir -p $(dir $@)
	$(CC) -DLOG_LEVEL=$(PLASTIC_DEBUG) $(CFLAGS) \
	        -include $(SYNAPSE_TYPE_H) -o $@ $<

$(FORMATION_O): $(FORMATION_C) $(SYNAPSE_TYPE_H) $(MAKEFILE_LIST)
	# FORMATION_O
	-mkdir -p $(dir $@)
	$(CC) -DLOG_LEVEL=$(PLASTIC_DEBUG) $(CFLAGS) \
	        -include $(SYNAPSE_TYPE_H) -o $@ $<

$(ELIMINATION_O): $(ELIMINATION_C) $(SYNAPSE_TYPE_H) $(MAKEFILE_LIST)
	# ELIMINATION_O
	-mkdir -p $(dir $@)
	$(CC) -DLOG_LEVEL=$(PLASTIC_DEBUG) $(CFLAGS) \
	        -include $(SYNAPSE_TYPE_H) -o $@ $<

$(BUILD_DIR)neuron/neuron.o: $(MODIFIED_DIR)neuron/neuron.c $(NEURON_INCLUDE_FILES) $(MAKEFILE_LIST)
	# neuron.o
	-@mkdir -p $(dir $@)
	$(CC) -DLOG_LEVEL=$(NEURON_DEBUG) $(CFLAGS) $(NEURON_INCLUDES) -o $@ $<

.PRECIOUS: $(MODIFIED_DIR)%.c $(MODIFIED_DIR)%.h $(LOG_DICT_FILE) $(EXTRA_PRECIOUS)
