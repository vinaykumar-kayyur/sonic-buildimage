#ifndef RSYSLOG_PLUGIN_H
#define RSYSLOG_PLUGIN_H

#include <string>
#include <memory>
#include "syslog_parser.h"
#include "common/events.h"
#include "common/logger.h"

using namespace std;
using namespace swss;

/**
 * Rsyslog Plugin will utilize an instance of a syslog parser to read syslog messages from rsyslog.d and will continuously read from stdin
 * A plugin instance is created for each container/host.
 *
 */

class RsyslogPlugin {
public:
    int onInit();
    bool onMessage(string msg);
    void run();
    RsyslogPlugin(string moduleName, string regexPath);
private:
    unique_ptr<SyslogParser> m_parser;
    event_handle_t m_eventHandle;
    string m_regexPath;
    string m_moduleName;
    bool createRegexList();
};

#endif

