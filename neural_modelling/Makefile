BUILDS = compressor_with_bit_field \
         spike_source/poisson \
         delay_extension \
         neuron \
         robot_motor_control \
         synapse_expander \
         bit_field_expander
DIRS = $(BUILDS:%=makefiles/%)

all: $(DIRS)
	for d in $(DIRS); do $(MAKE) -C $$d || exit $$?; done

clean: $(DIRS)
	for d in $(DIRS); do $(MAKE) -C $$d clean || exit $$?; done
