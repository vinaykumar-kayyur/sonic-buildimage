#disable some warning because UT need test functions not in header file.
CFLAGS = -Wno-parentheses -Wno-format-security -Wno-implicit-function-declaration -Wno-int-to-pointer-cast -c
IFLAGS = -I.. -I../include -I../lib
MFLAG = -DDEBUG -DBASH_PLUGIN_UT

all:
	gcc plugin_test.c $(IFLAGS) $(CFLAGS) -o plugin_test.o
	gcc mock_helper.c $(IFLAGS) $(CFLAGS) -o mock_helper.o
	gcc ../bash_tacplus.c   $(IFLAGS) $(CFLAGS) $(MFLAG) -o bash_tacplus.o
	gcc  plugin_test.o  mock_helper.o bash_tacplus.o -o plugin_test  -lc -lcunit 

clean:
	rm *.o
	rm plugin_test
