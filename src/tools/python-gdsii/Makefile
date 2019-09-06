PYCHECKER_MOULES = gdsii gdsii.library gdsii.structure gdsii.elements gdsii.types gdsii.tags \
		   gdsii._records gdsii.exceptions gdsii.record

PYTHON ?= python

help:
	@echo Commands: doc clean check pychecker

doc:
	$(MAKE) -C doc html

clean: clean-pyc
	rm -rf build dist
	rm -f MANIFEST
	$(MAKE) -C doc clean

clean-pyc:
	find . -name '*.py[co]' -print0 | xargs -r0 rm --

check:
	$(PYTHON) -m gdsii.record
	$(PYTHON) -m gdsii.tags
	$(PYTHON) -m test.test_record
	$(PYTHON) -m test.test_lib 

pychecker:
	pychecker -J 20 $(PYCHECKER_MOULES)

.PHONY: clean clean-pyc doc check pychecker
