#include <stdlib.h>
#include "configInterface.h"

int main(int argc, char *argv[]) {
    try {
        auto parser = ArgumentParser();
        parser.parse_args(argc, argv);
        auto context = parser.get_arg();
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