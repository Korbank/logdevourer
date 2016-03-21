#!/usr/bin/make -f

.PHONY: all man build install clean

all: build

build:
	python setup.py $@

install:
	python setup.py $@ $(if $(DESTDIR),--root=$(DESTDIR))

man: man/logdevd.8

man/logdevd.8: man/logdevd.pod
	pod2man --section=8 --center="Linux System Administration" --release="" $< $@

clean:
	python setup.py $@ --all
	rm -rf pylib/*.egg-info
