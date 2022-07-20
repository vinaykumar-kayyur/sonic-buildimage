extern "C"
{
    #include <lua5.1/lua.h>
    #include <lua5.1/lualib.h>
    #include <lua5.1/lauxlib.h>
}
#include <iostream>
#include <fstream>
#include <regex>
#include "gtest/gtest.h"
#include "json.hpp"
#include "events.h"
#include "../rsyslog_plugin/rsyslog_plugin.h"
#include "../rsyslog_plugin/syslog_parser.h"
#include "../rsyslog_plugin/timestamp_formatter.h"

using namespace std;
using namespace swss;
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
    lua_State* luaState = luaL_newstate();
    luaL_openlibs(luaState);

    bool success = parser->parseMessage("timestamp test_timestamp message test_message other_data test_data", tag, paramDict, luaState);
    EXPECT_EQ(true, success);
    EXPECT_EQ("test_tag", tag);
    EXPECT_EQ(expectedDict, paramDict);
    
    lua_close(luaState);
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
    lua_State* luaState = luaL_newstate();
    luaL_openlibs(luaState);

    bool success = parser->parseMessage("Test Message", tag, paramDict, luaState);
    EXPECT_EQ(false, success);

    lua_close(luaState);
    delete parser;
}

TEST(syslog_parser, lua_code_valid_1) {
    json jList = json::array();
    vector<regex> testExpressions;
    string regexString = ".* (sent|received) (?:to|from) .* ([0-9]{2,3}.[0-9]{2,3}.[0-9]{2,3}.[0-9]{2,3}) active ([1-9]{1,3})/([1-9]{1,3}) .*";
    json jTest;
    jTest["tag"] = "test_tag";
    jTest["regex"] = regexString;
    jTest["params"] = { "is-sent:ret=tostring(arg==\"sent\")", "ip", "major-code", "minor-code" };
    jList.push_back(jTest);
    regex expression(regexString);
    testExpressions.push_back(expression);

    string tag;
    event_params_t paramDict;

    event_params_t expectedDict;
    expectedDict["is-sent"] = "true";
    expectedDict["ip"] = "100.95.147.229";
    expectedDict["major-code"] = "2";
    expectedDict["minor-code"] = "2";

    SyslogParser* parser = new SyslogParser();
    parser->m_expressions = testExpressions;
    parser->m_regexList = jList;
    lua_State* luaState = luaL_newstate();
    luaL_openlibs(luaState);

    bool success = parser->parseMessage("NOTIFICATION: sent to neighbor 100.95.147.229 active 2/2 (peer in wrong AS) 2 bytes", tag, paramDict, luaState);
    EXPECT_EQ(true, success);
    EXPECT_EQ("test_tag", tag);
    EXPECT_EQ(expectedDict, paramDict);
    
    lua_close(luaState);
    delete parser;
}

TEST(syslog_parser, lua_code_valid_2) {
    json jList = json::array();
    vector<regex> testExpressions;
    string regexString = ".* (sent|received) (?:to|from) .* ([0-9]{2,3}.[0-9]{2,3}.[0-9]{2,3}.[0-9]{2,3}) active ([1-9]{1,3})/([1-9]{1,3}) .*";
    json jTest;
    jTest["tag"] = "test_tag";
    jTest["regex"] = regexString;
    jTest["params"] = { "is-sent:ret=tostring(arg==\"sent\")", "ip", "major-code", "minor-code" };
    jList.push_back(jTest);
    regex expression(regexString);
    testExpressions.push_back(expression);

    string tag;
    event_params_t paramDict;

    event_params_t expectedDict;
    expectedDict["is-sent"] = "false";
    expectedDict["ip"] = "10.10.24.216";
    expectedDict["major-code"] = "6";
    expectedDict["minor-code"] = "2";

    SyslogParser* parser = new SyslogParser();
    parser->m_expressions = testExpressions;
    parser->m_regexList = jList;
    lua_State* luaState = luaL_newstate();
    luaL_openlibs(luaState);

    bool success = parser->parseMessage("NOTIFICATION: received from neighbor 10.10.24.216 active 6/2 (Administrative Shutdown) 0 bytes", tag, paramDict, luaState);
    EXPECT_EQ(true, success);
    EXPECT_EQ("test_tag", tag);
    EXPECT_EQ(expectedDict, paramDict);
    
    lua_close(luaState);
    delete parser;

}

