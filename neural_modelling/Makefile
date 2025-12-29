# Copyright (c) 2014 The University of Manchester
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

MAKEFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
NEURAL_MODELLING_DIRS := $(abspath $(dir $(MAKEFILE_PATH)))
APP_OUTPUT_DIR := $(NEURAL_MODELLING_DIRS)/../spynnaker/pyNN/model_binaries/

BUILDS = synapse_expander \
         spike_source/poisson \
         delay_extension \
         robot_motor_control \
         neuron_only \
         synapse_only \
         neuron \
         local_only_combined

DIRS = $(BUILDS:%=makefiles/%)

# Locations of tag files
TAGFILES=sllt.tag common.tag fec.tag
SLLT_TAG=https://spinnakermanchester.github.io/spinnaker_tools/sllt.tag
COMMON_TAG=https://spinnakermanchester.github.io/spinn_common/common.tag
FEC_TAG=https://spinnakermanchester.github.io/SpiNNFrontEndCommon/c/fec.tag

DOXYGEN ?= doxygen
WGET ?= wget
INSTALL ?= install
MKDIR ?= mkdir -p
RM ?= rm -f

all: $(DIRS)
	for d in $(DIRS); do $(MAKE) -C $$d || exit $$?; done

clean: $(DIRS)
	$(RM) $(APP_OUTPUT_DIR)logs.sqlite3
	$(RM) $(APP_OUTPUT_DIR)*.aplx
	$(RM) -r $(NEURAL_MODELLING_DIRS)/modified_src

	for d in $(DIRS); do $(MAKE) -C $$d clean || exit $$?; done

INSTALL_ERROR := neural_modelling install is only required if you are building in a temporary location.
INSTALL_ERROR += In which case you must set the environment variable SPYNNAKER_INSTALL_DIR to where the install should go.
INSTALL_ERROR += This environment variable must also exist for all higher level makes.

# This installs the source and makefiles into a central location so that
# other projects can make use if it
install: $(DIRS)
	$(eval SPYNNAKER_INSTALL_DIR := $(strip $(if $(SPYNNAKER_INSTALL_DIR), $(SPYNNAKER_INSTALL_DIR), $(error $(INSTALL_ERROR)))))
	for d in $(DIRS); do $(MAKE) -C $$d || exit $$?; done
	$(MKDIR) $(SPYNNAKER_INSTALL_DIR)/src
	$(MKDIR) $(SPYNNAKER_INSTALL_DIR)/modified_src
	$(MKDIR) $(SPYNNAKER_INSTALL_DIR)/make

	for d in $$(find $(NEURAL_MODELLING_DIRS)/src -type d -printf '%P\n' ); do install -d --mode 755 "$(NEURAL_MODELLING_DIRS)/src/$$d" "$(SPYNNAKER_INSTALL_DIR)/src/$$d"; done
	for f in $$(find $(NEURAL_MODELLING_DIRS)/src -type f -printf '%P\n' ); do install --mode 644 "$(NEURAL_MODELLING_DIRS)/src/$$f" "$(SPYNNAKER_INSTALL_DIR)/src/$$f"; done
	for d in $$(find $(NEURAL_MODELLING_DIRS)/modified_src -type d -printf '%P\n' ); do install -d --mode 755 "$(NEURAL_MODELLING_DIRS)/modified_src/$$d" "$(SPYNNAKER_INSTALL_DIR)/modified_src/$$d"; done
	for f in $$(find $(NEURAL_MODELLING_DIRS)/modified_src -type f -printf '%P\n' ); do install --mode 644 "$(NEURAL_MODELLING_DIRS)/modified_src/$$f" "$(SPYNNAKER_INSTALL_DIR)/modified_src/$$f"; done
	$(INSTALL) $(NEURAL_MODELLING_DIRS)/make/* $(SPYNNAKER_INSTALL_DIR)/make

sllt.tag: .sllt_template.tag
	cp .sllt_template.tag sllt.tag
ifneq (, $(shell which $(WGET)))
	-$(WGET) -q -O sllt.tag $(SLLT_TAG)
endif

common.tag: .common_template.tag
	cp .common_template.tag common.tag
ifneq (, $(shell which $(WGET)))
	-$(WGET) -q -O common.tag $(COMMON_TAG)
endif

fec.tag: .fec_template.tag
	cp .fec_template.tag fec.tag
ifneq (, $(shell which $(WGET)))
	-$(WGET) -q -O fec.tag $(FEC_TAG)
endif

doxygen: $(TAGFILES)
	$(DOXYGEN)
doxysetup: $(TAGFILES)

.PHONY: all clean install doxygen doxysetup
