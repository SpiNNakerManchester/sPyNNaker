# Copyright (c) 2021-2022 The University of Manchester
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
CHECK_PATH := $(NEURAL_MODELLING_DIRS)/makefiles/local_only_synapse_only/local_only.mk
ifneq ($(CHECK_PATH), $(MAKEFILE_PATH))
    $(error Please check NEURAL_MODELLING_DIRS as based on that this file is at $(CHECK_PATH) when it is actually at $(MAKEFILE_PATH))
endif

# Set logging levels
ifeq ($(SPYNNAKER_DEBUG), DEBUG)
    LOCAL_ONLY_DEBUG = LOG_DEBUG
endif

ifndef LOCAL_ONLY_DEBUG
    LOCAL_ONLY_DEBUG = LOG_INFO
endif

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

ifndef LOCAL_ONLY_IMPL
    $(error LOCAL_ONLY_IMPL is not set.  Please choose an implementation to compile)
else
    LOCAL_ONLY_IMPL := $(call strip_source_dirs,$(LOCAL_ONLY_IMPL))
endif

OTHER_SOURCES_CONVERTED := $(call strip_source_dirs,$(OTHER_SOURCES))

# List all the sources relative to one of SOURCE_DIRS
SOURCES = neuron/c_main_local_only_synapses.c \
          neuron/local_only_fast.c \
          $(LOCAL_ONLY_IMPL) $(OTHER_SOURCES_CONVERTED)

include $(SPINN_DIRS)/make/local.mk

FEC_OPT = $(OTIME)

$(BUILD_DIR)neuron/c_main_local_only_synapses.o: $(MODIFIED_DIR)neuron/c_main_local_only_synapses.c
	#c_main.c
	-@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -o $@ $<

.PRECIOUS: $(MODIFIED_DIR)%.c $(MODIFIED_DIR)%.h $(LOG_DICT_FILE) $(EXTRA_PRECIOUS)
