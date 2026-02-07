CHECK_PROFILE ?= fast

.PHONY: check
check:
	@CHECK_PROFILE=$(CHECK_PROFILE) sh scripts/check.sh
