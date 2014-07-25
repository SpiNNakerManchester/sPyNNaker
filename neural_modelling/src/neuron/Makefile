MODELS = IF_curr_exp IF_curr_delta IF_cond_exp IZK_curr_exp IZK_curr_delta IF_curr_exp_stdp_trace_pair IF_curr_exp_stdp_trace_nearest_pair IF_curr_exp_dual
BUILD_DIRS := $(addprefix builds/, $(MODELS))

all: $(BUILD_DIRS)
	for d in $(BUILD_DIRS); do (cd $$d; "$(MAKE)") || exit $$?; done

clean: $(BUILD_DIRS)
	for d in $(BUILD_DIRS); do (cd $$d; "$(MAKE)" clean) || exit $$?; done
