#include <iostream>
#include <ctime>
#include "syslog_parser.h"
#include "logger.h"

/**
 * Parses syslog message and returns structured event
 *
 * @param nessage us syslog message being fed in by rsyslog.d
 * @return return structured event json for publishing
 *
*/

void SyslogParser::addTimestamp(string message, event_params_t& paramMap) {
    string formattedTimestamp = m_timestampFormatter->changeTimestampFormat(message);
    if(formattedTimestamp.empty()) {
        SWSS_LOG_ERROR("Message does not contain valid timestamp and cannot be formatted: %s.\n", message.c_str());
	return;
    }
    paramMap["timestamp"] = formattedTimestamp;
}

bool SyslogParser::parseMessage(string message, string& eventTag, event_params_t& paramMap, lua_State* luaState) {
    for(long unsigned int i = 0; i < m_regexList.size(); i++) {
        smatch matchResults;
        vector<string> params = m_regexList[i]["params"];
        if(!regex_search(message, matchResults, m_expressions[i]) || params.size() != matchResults.size() - 1) {
            continue;
        }
        // found matching regex
        eventTag = m_regexList[i]["tag"];
	// check params for lua code
	for(long unsigned int j = 0; j < params.size(); j++) {
            auto delimPos = params[j].find(':');
	    string resultValue = matchResults[j + 1].str();
	    if(delimPos == string::npos) { // no lua code
		paramMap[params[j]] = resultValue;
		continue;
	    }
            // have to execute lua script
            string param = params[j].substr(0, delimPos);
            string luaString = params[j].substr(delimPos + 1); 
	    if(luaString.empty()) { // empty lua code
                SWSS_LOG_INFO("Lua code missing after :, skipping operation");
                paramMap[param] = resultValue;
                continue; 
	    }
            const char* luaCode = luaString.c_str();
            lua_pushstring(luaState, resultValue.c_str());
            lua_setglobal(luaState, "arg");
            if(luaL_dostring(luaState, luaCode) == 0) {
                lua_pop(luaState, lua_gettop(luaState));
	    } else {
		SWSS_LOG_ERROR("Invalid lua code, unable to do operation.\n");
		paramMap[param] = resultValue;
		continue;
            }
            lua_getglobal(luaState, "ret");
            paramMap[param] = lua_tostring(luaState, -1);
            lua_pop(luaState, 1);
	}
	addTimestamp(message, paramMap);
        return true;
    }
    return false;
}

SyslogParser::SyslogParser() {
    string timestampFormatRegex = "([a-zA-Z]{3}) ([0-9]{1,2}) ([0-9]{2}:[0-9]{2}:[0-9]{2}.[0-9]{0,6}).*";
    m_timestampFormatter = unique_ptr<TimestampFormatter>(new TimestampFormatter(timestampFormatRegex));
}
