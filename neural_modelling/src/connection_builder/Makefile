all:
	(cd builder && "$(MAKE)") || exit $$?
	(cd builder && "$(MAKE)" PROFILER_ENABLED=1) || exit $$?

clean:
	(cd builder && "$(MAKE)" clean) || exit $$?
	(cd builder && "$(MAKE)" clean PROFILER_ENABLED=1) || exit $$?