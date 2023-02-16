# Copyright (c) 2014 The University of Manchester
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
SLLT_TAG=http://spinnakermanchester.github.io/spinnaker_tools/sllt.tag
COMMON_TAG=http://spinnakermanchester.github.io/spinn_common/common.tag
FEC_TAG=http://spinnakermanchester.github.io/SpiNNFrontEndCommon/c/fec.tag

DOXYGEN ?= doxygen
WGET ?= wget

all: $(DIRS)
	for d in $(DIRS); do $(MAKE) -C $$d || exit $$?; done

clean: $(DIRS)
	for d in $(DIRS); do $(MAKE) -C $$d clean || exit $$?; done

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

.PHONY: all clean doxygen doxysetup
