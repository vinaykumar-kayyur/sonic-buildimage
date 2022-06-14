#ifndef SYSLOG_PARSER_H
#define SYSLOG_PARSER_H

#include <vector>
#include <string>
#include <regex>
#include "common/json.hpp"
#include "common/events.h"

using namespace std;
using json = nlohmann::json;

/**
 * Syslog Parser is responsible for parsing log messages fed by rsyslog.d and returns
 * matched result to rsyslog_plugin to use with events publish API
 *
 */

class SyslogParser {
public:
    SyslogParser(vector<regex> regex_expressions, json list);
    bool parseMessage(string message, string& tag, event_params_t& param_dict);

    vector<regex> expressions;
    json regex_list = json::array();
};

#endif
