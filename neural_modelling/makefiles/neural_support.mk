# Copyright (c) 2017 The University of Manchester
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

# Makefile for building neural modelling C code for sPyNNaker specifically

MAKEFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
SPYNNAKER_DIR := $(abspath $(dir $(MAKEFILE_PATH))/../../)/

BUILD_DIR := $(SPYNNAKER_DIR)neural_modelling/builds/$(APP)/
APP_OUTPUT_DIR := $(SPYNNAKER_DIR)spynnaker/pyNN/model_binaries/
# key for the database in this APP_OUTPUT_DIR
DATABASE_KEY = S

include $(SPYNNAKER_DIR)neural_modelling/make/neural_support.mk
