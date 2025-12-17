# Copyright (c) 2021 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

ifndef FEC_INSTALL_DIR:
    CUR_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/)
    # assume parallel clone
    FEC_INSTALL_DIR := $(abspath $(CUR_DIR)/../../../SpiNNFrontEndCommon/c_common/front_end_common_lib)
endif

MAKEFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
CURRENT_DIR := $(abspath $(dir $(MAKEFILE_PATH)))
NEURAL_MODELLING_DIRS := $(abspath $(dir $(MAKEFILE_PATH))/../)/

# Set logging levels
ifeq ($(SPYNNAKER_DEBUG), DEBUG)
    NEURON_DEBUG = LOG_DEBUG
    LOCAL_ONLY_DEBUG = LOG_DEBUG
endif

ifndef NEURON_DEBUG
    NEURON_DEBUG = LOG_INFO
endif

ifndef LOCAL_ONLY_DEBUG
    LOCAL_ONLY_DEBUG = LOG_INFO
endif

# Add source directory

# Define the directories
NEURON_DIR := $(abspath $(NEURAL_MODELLING_DIRS)/src)
NEURON_MODIFIED_DIR := $(abspath $(NEURAL_MODELLING_DIRS)/modified_src)/
SOURCE_DIRS += $(NEURON_DIR):$(NEURON_MODIFIED_DIR)

include $(CURRENT_DIR)/funcs.mk

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
		    ADDITIONAL_INPUT_H = $(NEURON_MODIFIED_DIR)neuron/additional_inputs/additional_input_none_impl.h
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
		    CURRENT_SOURCE_H = $(NEURON_MODIFIED_DIR)neuron/current_sources/current_source_impl.h
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

ifndef LOCAL_ONLY_IMPL
    $(error LOCAL_ONLY_IMPL is not set.  Please choose an implementation to compile)
else
    LOCAL_ONLY_IMPL := $(call strip_source_dirs,$(LOCAL_ONLY_IMPL))
endif

OTHER_SOURCES_CONVERTED := $(call strip_source_dirs,$(OTHER_SOURCES))

# List all the sources relative to one of SOURCE_DIRS
SOURCES = neuron/c_main_local_only.c \
          neuron/neuron.c \
          neuron/local_only.c \
          $(LOCAL_ONLY_IMPL) $(OTHER_SOURCES_CONVERTED)

include $(FEC_INSTALL_DIR)/make/fec.mk

FEC_OPT = $(OTIME)

$(BUILD_DIR)neuron/c_main_local_only.o: $(NEURON_MODIFIED_DIR)neuron/c_main_local_only.c
	#c_main.c
	-@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -o $@ $<

$(BUILD_DIR)neuron/spike_processing_local_only.o: $(NEURON_MODIFIED_DIR)neuron/spike_processing_local_only.c
	#spike_processing.c
	-@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -o $@ $<

$(BUILD_DIR)neuron/neuron.o: $(NEURON_MODIFIED_DIR)neuron/neuron.c
	# neuron.o
	-@mkdir -p $(dir $@)
	$(CC) -DLOG_LEVEL=$(NEURON_DEBUG) $(CFLAGS) $(NEURON_INCLUDES) -o $@ $<

.PRECIOUS: $(NEURON_MODIFIED_DIR)%.c $(NEURON_MODIFIED_DIR)%.h $(LOG_DICT_FILE) $(EXTRA_PRECIOUS)
