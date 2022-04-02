#include <execution>
#include <iostream>
#include <string>
#include <vector>

#include <boost/program_options.hpp>
#include <swss/dbconnector.h>
#include <swss/sonicv2connector.h>

namespace po = boost::program_options;

static std::string nameSpace;
static std::string dbOrOperation;
const char* emptyStr = "";

void printUsage(const po::options_description &description)
{
    std::cout << "usage: sonic-db-cli [-h] [-s] [-n NAMESPACE] db_or_op [cmd ...]" << std::endl;
    std::cout << description << std::endl;
}

void printRedisReply(redisReply* reply)
{
    switch(reply->type)
    {
    case REDIS_REPLY_INTEGER:
        std::cout << reply->integer;
        break;
    case REDIS_REPLY_STRING:
    case REDIS_REPLY_ERROR:
    case REDIS_REPLY_STATUS:
    case REDIS_REPLY_NIL:
        std::cout << std::string(reply->str, reply->len);
        break;
    case REDIS_REPLY_ARRAY: 
        for (size_t i = 0; i < reply->elements; i++)
        {
            printRedisReply(reply->element[i]);
        }
        break;
    default:
        std::cerr << reply->type << std::endl;
        throw std::runtime_error("Unexpected reply type");
    }

    std::cout << std::endl;
}

int executeCommands(
    const std::string& dbName,
    std::vector<std::string>& commands,
    const std::string& nameSpace,
    bool useUnixSocket)
{
    std::unique_ptr<swss::SonicV2Connector_Native> dbconn;
    if (nameSpace.compare("None") == 0) {
        dbconn = std::make_unique<swss::SonicV2Connector_Native>(useUnixSocket, emptyStr);
    }
    else {
        dbconn = std::make_unique<swss::SonicV2Connector_Native>(true, nameSpace.c_str());
    }

    try {
        dbconn->connect(dbName);
    }
    catch (const std::exception& e)
    {
        std::cerr << "Invalid database name input : " << dbName << std::endl;
        return 1;
    }

    auto& client = dbconn->get_redis_client(dbName);

    size_t argc = commands.size();
    const char** argv = new const char*[argc];
    size_t* argvc = new size_t[argc];
    for (size_t i = 0; i < argc; i++)
    {
        argv[i] = strdup(commands[i].c_str());
        argvc[i] = commands[i].size();
    }

    swss::RedisCommand command;
    command.formatArgv(argc, argv, argvc);
    swss::RedisReply reply(&client, command);

    auto redisReply = reply.getContext();
    printRedisReply(redisReply);

    return 0;
}

void handleSingleOperation(
    const std::string& nameSpace,
    const std::string& dbName,
    const std::string& operation,
    bool useUnixSocket)
{
    swss::SonicV2Connector_Native conn(useUnixSocket, nameSpace.c_str());
    conn.connect(dbName);
    auto& client = conn.get_redis_client(dbName);
    
    swss::RedisReply reply(&client, operation);
    auto redisReply = reply.getContext();
    printRedisReply(redisReply);
}

void handleAllInstances(
    const std::string& nameSpace,
    const std::string& operation,
    bool useUnixSocket)
{
    // Use the tcp connectivity if namespace is local and unixsocket cmd_option is present.
    if (nameSpace.compare("None") == 0) {
        useUnixSocket = true;
    }
    
    auto dbNames = swss::SonicDBConfig::getDbList(nameSpace);
    // Operate All Redis Instances in Parallel
    // TODO: if one of the operations failed, it could fail quickly and not necessary to wait all other operations
    std::for_each(
        std::execution::par,
        dbNames.begin(),
        dbNames.end(),
        [=](auto&& dbName)
        {
            handleSingleOperation(nameSpace, dbName, operation, useUnixSocket);
        });
}

int handleOperation(const po::variables_map &variablesMap, const po::options_description &description)
{
    if (variablesMap.count("db_or_op")) {
        auto dbOrOperation = variablesMap["db_or_op"].as<std::string>();
        auto nameSpace = variablesMap["--namespace"].as<std::string>();
        bool useUnixSocket = variablesMap.count("--unixsocket");
        if (nameSpace.compare("None") != 0) {
            swss::SonicDBConfig::initializeGlobalConfig(nameSpace);
        }
        
        if (variablesMap.count("cmd")) {
            auto commands = variablesMap["cmd"].as< std::vector<std::string> >();
            return executeCommands(dbOrOperation, commands, nameSpace, useUnixSocket);
        }
        else if (nameSpace.compare("PING") == 0 || nameSpace.compare("SAVE") == 0 || nameSpace.compare("FLUSHALL") == 0) {
            // redis-cli doesn't depend on database_config.json which could raise some exceptions
            // sonic-db-cli catch all possible exceptions and handle it as a failure case which not return 'OK' or 'PONG'
            handleAllInstances(nameSpace, dbOrOperation, useUnixSocket);
        }
        else {
            printUsage(description);
        }
    }
    else {
        printUsage(description);
    }

    return 0;
}

void parseCliArguments(
    int argc,
    char** argv,
    po::options_description &description,
    po::variables_map &variablesMap)
{
    description.add_options()
        ("--help,-h", "Help message")
        ("--unixsocket,-s", "Override use of tcp_port and use unixsocket")
        ("--namespace,-n", po::value<std::string>(&nameSpace)->default_value("None"), "Namespace string to use asic0/asic1.../asicn")
        ("db_or_op", po::value<std::string>(&dbOrOperation)->default_value(emptyStr), "Database name Or Unary operation(only PING/SAVE/FLUSHALL supported)")
        ("cmd", po::value< std::vector<std::string> >(), "Command to execute in database")
    ;

    po::store(po::parse_command_line(argc, argv, description), variablesMap);
    po::notify(variablesMap);
}

int main(int argc, char** argv)
{
    po::options_description description("SONiC DB CLI");
    po::variables_map variablesMap;

    try {
        parseCliArguments(argc, argv, description, variablesMap);
    }
    catch (po::error_with_option_name& e) {
        std::cerr << "Command Line Syntax Error: " << e.what() << std::endl;
        printUsage(description);
        return -1;
    }
    catch (po::error& e) {
        std::cerr << "Command Line Error: " << e.what() << std::endl;
        printUsage(description);
        return -1;
    }

    if (variablesMap.count("--help")) {
        printUsage(description);
        return 0;
    }

    try
    {
        return handleOperation(variablesMap, description);
    }
    catch (const std::exception& e)
    {
        std::cerr << "An exception of type " << e.what() << " occurred. Arguments:" << std::endl;
        for (int idx = 0; idx < argc; idx++) {
            std::cerr << argv[idx]  << " ";
        }
        std::cerr << std::endl;
        return 1;
    }

    return 0;
}