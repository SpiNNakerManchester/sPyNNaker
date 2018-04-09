COMMON_MODIFIED_DIR =  $(NEURAL_MODELLING_DIRS)/src/common_modified/

RAW_FILES = $(shell find $(NEURAL_MODELLING_DIRS)/src/common -name '*.c')
RAW_FILES += $(shell find $(NEURAL_MODELLING_DIRS)/src/common -name '*.h')

_MODIFIED_FILES = $(RAW_FILES)
$(eval _MODIFIED_FILES := $(_MODIFIED_FILES:$(RAW_DIR)%=$(COMMON_MODIFIED_DIR)%))

_DICT_FILES = $(sort $(RAW_FILES))
$(eval _DICT_FILES := $(_DICT_FILES:$(RAW_DIR)%.c=$(COMMON_MODIFIED_DIR)%.cdict))
$(eval _DICT_FILES := $(_DICT_FILES:$(RAW_DIR)%.h=$(COMMON_MODIFIED_DIR)%.hdict))

_COMMON_DICT_FILE =  $(COMMON_MODIFIED_DIR)common.dict

$(COMMON_MODIFIED_DIR): $(_MODIFIED_FILES) $(_COMMON_DICT_FILE)


_COMMON_RANGE_FILE = $(abspath $(COMMON_MODIFIED_DIR))/log_ranges.txt
# SpiNNFrontEndCommon/c_common/front_end_common_lib is 2000 range
_COMMON_RANGE_START = 3000

# Rule to create all the modified c files
$(COMMON_MODIFIED_DIR)%.c $(COMMON_MODIFIED_DIR)%.cdict: $(RAW_DIR)%.c
	python -m spinn_utilities.make_tools.file_convertor $< $(COMMON_MODIFIED_DIR)$*.c $(_COMMON_RANGE_FILE) $(_COMMON_RANGE_START)

# Rule to create all the modified h files
$(COMMON_MODIFIED_DIR)%.h $(COMMON_MODIFIED_DIR)%.hdict: $(RAW_DIR)%.h
	python -m spinn_utilities.make_tools.file_convertor $< $(COMMON_MODIFIED_DIR)$*.h $(RANGE_FILE) $(RANGE_START)

# At the end we want all the dict files merged
$(_COMMON_DICT_FILE): $(_DICT_FILES)
	head -n 2 $(firstword $(_DICT_FILES)) > $(_COMMON_DICT_FILE)
	$(foreach dict, $(_DICT_FILES), tail -n+3 $(dict) >> $(_COMMON_DICT_FILE);)

COMMON_PRECIOUS := $(_MODIFIED_FILES) $(_DICT_FILES) $(_COMMON_DICT_FILE)