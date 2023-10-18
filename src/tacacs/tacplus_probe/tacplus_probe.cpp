#include <string>
#include <iostream>
#include <chrono>

// Tacacs+ lib
extern "C" {
#include <libtac/libtac.h>
#include <libtac/support.h>
}

// swsscommon lib
#include <swss/table.h>

using namespace std;
using namespace std::chrono;
using namespace swss;

// Config file path
const char *tacacs_config_file = "/etc/tacplus_nss.conf";

// Counter DB table name
#define COUNTERS_TACPLUS_SERVER_LATENCY             "TACPLUS_SERVER_LATENCY"
#define LATENCY_ATTRIBUTE_NAME                      "latency"

int main(int argc, char** argv)
{
    int tacacs_ctrl = parse_config_file(tacacs_config_file);

    if (tac_srv_no == 0)
    {
        cout << "No TACACS server found in:" << tacacs_config_file << endl;
    }

    
    auto counter_db = make_unique<DBConnector>("COUNTER_DB", 0);
    auto tacacs_counter_table = make_unique<Table>(counter_db.get(), COUNTERS_TACPLUS_SERVER_LATENCY);

    for(int server_idx = 0; server_idx < tac_srv_no; server_idx++)
    {
        vector<FieldValueTuple> fieldValues;
        string server = tac_ntop(tac_srv[server_idx].addr->ai_addr);
        long long start = duration_cast<milliseconds>(system_clock::now().time_since_epoch()).count();
        int server_fd = tac_connect_single(tac_srv[server_idx].addr, tac_srv[server_idx].key, tac_source_addr, tac_timeout, __vrfname);
        
        cout << "server:" << server << " ";
        if(server_fd < 0)
        {
            // tacacs server unreachable
            cout << "unreachable" << endl;
            fieldValues.emplace_back(LATENCY_ATTRIBUTE_NAME, std::to_string(-1));
        }
        else
        {
            // use connection setup latency as server latency
            long long latency = duration_cast<milliseconds>(system_clock::now().time_since_epoch()).count() - start;
            close(server_fd);

            cout << "latency:" << latency << "ms" << endl;
            fieldValues.emplace_back(LATENCY_ATTRIBUTE_NAME, std::to_string(latency));
        }

        tacacs_counter_table->set(server, fieldValues);
    }
}