RsyslogPlugin* createPlugin(string path) {
    RsyslogPlugin* plugin = new RsyslogPlugin("test_mod_name", path);
    return plugin;
}

TimestampFormatter* createFormatter() {
    const string timestampFormatRegex = "([a-zA-Z]{3}) ([0-9]{1,2}) ([0-9]{2}:[0-9]{2}:[0-9]{2}.[0-9]{0,6})";
    TimestampFormatter* formatter = new TimestampFormatter(timestampFormatRegex);
    return formatter;
}

TEST(rsyslog_plugin, onInit_invalidJS0N) {
    auto plugin = createPlugin("./rsyslog_plugin_tests/test_regex_1.rc.json");
    EXPECT_NE(0, plugin->onInit());
    delete plugin;
}

TEST(rsyslog_plugin, onInit_emptyJSON) {
    auto plugin = createPlugin("./rsyslog_plugin_tests/test_regex_6.rc.json");
    EXPECT_NE(0, plugin->onInit());
    delete plugin;
}

TEST(rsyslog_plugin, onInit_missingRegex) {
    auto plugin = createPlugin("./rsyslog_plugin_tests/test_regex_3.rc.json");
    EXPECT_NE(0, plugin->onInit());
    delete plugin;
}

TEST(rsyslog_plugin, onInit_invalidRegex) {
    auto plugin = createPlugin("./rsyslog_plugin_tests/test_regex_4.rc.json");
    EXPECT_NE(0, plugin->onInit());
    delete plugin;
}

TEST(rsyslog_plugin, onMessage) {
    auto plugin = createPlugin("./rsyslog_plugin_tests/test_regex_2.rc.json");
    EXPECT_EQ(0, plugin->onInit());

    ifstream infile("./rsyslog_plugin_tests/test_syslogs.txt");
    string logMessage;
    bool parseResult;
    lua_State* luaState = luaL_newstate();
    luaL_openlibs(luaState);
    while(infile >> logMessage >> parseResult) {
        EXPECT_EQ(parseResult, plugin->onMessage(logMessage, luaState));
    }
    lua_close(luaState);
    infile.close();
    delete plugin;
}

TEST(rsyslog_plugin, onMessage_noParams) {
    auto plugin = createPlugin("./rsyslog_plugin_tests/test_regex_5.rc.json");
    EXPECT_EQ(0, plugin->onInit());

    ifstream infile("./rsyslog_plugin_tests/test_syslogs_2.txt");
    string logMessage;
    bool parseResult;
    lua_State* luaState = luaL_newstate();
    luaL_openlibs(luaState);
    while(infile >> logMessage >> parseResult) {
        EXPECT_EQ(parseResult, plugin->onMessage(logMessage, luaState));
    }
    lua_close(luaState);
    infile.close();
    delete plugin;
}

TEST(timestampFormatter, changeTimestampFormat) {
    auto formatter = createFormatter();
    
    string timestampOne = "Jul 20 10:09:40.230874";
    string timestampTwo = "Jan 1 00:00:00.000000";
    string timestampThree = "Dec 31 23:59:59.000000"; 

    string formattedTimestampOne = formatter->changeTimestampFormat(timestampOne);
    EXPECT_EQ("2022-07-20T10:09:40.230874Z", formattedTimestampOne);

    EXPECT_EQ("072010:09:40.230874", formatter->m_storedTimestamp);

    string formattedTimestampTwo = formatter->changeTimestampFormat(timestampTwo);
    EXPECT_EQ("2022-01-01T00:00:00.000000Z", formattedTimestampTwo);

    formatter->m_storedTimestamp = "010100:00:00.000000";
    formatter->m_storedYear = "2025";

    string formattedTimestampThree = formatter->changeTimestampFormat(timestampThree);
    EXPECT_EQ("2025-12-31T23:59:59.000000Z", formattedTimestampThree);
}

int main(int argc, char* argv[]) {
    testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
