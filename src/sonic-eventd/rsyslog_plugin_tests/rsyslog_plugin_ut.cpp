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

TEST(syslog_parser, matching_regex) {
    json j_list = json::array();
    vector<regex> test_expressions;
    string regex_string = "timestamp (.*) message (.*) other_data (.*)";
    json j_test;
    j_test["tag"] = "test_tag";
    j_test["regex"] = regex_string;
    j_test["params"] = { "timestamp", "message", "other_data" };
    j_list.push_back(j_test);
    regex expression(regex_string);
    test_expressions.push_back(expression);

    string tag;
    event_params_t param_dict;

    event_params_t expected_dict;
    expected_dict["timestamp"] = "test_timestamp";
    expected_dict["message"] = "test_message";
    expected_dict["other_data"] = "test_data";

    SyslogParser* parser = new SyslogParser(test_expressions, j_list);

    bool success = parser->parseMessage("timestamp test_timestamp message test_message other_data test_data", tag, param_dict);
    EXPECT_EQ(true, success);
    EXPECT_EQ("test_tag", tag);
    EXPECT_EQ(expected_dict, param_dict);

    delete parser;
}

TEST(syslog_parser, no_matching_regex) {
    json j_list = json::array();
    vector<regex> test_expressions;
    string regex_string = "no match";
    json j_test;
    j_test["tag"] = "test_tag";
    j_test["regex"] = regex_string;
    j_test["params"] = vector<string>();
    j_list.push_back(j_test);
    regex expression(regex_string);
    test_expressions.push_back(expression);

    string tag;
    event_params_t param_dict;
    SyslogParser* parser = new SyslogParser(test_expressions, j_list);
    bool success = parser->parseMessage("Test Message", tag, param_dict);
    EXPECT_EQ(false, success);
    delete parser;
}


RsyslogPlugin* createPlugin(string path) {
    RsyslogPlugin* plugin = new RsyslogPlugin("test_mod_name", path);
    return plugin;
}

TEST(rsyslog_plugin, onInit_invalidJS0N) {
    auto plugin = createPlugin("./test_regex_1.rc.json");
    EXPECT_EQ(false, plugin->onInit());
    delete plugin;
}

TEST(rsyslog_plugin, onInit_emptyJSON) {
    auto plugin = createPlugin("./test_regex_6.rc.json");
    EXPECT_EQ(false, plugin->onInit());
    delete plugin;
}

TEST(rsyslog_plugin, onInit_missingRegex) {
    auto plugin = createPlugin("./test_regex_3.rc.json");
    EXPECT_EQ(false, plugin->onInit());
    delete plugin;
}

TEST(rsyslog_plugin, onInit_invalidRegex) {
    auto plugin = createPlugin("./test_regex_4.rc.json");
    EXPECT_EQ(false, plugin->onInit());
    delete plugin;
}

TEST(rsyslog_plugin, onMessage) {
    auto plugin = createPlugin("./test_regex_2.rc.json");
    EXPECT_EQ(true, plugin->onInit());

    ifstream infile("test_syslogs.txt");
    string log_message;
    bool parse_result;
    while(infile >> log_message >> parse_result) {
	EXPECT_EQ(parse_result, plugin->onMessage(log_message));
    }
    infile.close();
    delete plugin;
}

TEST(rsyslog_plugin, onMessage_noParams) {
    auto plugin = createPlugin("./test_regex_5.rc.json");
    EXPECT_EQ(true, plugin->onInit());

    ifstream infile("test_syslogs_2.txt");
    string log_message;
    bool parse_result;
    while(infile >> log_message >> parse_result) {
        EXPECT_EQ(parse_result, plugin->onMessage(log_message));
    }
    infile.close();
    delete plugin;
}

int main(int argc, char* argv[]) {
    testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
