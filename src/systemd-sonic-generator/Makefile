CC=gcc
CFLAGS=-std=gnu99

MAIN_TARGET = systemd-sonic-generator

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	rm -f ./systemd-sonic-generator
	
	$(CC) $(CFLAGS) -o $@ systemd-sonic-generator.c
