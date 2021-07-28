#include <stdlib.h>
#include "configInterface.h"

int main(int argc, char *argv[]) {
    try {
        arg_config context;
        initialize_swss(&context);
        loop_relay(&context);
    }
    catch (std::exception &e)
    {
        printf("Usage: -i <interface> -o <option>\n");
        return 1;
    }
    return 0;
}
