#ifndef RSYSLOG_PLUGIN_H
#define RSYSLOG_PLUGIN_H

extern "C"
{
    #include <lua5.1/lua.h>
    #include <lua5.1/lualib.h>
    #include <lua5.1/lauxlib.h>
}
#include <string>
#include <memory>
#include <csignal>
#include <unordered_map>
#include "syslog_parser.h"
#include "events.h"
#include "logger.h"

using namespace std;
using namespace swss;

/**
 * Rsyslog Plugin will utilize an instance of a syslog parser to read syslog messages from rsyslog.d and will continuously read from stdin
 * A plugin instance is created for each container/host.
 *
 */

class RsyslogPlugin {
public:
    static bool g_running;
    int onInit();
    bool onMessage(string msg, lua_State* luaState);
    void run();
    RsyslogPlugin(string regexPath);
    static void signalHandler(int signum) {
        if (signum == SIGTERM) {
            SWSS_LOG_INFO("Rsyslog plugin received SIGTERM, shutting down");
            RsyslogPlugin::g_running = false;
        }
    }
private:
    unordered_map<string, pair<event_handle_t, unique_ptr<SyslogParser>>> m_event_buckets;
    string m_regexPath;
    bool createEventBuckets();
};

#endif

