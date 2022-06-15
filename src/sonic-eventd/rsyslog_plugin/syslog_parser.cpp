#include <iostream>
#include <ios>
#include <fstream>
#include <regex>
#include "syslog_parser.h"
#include "common/logger.h"


using namespace std;
/**
 * Parses syslog message and returns structured event
 *
 * @param nessage us syslog message being fed in by rsyslog.d
 * @return return structured event json for publishing
 *
*/

bool SyslogParser::parseMessage(string message, string& event_tag, event_params_t& param_map) {
    for(long unsigned int i = 0; i < m_regex_list.size(); i++) {
        smatch match_results;
	vector<string> params = m_regex_list[i]["params"];
	if(!regex_search(message, match_results, m_expressions[i]) || params.size() != match_results.size() - 1) {
            continue;
	}
	// found matching regex
	event_tag = m_regex_list[i]["tag"];
        transform(params.begin(), params.end(), match_results.begin() + 1, inserter(param_map, param_map.end()), [](string a, string b) {
	    return make_pair(a,b);
	});
	return true;
    }
    return false;
}

SyslogParser::SyslogParser(vector<regex> expressions, json regex_list) {
    m_expressions = expressions;
    m_regex_list = regex_list;
}
