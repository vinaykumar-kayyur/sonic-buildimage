#include <iostream>
#include <fstream>
#include <regex>
#include "gtest/gtest.h"
#include "common/json.hpp"
#include "common/events.h"
#include "rsyslog_plugin/rsyslog_plugin.h"
#include "rsyslog_plugin/syslog_parser.h"

using namespace std;
using json = nlohmann::json;

RsyslogPlugin* plugin = NULL;

json j_list_1 = json::array();
json j_list_2 = json::array();
vector<regex> test_expressions_1;
vector<regex> test_expressions_2;

void createTests() {
    string regex_string_1 = "timestamp (.*) message (.*) other_data (.*)";
    string regex_string_2 = "no match";

    json j_test_1;
    j_test_1["tag"] = "test_tag_1";
    j_test_1["regex"] = regex_string_1;
    j_test_1["params"] = { "timestamp", "message", "other_data" };
    j_list_1.push_back(j_test_1);

    json j_test_2;
    j_test_2["tag"] = "test_tag_2";
    j_test_2["regex"] = regex_string_2;
    j_test_2["params"] = {};
    j_list_2.push_back(j_test_2);

    regex expression_1(regex_string_1);
    test_expressions_1.push_back(expression_1);
    regex expression_2(regex_string_2);
    test_expressions_2.push_back(expression_2);
}


TEST(syslog_parser, matching_regex) {
    createTests();
    string tag = "";
    event_params_t param_dict;

    event_params_t expected_dict;
    expected_dict["timestamp"] = "test_timestamp";
    expected_dict["message"] = "test_message";
    expected_dict["other_data"] = "test_data";

    SyslogParser* parser = new SyslogParser(test_expressions_1, j_list_1);

    bool success = parser->parseMessage("timestamp test_timestamp message test_message other_data test_data", tag, param_dict);
    EXPECT_EQ(true, success);
    EXPECT_EQ("test_tag_1", tag);
    EXPECT_EQ(expected_dict, param_dict);

    delete parser;
}

TEST(syslog_parser, no_matching_regex) {
    string tag = "";
    event_params_t param_dict;
    SyslogParser* parser = new SyslogParser(test_expressions_2, j_list_2);
    bool success = parser->parseMessage("Test Message", tag, param_dict);
    EXPECT_EQ(false, success);
    delete parser;
}


void createPlugin(string path) {
    SyslogParser* testParser = new SyslogParser({}, json::array());
    plugin = new RsyslogPlugin(testParser, "test_mod_name", path);
}

TEST(rsyslog_plugin, createRegexList_invalidJS0N) {
    createPlugin("./test_regex_1.rc.json");
    if(plugin != NULL) {
        EXPECT_EQ(false, plugin->createRegexList());
    }
    delete plugin;
}

TEST(rsyslog_plugin, createRegexList_missingRegex) {
    createPlugin("./test_regex_3.rc.json");
    if(plugin != NULL) {
	EXPECT_EQ(false, plugin->createRegexList());
    }
    delete plugin;
}

TEST(rsyslog_plugin, createRegexList_invalidRegex) {
    createPlugin("./test_regex_4.rc.json");
    if(plugin != NULL) {
	EXPECT_EQ(false, plugin->createRegexList());
    }
    delete plugin;
}

TEST(rsyslog_plugin, createRegexList_validRegex) {
    createPlugin("./test_regex_2.rc.json");
    if(plugin != NULL) {
	auto parser = plugin->parser;
	EXPECT_EQ(1, parser->regex_list.size());
	EXPECT_EQ(1, parser->expressions.size());

	ifstream infile("test_syslogs.txt");
	string log_message;
	bool parse_result;

	while(infile >> log_message >> parse_result) {
	    string tag = "";
	    event_params_t param_dict;
	    EXPECT_EQ(parse_result, parser->parseMessage(log_message, tag, param_dict));
	}
    }
    delete plugin;
}

int main(int argc, char* argv[]) {
    testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
