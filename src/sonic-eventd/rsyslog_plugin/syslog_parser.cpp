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
    for(long unsigned int i = 0; i < regex_list.size(); i++) {
        smatch match_results;
	regex_search(message, match_results, expressions[i]);
	vector<string> groups;
	vector<string> params;
	try {
	    event_tag = regex_list[i]["tag"];
	    vector<string> p = regex_list[i]["params"];
	    params = p;
	} catch (exception& exception) {
	    SWSS_LOG_ERROR("Invalid regex list, throws exception: %s\n", exception.what());
	    return false;
	}
	// first match in groups is entire message
	for(long unsigned int j = 1; j < match_results.size(); j++) {
	    groups.push_back(match_results.str(j));
	}
	if (groups.size() == params.size()) { // found matching regex
            transform(params.begin(), params.end(), groups.begin(), inserter(param_map, param_map.end()), [](string a, string b) {
	        return make_pair(a,b);
	    });
	    return true;
	}
    }
    return false;
}

SyslogParser::SyslogParser(vector<regex> regex_expressions, json list) {
    expressions = regex_expressions;
    regex_list = list;
}
