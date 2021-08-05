#include <stdlib.h>
#include "configInterface.h"

int main(int argc, char *argv[]) {
    try {
        std::vector<arg_config> vlans;
        initialize_swss(&vlans);
        loop_relay(&vlans);
    }
    catch (std::exception &e)
    {
        printf("Usage: -i <interface> -o <option>\n");
        return 1;
    }
    return 0;
}
