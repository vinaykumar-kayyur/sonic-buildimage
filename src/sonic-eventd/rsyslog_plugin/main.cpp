#include <iostream>
#include <memory>
#include <unistd.h>
#include "rsyslog_plugin.h"

#define SUCCESS_CODE 0
#define INVALID_REGEX_ERROR_CODE 1
#define EVENT_INIT_PUBLISH_ERROR_CODE 2
#define MISSING_ARGS_ERROR_CODE 3

void showUsage() {
    cout << "Usage for rsyslog_plugin: \n" << "options\n"
        << "\t-r,required,type=string\t\tList of all regex files that will be used and corresponding yang module./\n"
        << "\t-h                     \t\tHelp"
        << endl;
}

int main(int argc, char** argv) {
    string regexFilePath;
    int optionVal;

    while((optionVal = getopt(argc, argv, "r:m:h")) != -1) {
        switch(optionVal) {
            case 'r':
                regexFilePath = optarg;
                break;
            case 'h':
            case '?':
            default:
                showUsage();
                return 1;
        }
    }

    if(regexFilePath.empty()) { // Missing required path
        cerr << "Error: Missing regex file path" << endl;
        return MISSING_ARGS_ERROR_CODE;
    }

    // TODO: Expand onInit to use regex file to create buckets and for each bucket a regex list
    // TODO: Expand onMessage to first determine which bucket to use (bucket regex)
    // 5 buckets, 0 bgp, 1 swss, 2 dhcp_relay, 3 syncd, 4 host
    unique_ptr<RsyslogPlugin> plugin(new RsyslogPlugin(regexPath));
    int returnCode = plugin->onInit();
    // TODO: Might have to update this return code part too
    if(returnCode == INVALID_REGEX_ERROR_CODE) {
        SWSS_LOG_ERROR("Rsyslog plugin was not able to be initialized due to invalid regex file provided.\n");
        return returnCode;
    } else if(returnCode == EVENT_INIT_PUBLISH_ERROR_CODE) {
        SWSS_LOG_ERROR("Rsyslog plugin was not able to be initialized due to event_init_publish call failing.\n");
        return returnCode;
    }

    plugin->run();
    return SUCCESS_CODE;
}
