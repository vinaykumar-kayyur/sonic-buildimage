#include <ios>
#include <iostream>
#include <vector>
#include <fstream>
#include <regex>
#include "rsyslog_plugin.h"
#include "common/logger.h"
#include "common/json.hpp"

using namespace std;
using namespace swss;
using json = nlohmann::json;

bool RsyslogPlugin::onMessage(string msg) {
    string tag;
    event_params_t param_dict;
    if(!m_parser->parseMessage(msg, tag, param_dict)) {
        SWSS_LOG_DEBUG("%s was not able to be parsed into a structured event\n", msg.c_str());
	return false;
    } else {
        int return_code = event_publish(m_event_handle, tag, &param_dict);
        if (return_code != 0) {
            SWSS_LOG_ERROR("rsyslog_plugin was not able to publish event for %s. last thrown event error: %d\n", tag.c_str(), event_last_error());
	    return false;
        }
	return true;
    }
}

bool RsyslogPlugin::createRegexList() {
    fstream regex_file;
    regex_file.open(m_regex_path, ios::in);
    if (!regex_file) {
        SWSS_LOG_ERROR("No such path exists: %s for source %s\n", m_regex_path.c_str(), m_module_name.c_str());
        return false;
    }
    try {
        regex_file >> m_parser->m_regex_list;
    } catch (exception& exception) {
        SWSS_LOG_ERROR("Invalid JSON file: %s, throws exception: %s\n", m_regex_path.c_str(), exception.what());
        return false;
    }

    string regex_string;
    regex expression;

    for(long unsigned int i = 0; i < m_parser->m_regex_list.size(); i++) {
        try {
            regex_string = m_parser->m_regex_list[i]["regex"];
	    string tag = m_parser->m_regex_list[i]["tag"];
	    vector<string> params = m_parser->m_regex_list[i]["params"];
            regex expr(regex_string);
            expression = expr;
        } catch (exception& exception) {
            SWSS_LOG_ERROR("Invalid regex, throws exception: %s\n", exception.what());
            return false;
        }
        m_parser->m_expressions.push_back(expression);
    }
    regex_file.close();
    return true;
}

[[noreturn]] void RsyslogPlugin::run() {
    while(true) {
        string line;
        getline(cin, line);
        if(line.empty()) {
            continue;
        }
        if(!onMessage(line)) {
            SWSS_LOG_DEBUG("RsyslogPlugin was not able to parse or publish the log message: %s\n", line.c_str());
	}
    }
}

bool RsyslogPlugin::onInit() {
    m_event_handle = events_init_publisher(m_module_name);
    bool return_code = createRegexList();
    return (m_event_handle != NULL && return_code);
}

RsyslogPlugin::RsyslogPlugin(string module_name, string regex_path) {
    m_parser = new SyslogParser({}, json::array());
    m_module_name = module_name;
    m_regex_path = regex_path;
}
