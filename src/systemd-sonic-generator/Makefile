CC=gcc
CFLAGS=-std=gnu99

BINARY = systemd-sonic-generator
MAIN_TARGET = $(BINARY)_1.0.0_$(CONFIGURED_ARCH).deb
DERIVED_TARGETS = $(BINARY)-dbgsym_1.0.0_$(CONFIGURED_ARCH).deb

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	dpkg-buildpackage -us -uc -b
	mv ../$(MAIN_TARGET) $(DEST)/
	rm ../$(BINARY)_*
	$(foreach dbg_deb, $(DERIVED_TARGETS), \
		{ if [ -e $(dbg_deb) ]; then mv $(dbg_deb) $(DEST)/; fi };)

$(BINARY): systemd-sonic-generator.c
	rm -f ./systemd-sonic-generator

	$(CC) $(CFLAGS) -o $@ $^

install: $(BINARY)
	mkdir -p $(DESTDIR)
	mkdir -p $(DESTDIR)/lib
	mkdir -p $(DESTDIR)/lib/systemd
	mkdir -p $(DESTDIR)/lib/systemd/system-generators
	cp ./systemd-sonic-generator $(DESTDIR)/lib/systemd/system-generators
