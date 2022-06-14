#include <ios>
#include <iostream>
#include <vector>
#include <fstream>
#include <regex>
#include "rsyslog_plugin.h"
#include "common/logger.h"
#include "common/json.hpp"
#include "common/events.h"

using namespace std;
using namespace swss;
using json = nlohmann::json;

void RsyslogPlugin::onMessage(string msg) {
    string tag = "";
    event_params_t param_dict;
    if(!parser->parseMessage(msg, tag, param_dict)) {
        SWSS_LOG_INFO("%s was not able to be parsed into a structured event\n", msg.c_str());
    } else {
	int return_code = event_publish(fetchHandle(), tag, &param_dict);
	if (return_code != 0) {
            SWSS_LOG_INFO("rsyslog_plugin was not able to publish event for %s\n", tag.c_str());
	}
    }
}

[[noreturn]] void RsyslogPlugin::run() {
    while(true) {
        string line;
        getline(cin, line);
        if(line.empty()) {
            continue;
        }
        onMessage(line);
    }
}

bool RsyslogPlugin::createRegexList() {
    fstream regex_file;
    regex_file.open(regex_path, ios::in);
    if (!regex_file) {
        SWSS_LOG_ERROR("No such path exists: %s for source %s\n", regex_path.c_str(), module_name.c_str());
        return false;
    }
    try {
        regex_file >> parser->regex_list;
    } catch (exception& exception) {
        SWSS_LOG_ERROR("Invalid JSON file: %s, throws exception: %s\n", regex_path.c_str(), exception.what());
        return false;
    }

    string regex_string = "";
    regex expression;

    for(long unsigned int i = 0; i < parser->regex_list.size(); i++) {
        try {
            regex_string = parser->regex_list[i]["regex"];
            regex expr(regex_string);
            expression = expr;
        } catch (exception& exception) {
            SWSS_LOG_ERROR("Invalid regex, throws exception: %s\n", exception.what());
            return false;
        }
        parser->expressions.push_back(expression);
    }
    regex_file.close();
    return true;
}


RsyslogPlugin::RsyslogPlugin(SyslogParser* syslog_parser, string mod_name, string path) {
    parser = syslog_parser;
    module_name = mod_name;
    regex_path = path;
    if(!onInit()) {
        SWSS_LOG_ERROR("Initializing rsyslog plugin failed.\n");
    }
}
