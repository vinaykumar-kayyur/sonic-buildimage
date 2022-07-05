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
    json jList = json::array();
    vector<regex> testExpressions;
    string regexString = "timestamp (.*) message (.*) other_data (.*)";
    json jTest;
    jTest["tag"] = "test_tag";
    jTest["regex"] = regexString;
    jTest["params"] = { "timestamp", "message", "other_data" };
    jList.push_back(jTest);
    regex expression(regexString);
    testExpressions.push_back(expression);

    string tag;
    event_params_t paramDict;

    event_params_t expectedDict;
    expectedDict["timestamp"] = "test_timestamp";
    expectedDict["message"] = "test_message";
    expectedDict["other_data"] = "test_data";

    SyslogParser* parser = new SyslogParser();
    parser->m_expressions = testExpressions;
    parser->m_regexList = jList;

    bool success = parser->parseMessage("timestamp test_timestamp message test_message other_data test_data", tag, paramDict);
    EXPECT_EQ(true, success);
    EXPECT_EQ("test_tag", tag);
    EXPECT_EQ(expectedDict, paramDict);

    delete parser;
}

TEST(syslog_parser, no_matching_regex) {
    json jList = json::array();
    vector<regex> testExpressions;
    string regexString = "no match";
    json jTest;
    jTest["tag"] = "test_tag";
    jTest["regex"] = regexString;
    jTest["params"] = vector<string>();
    jList.push_back(jTest);
    regex expression(regexString);
    testExpressions.push_back(expression);

    string tag;
    event_params_t paramDict;

    SyslogParser* parser = new SyslogParser();
    parser->m_expressions = testExpressions;
    parser->m_regexList = jList;

    bool success = parser->parseMessage("Test Message", tag, paramDict);
    EXPECT_EQ(false, success);
    delete parser;
}


RsyslogPlugin* createPlugin(string path) {
    RsyslogPlugin* plugin = new RsyslogPlugin("test_mod_name", path);
    return plugin;
}

TEST(rsyslog_plugin, onInit_invalidJS0N) {
    auto plugin = createPlugin("./test_regex_1.rc.json");
    EXPECT_NE(0, plugin->onInit());
    delete plugin;
}

TEST(rsyslog_plugin, onInit_emptyJSON) {
    auto plugin = createPlugin("./test_regex_6.rc.json");
    EXPECT_NE(0, plugin->onInit());
    delete plugin;
}

TEST(rsyslog_plugin, onInit_missingRegex) {
    auto plugin = createPlugin("./test_regex_3.rc.json");
    EXPECT_NE(0, plugin->onInit());
    delete plugin;
}

TEST(rsyslog_plugin, onInit_invalidRegex) {
    auto plugin = createPlugin("./test_regex_4.rc.json");
    EXPECT_NE(0, plugin->onInit());
    delete plugin;
}

TEST(rsyslog_plugin, onMessage) {
    auto plugin = createPlugin("./test_regex_2.rc.json");
    EXPECT_EQ(0, plugin->onInit());

    ifstream infile("test_syslogs.txt");
    string logMessage;
    bool parseResult;
    while(infile >> logMessage >> parseResult) {
        EXPECT_EQ(parseResult, plugin->onMessage(logMessage));
    }
    infile.close();
    delete plugin;
}

TEST(rsyslog_plugin, onMessage_noParams) {
    auto plugin = createPlugin("./test_regex_5.rc.json");
    EXPECT_EQ(0, plugin->onInit());

    ifstream infile("test_syslogs_2.txt");
    string logMessage;
    bool parseResult;
    while(infile >> logMessage >> parseResult) {
        EXPECT_EQ(parseResult, plugin->onMessage(logMessage));
    }
    infile.close();
    delete plugin;
}

int main(int argc, char* argv[]) {
    testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
