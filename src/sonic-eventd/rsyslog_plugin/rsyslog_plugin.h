#ifndef RSYSLOG_PLUGIN_H
#define RSYSLOG_PLUGIN_H

#include <string>
#include <fstream>
#include "syslog_parser.h"
#include "common/logger.h"
#include "common/events.h"

using namespace std;
using json = nlohmann::json;

/**
 * Rsyslog Plugin will utilize an instance of a syslog parser to read syslog messages from rsyslog.d and will continuously read from stdin
 * A plugin instance is created for each container/host.
 *
 */

class RsyslogPlugin {
public:
    RsyslogPlugin(SyslogParser* syslog_parser, string mod_name, string path);
    void onMessage(string msg);
    void run();
    bool createRegexList();
    event_handle_t fetchHandle() {
        return event_handle;
    }
    SyslogParser* parser;
private:
    string regex_path;
    string module_name;
    event_handle_t event_handle;

    bool onInit() {
        event_handle = events_init_publisher(module_name);
        int return_code = createRegexList();
	return (event_handle != NULL && return_code == 0); 
    }

};

#endif

