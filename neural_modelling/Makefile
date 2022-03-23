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

BUILDS = synapse_expander \
         bit_field_expander \
         spike_source/poisson \
         delay_extension \
         robot_motor_control \
         neuron_only \
         synapse_only \
         neuron 

DIRS = $(BUILDS:%=makefiles/%)

APP_OUTPUT_DIR =  $(abspath $(dir $(MAKEFILE_PATH))../spynnaker/pyNN/model_binaries)/

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

install-clean:
	$(info Deleted all old files in "$(APP_OUTPUT_DIR)")
	$(RM) $(APP_OUTPUT_DIR)*.dict $(APP_OUTPUT_DIR)logs.sqlite3  $(APP_OUTPUT_DIR)*.aplx

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
