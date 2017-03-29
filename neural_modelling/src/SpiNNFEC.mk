# If SPINN_DIRS is not defined, this is an error!
ifndef SPINN_DIRS
    $(error SPINN_DIRS is not set.  Please define SPINN_DIRS (possibly by running "source setup" in the spinnaker package folder))
endif

ifndef SOURCE_DIRS
    $(error SOURCE_DIRS is not set.  Please define SOURCE_DIRS)
endif

ifndef APP_OUTPUT_DIR
    $(error APP_OUTPUT_DIR is not set.  Please define APP_OUTPUT_DIR)
endif

ifndef BUILD_DIR
    $(error BUILD_DIR is not set.  Please define BUILD_DIR)
endif

define define-build-code
$(call build_dir,$1/%.c): $1/%.c
	@-$$(MKDIR) $$(dir $$@)
	@echo "DEFINE_BUILD_CODE $$<"
	$$(CC) $$(CFLAGS) -D__FILENAME__=\"$$(notdir $$<)\" -o $$@ $$<
endef

define source_dir
$(firstword $(abspath $(strip $(foreach dir, $(sort $(SOURCE_DIRS)), $(findstring $(dir), $(1))))))
endef

define build_dir
$$(BUILD_DIR)$$(patsubst %.c,%.o,$$(notdir $(1)))
endef

# Convert the objs into the correct format to work here
$(foreach dir, $(sort $(SOURCE_DIRS)), $(eval $(call define-build-code,$(dir))))
OBJECTS += $(addprefix $(BUILD_DIR),$(notdir $(SOURCES:.c=.o)))

ifdef SPINN_COMMON
    CFLAGS += -I$(SPINN_COMMON)/include
endif

ifdef SPINN_FEC
    CFLAGS += -I$(SPINN_FEC)/include
endif

LIBRARIES += -lspinn_frontend_common -lspinn_common -lm
FEC_DEBUG := PRODUCTION_CODE
# Run md5sum on application name and extract first 8 bytes
SHELL = bash
APPLICATION_NAME_HASH = $(shell echo -n "$(APP)" | sh -c 'md5sum 2>/dev/null||md5 -q' | cut -c 1-8)

CFLAGS += -Wall -Wextra -D$(FEC_DEBUG) $(OTIME) -DAPPLICATION_NAME_HASH=0x$(APPLICATION_NAME_HASH)

include $(SPINN_DIRS)/make/Makefile.common

all: $(APP_OUTPUT_DIR)$(APP).aplx

# Tidy and cleaning dependencies
clean:
	$(RM) $(OBJECTS) $(BUILD_DIR)$(APP).elf $(BUILD_DIR)$(APP).txt $(APP_OUTPUT_DIR)$(APP).aplx
