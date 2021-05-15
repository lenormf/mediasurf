PREFIX ?= /usr/local
DESTDIR ?= # root dir

bindir := $(DESTDIR)$(PREFIX)/bin
sharedir := $(DESTDIR)$(PREFIX)/share/mediasurf

all:
	: #

installdirs:
	install -d $(bindir) $(sharedir)

install: installdirs
	install -m 0755 mediasurf.py $(bindir)/mediasurf
	cp -r runtime/* $(sharedir)/

.PHONY: all install installdirs
