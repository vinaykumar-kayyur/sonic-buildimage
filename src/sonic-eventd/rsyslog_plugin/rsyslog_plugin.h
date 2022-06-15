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
    bool onInit();
    bool onMessage(string msg);
    void run();
    RsyslogPlugin(string module_name, string regex_path);
private:
    SyslogParser* m_parser;
    event_handle_t m_event_handle;
    string m_regex_path;
    string m_module_name;

    bool createRegexList();
};

#endif

