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

ifndef SYNAPSE_DYNAMICS
    $(error SYNAPSE_DYNAMICS is not set.  Please select a synapse dynamics implementation)
else
    SYNAPSE_DYNAMICS_C := $(call replace_source_dirs,$(SYNAPSE_DYNAMICS))
    SYNAPSE_DYNAMICS := $(call strip_source_dirs,$(SYNAPSE_DYNAMICS))
    SYNAPSE_DYNAMICS_O := $(BUILD_DIR)$(SYNAPSE_DYNAMICS:%.c=%.o)

    SYNAPSE_DYNAMICS_STATIC := synapse/plasticity/synapse_dynamics_static_impl.c
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

ifdef COMPARTMENT_TYPE_H
	COMPARTMENT_TYPE := $(call strip_source_dirs,$(COMPARTMENT_TYPE_H))
	COMPARTMENT_TYPE_H := $(call replace_source_dirs, $(COMPARTMENT_TYPE_H))
    SYNAPSE_INCLUDES := -include $(COMPARTMENT_TYPE_H)
endif

SYNGEN_ENABLED = 1
ifndef SYNAPTOGENESIS_DYNAMICS
    SYNAPTOGENESIS_DYNAMICS := synapse/structural_plasticity/synaptogenesis_dynamics_static_impl.c
    SYNAPTOGENESIS_DYNAMICS_C := $(MODIFIED_DIR)$(SYNAPTOGENESIS_DYNAMICS)
    SYNGEN_ENABLED = 0
else
    SYNAPTOGENESIS_DYNAMICS_C := $(call replace_source_dirs,$(SYNAPTOGENESIS_DYNAMICS))
    SYNAPTOGENESIS_DYNAMICS := $(call strip_source_dirs,$(SYNAPTOGENESIS_DYNAMICS))
endif
SYNAPTOGENESIS_DYNAMICS_O := $(BUILD_DIR)$(SYNAPTOGENESIS_DYNAMICS:%.c=%.o)

OTHER_SOURCES_CONVERTED := $(call strip_source_dirs,$(OTHER_SOURCES))

ifndef PACKET_COMPRESSOR
    SPIKE_PROCESSING := synapse/spike_processing.c
else
    SPIKE_PROCESSING := synapse/spike_processing_compressor.c
endif

# List all the sources relative to one of SOURCE_DIRS
SOURCES = common/rate_buffer.c \
        common/out_spikes.c \
		synapse/c_main.c \
		synapse/synapses.c \
		$(SPIKE_PROCESSING) \
		synapse/population_table/population_table_$(POPULATION_TABLE_IMPL)_impl.c \
		$(SYNAPSE_DYNAMICS) $(WEIGHT_DEPENDENCE) \
		$(TIMING_DEPENDENCE) $(SYNAPTOGENESIS_DYNAMICS) $(OTHER_SOURCES_CONVERTED)

include $(SPINN_DIRS)/make/local.mk

FEC_OPT = $(OSPACE)

# Synapse build rules
SYNAPSE_TYPE_COMPILE = $(CC) -DLOG_LEVEL=$(SYNAPSE_DEBUG) $(CFLAGS) -DSTDP_ENABLED=$(STDP_ENABLED)

$(BUILD_DIR)synapse/c_main.o: $(MODIFIED_DIR)synapse/c_main.c
	#syn_c_cmain.c
	-mkdir -p $(dir $@)
	$(SYNAPSE_TYPE_COMPILE) -o $@ $<

$(BUILD_DIR)synapse/synapses.o: $(MODIFIED_DIR)synapse/synapses.c
	#synapses.c
	-mkdir -p $(dir $@)
	$(SYNAPSE_TYPE_COMPILE) $(SYNAPSE_INCLUDES) -o $@ $<

$(BUILD_DIR)synapse/spike_processing.o: $(MODIFIED_DIR)$(SPIKE_PROCESSING)
	#spike_processing.c
	-mkdir -p $(dir $@)
	$(SYNAPSE_TYPE_COMPILE) -o $@ $<

$(BUILD_DIR)synapse/population_table/population_table_fixed_impl.o: $(MODIFIED_DIR)synapse/population_table/population_table_fixed_impl.c
	#population_table/population_table_fixed_impln.c
	-mkdir -p $(dir $@)
	$(SYNAPSE_TYPE_COMPILE) -o $@ $<

$(BUILD_DIR)synapse/population_table/population_table_binary_search_impl.o: $(MODIFIED_DIR)synapse/population_table/population_table_binary_search_impl.c
	#population_table/population_table_binary_search_impl
	-mkdir -p $(dir $@)
	$(SYNAPSE_TYPE_COMPILE) -o $@ $<

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
	$(STDP_COMPILE) -o $@ $<

    $(BUILD_DIR)synapse/plasticity/common/post_events.o: $(MODIFIED_DIR)synapse/plasticity/common/post_events.c
	# plasticity/common/post_events.c
	-@mkdir -p $(dir $@)
	$(STDP_COMPILE) -o $@ $<

else
    $(SYNAPTOGENESIS_DYNAMICS_O): $(SYNAPTOGENESIS_DYNAMICS_C)
	# $(SYNAPTOGENESIS_DYNAMICS) Synapese
	-@mkdir -p $(dir $@)
	$(SYNAPSE_TYPE_COMPILE) -o $@ $<

    $(SYNAPSE_DYNAMICS_O): $(SYNAPSE_DYNAMICS_C)
	# SYNAPSE_DYNAMICS_O Synapese
	-@mkdir -p $(dir $@)
	$(SYNAPSE_TYPE_COMPILE) -o $@ $<

endif

$(WEIGHT_DEPENDENCE_O): $(WEIGHT_DEPENDENCE_C) $(SYNAPSE_TYPE_H)
	# WEIGHT_DEPENDENCE_O
	-@mkdir -p $(dir $@)
	$(CC) -DLOG_LEVEL=$(PLASTIC_DEBUG) $(CFLAGS) \
	        -o $@ $<

$(TIMING_DEPENDENCE_O): $(TIMING_DEPENDENCE_C) $(SYNAPSE_TYPE_H) \
                        $(WEIGHT_DEPENDENCE_H)
	# TIMING_DEPENDENCE_O
	-@mkdir -p $(dir $@)
	$(CC) -DLOG_LEVEL=$(PLASTIC_DEBUG) $(CFLAGS) \
	        -include $(WEIGHT_DEPENDENCE_H) -o $@ $<

.PRECIOUS: $(MODIFIED_DIR)%.c $(MODIFIED_DIR)%.h $(LOG_DICT_FILE) $(EXTRA_PRECIOUS)