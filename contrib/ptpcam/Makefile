CC=gcc
CFLAGS=$(shell pkg-config --cflags libusb-1.0) -w
LDFLAGS=$(shell pkg-config --libs libusb-1.0)

all: ptpcam

clean:
	-rm ptpcam

ptpcam: config.h libptp-endian.h libptp-stdint.h myusb.c properties.c ptp-pack.c ptp.c ptp.h ptpcam.c ptpcam.h
	$(CC) -o ptpcam myusb.c properties.c ptp.c ptpcam.c $(CFLAGS) $(LDFLAGS)
