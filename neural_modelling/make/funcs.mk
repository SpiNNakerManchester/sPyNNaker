# See Notes in sPyNNaker/neural_modelling/CHANGES_April_2018

# Copyright (c) 2025 The University of Manchester
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

# Define a rule to find the source directory of the given file.
# This attempts to find each of SOURCE_DIRS within the given file name; the
# first one that matches is then returned.  If none match, an empty string
# will be returned.

# Get one of the paths from the colon separated pair in SOURCE_DIRS
# $1 = colon separated pair
# $2 = 1 for original source dir, 2 for modified source dir
get_path = $(abspath $(word $2, $(subst :, ,$1)))/

# Get the source directory for a given file
define get_source_dir#(file)
$(firstword $(strip $(foreach d, $(SOURCE_DIRS), $(findstring $(call get_path,$(d),1), $(1)))))
endef

# Get the modified source directory for a given source directory
define get_mod_dir#(src_dir)
$(call get_path,$(firstword $(strip $(foreach d, $(SOURCE_DIRS), $(findstring $(1):, $(d))))), 2)
endef

# Define rule to strip any SOURCE_DIRS from source_file to allow use via local.mk.
# If no match is found, the value is returned untouched
# (though this will probably fail later).
define strip_source_dirs#(source_file)
$(or $(patsubst $(call get_source_dir, $(1))%,%,$(1)), $(1))
endef

# Define a rule to replace any SOURCE_DIRS from header_file with the modified_src folder.
define replace_source_dirs#(header_file)
$(foreach d, $(SOURCE_DIRS), $(patsubst $(call get_path,$(d),1)%, $(call get_path,$(d),2)%, $(filter $(call get_path,$(d),1)%,$(1))))
endef
