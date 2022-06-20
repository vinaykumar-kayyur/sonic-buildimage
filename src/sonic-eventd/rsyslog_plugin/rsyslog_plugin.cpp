#include <iostream>
#include <vector>
#include <fstream>
#include <regex>
#include "rsyslog_plugin.h"
#include "common/json.hpp"

using json = nlohmann::json;

bool RsyslogPlugin::onMessage(string msg) {
    string tag;
    event_params_t paramDict;
    if(!m_parser->parseMessage(msg, tag, paramDict)) {
        SWSS_LOG_DEBUG("%s was not able to be parsed into a structured event\n", msg.c_str());
        return false;
    } else {
        int returnCode = event_publish(m_eventHandle, tag, &paramDict);
        if (returnCode != 0) {
            SWSS_LOG_ERROR("rsyslog_plugin was not able to publish event for %s. last thrown event error: %d\n", tag.c_str(), event_last_error());
            return false;
        }
        return true;
    }
}

bool RsyslogPlugin::createRegexList() {
    fstream regexFile;
    regexFile.open(m_regexPath, ios::in);
    if (!regexFile) {
        SWSS_LOG_ERROR("No such path exists: %s for source %s\n", m_regexPath.c_str(), m_moduleName.c_str());
        return false;
    }
    try {
        regexFile >> m_parser->m_regexList;
    } catch (invalid_argument& iaException) {
        SWSS_LOG_ERROR("Invalid JSON file: %s, throws exception: %s\n", m_regexPath.c_str(), iaException.what());
        return false;
    }

    string regexString;
    regex expression;

    for(long unsigned int i = 0; i < m_parser->m_regexList.size(); i++) {
        try {
            regexString = m_parser->m_regexList[i]["regex"];
            string tag = m_parser->m_regexList[i]["tag"];
            vector<string> params = m_parser->m_regexList[i]["params"];
            regex expr(regexString);
            expression = expr;
        } catch (domain_error& deException) {
            SWSS_LOG_ERROR("Missing required key, throws exception: %s\n", deException.what());
            return false;
        } catch (regex_error& reException) {
            SWSS_LOG_ERROR("Invalid regex, throws exception: %s\n", reException.what());
	    return false;
	}
        m_parser->m_expressions.push_back(expression);
    }
    if(m_parser->m_expressions.empty()) {
        SWSS_LOG_ERROR("Empty list of regex expressions.\n");
        return false;
    }
    regexFile.close();
    return true;
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

int RsyslogPlugin::onInit() {
    m_eventHandle = events_init_publisher(m_moduleName);
    bool success = createRegexList();
    if(!success) {
        return 1; // invalid regex error code
    } else if(m_eventHandle == NULL) {
        return 2; // event init publish error code
    }
    return 0;
}

RsyslogPlugin::RsyslogPlugin(string moduleName, string regexPath) {
    m_parser = unique_ptr<SyslogParser>(new SyslogParser());
    m_moduleName = moduleName;
    m_regexPath = regexPath;
}
