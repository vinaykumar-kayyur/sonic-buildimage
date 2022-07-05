#include <iostream>
#include "syslog_parser.h"
#include "common/logger.h"

/**
 * Parses syslog message and returns structured event
 *
 * @param nessage us syslog message being fed in by rsyslog.d
 * @return return structured event json for publishing
 *
*/

bool SyslogParser::parseMessage(string message, string& eventTag, event_params_t& paramMap) {
    for(long unsigned int i = 0; i < m_regexList.size(); i++) {
        smatch matchResults;
        vector<string> params = m_regexList[i]["params"];
        if(!regex_search(message, matchResults, m_expressions[i]) || params.size() != matchResults.size() - 1) {
            continue;
        }
        // found matching regex
        eventTag = m_regexList[i]["tag"];
        transform(params.begin(), params.end(), matchResults.begin() + 1, inserter(paramMap, paramMap.end()), [](string a, string b) {
            return make_pair(a,b);
        });
        return true;
    }
    return false;
}
