#include "logger.h"

void run_eventd_service();

int main()
{
    SWSS_LOG_INFO("The eventd service started");

    run_eventd_service();

    SWSS_LOG_INFO("The eventd service exited");

    return 0;
}

