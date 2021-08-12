#include <stdlib.h>
#include "configInterface.h"

int main(int argc, char *argv[]) {
    try {
        std::vector<arg_config> vlans;
        swss::DBConnector state_db(6, "localhost", 6379, 0);
        initialize_swss(&vlans, &state_db);
        loop_relay(&vlans, &state_db);
    }
    catch (std::exception &e)
    {
        printf("An exception occurred.\n");
        return 1;
    }
    return 0;
}
