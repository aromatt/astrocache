.ONESHELL:
SHELL:=/bin/bash

.PHONY: test
test:
	PYTHONPATH=. ./snapshot.py

.PHONY: update-snapshot
update-snapshot:
	PYTHONPATH=. ./snapshot.py -u
