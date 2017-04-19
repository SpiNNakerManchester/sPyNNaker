CURRENT_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
SOURCE_DIR := $(abspath $(CURRENT_DIR))
SOURCE_DIRS += $(SOURCE_DIR)
ifndef APP_OUTPUT_DIR
    APP_OUTPUT_DIR := $(abspath $(CURRENT_DIR)../../spynnaker/pyNN/model_binaries/)/
endif
