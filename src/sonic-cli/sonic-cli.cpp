#include <swss/sonicv2connector.h>

#include <getopt.h>
#include <unistd.h>

#include <iostream>
#include <string>
#include <vector>

static std::string nameSpace;
static std::string dbOrOperation;
static std::vector<std::string> commands;

static int useUnixSocket;
static int helpRequested;

void printUsage()
{
    std::cerr << "usage: sonic-db-cli [-h] [-s] [-n NAMESPACE] db_or_op [cmd ...]" << std::endl;
}

void parseCliArguments(int argc, char** argv)
{
    for (int index = 1; index < argc; index++)
    {
        std::string opt{argv[index]};
        if (opt == "-h" || opt == "--help")
        {
            helpRequested = true;
        }
        else if (opt == "-n" || opt == "--namespace")
        {
            index++;
            if (index == argc)
            {
                throw std::invalid_argument("namespace option requires argument");
            }
            nameSpace = argv[index];
        }
        else if (opt == "-s" || opt == "--unixsocket")
        {
            useUnixSocket = true;
        }
        else
        {
            if (dbOrOperation.empty())
            {
                dbOrOperation = argv[index];
            }
            else
            {
                commands.emplace_back(argv[index]);
            }
        }
    }
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

void executeCommands(const std::string& dbname, std::vector<std::string>& commands)
{
    swss::SonicV2Connector_Native conn(useUnixSocket, nameSpace.c_str());
    conn.connect(dbname);
    auto& client = conn.get_redis_client(dbname);
    
    swss::RedisCommand r;

    size_t argc = commands.size();
    const char** argv = new const char*[argc];
    size_t* argvc = new size_t[argc];

    for (size_t i = 0; i < argc; i++)
    {
        argv[i] = strdup(commands[i].c_str());
        argvc[i] = commands[i].size();
    }

    swss::RedisCommand c;
    c.formatArgv(argc, argv, argvc);
    swss::RedisReply reply(&client, c);

    auto redisReply = reply.getContext();
    printRedisReply(redisReply);
}

void handleSingleOperation(const std::string& ns, const std::string& operation)
{
    swss::SonicV2Connector_Native conn(useUnixSocket, ns.c_str());
    conn.connect("APPL_DB");
    auto& client = conn.get_redis_client("APPL_DB");
    
    swss::RedisReply reply(&client, operation);
    auto redisReply = reply.getContext();
    printRedisReply(redisReply);
}

void handleOperation()
{
    if (dbOrOperation == "PING" || dbOrOperation == "SAVE" || dbOrOperation == "FLUSHALL")
    {
        handleSingleOperation(nameSpace, dbOrOperation);
    }
    else if (!commands.empty())
    {
        executeCommands(dbOrOperation, commands);
    }
    else
    {
        throw std::runtime_error("Invalid operation");
    }
}

int main(int argc, char** argv)
{
    try
    {
        parseCliArguments(argc, argv);
        handleOperation();
    }
    catch (const std::exception& e)
    {
        std::cerr << e.what() << std::endl;
        return -1;
    }

    return 0;
}