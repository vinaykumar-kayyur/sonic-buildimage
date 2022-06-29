PREFIX   ?=

CC       := g++
CXX      := g++

CFLAGS   := -Os -g -fPIC -Wall -Werror -Wno-uninitialized -Wno-format-truncation \
            -I/usr/include/sai
CFLAGS   += $(SONIC_COMMON_CFLAGS)
CXXFLAGS := $(CFLAGS)
LDFLAGS  := $(SONIC_COMMON_LDFLAGS)

SRCS   := mdio_ipc_client.cpp
OBJS   := $(SRCS:.cpp=.o)

all: libmdio_ipc_client.so

$(OBJS) :%.o:%.cpp
	$(CXX) -c -o $@ $^ $(CXXFLAGS)


libmdio_ipc_client.so: $(OBJS)
	$(CXX) -shared -o $@ $^ $(LDFLAGS)

clean:
	rm -f libmdio_ipc_client.so *.o
