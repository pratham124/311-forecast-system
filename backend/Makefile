# Run repo-wide targets from backend/ (the main Makefile lives one level up).
ROOT := $(abspath ..)

.PHONY: help
help:
	@$(MAKE) -C $(ROOT) help

%:
	@$(MAKE) -C $(ROOT) $@
