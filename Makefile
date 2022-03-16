.ONESHELL:
SHELL:=/bin/bash

.PHONY: test
test:
	PYTHONPATH=. ./snapshot.py
