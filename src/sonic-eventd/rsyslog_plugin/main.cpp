#include <iostream>
#include <unistd.h>
#include "rsyslog_plugin.h"
#include "syslog_parser.h"

using namespace std;

void showUsage() {
    cerr << "Usage for rsyslog_plugin: " << " <option(s)> SOURCES\n"
        << "Options:\n"
        << "\t-r,required,type=string\t\tPath to regex file"
        << "\t-m,required,type=string\t\tYANG module name of source generating syslog message"
        << endl;
}

int main(int argc, char** argv) {
    string regex_path;
    string module_name;
    int option_val;

    while((option_val = getopt(argc, argv, "r:m:")) != -1) {
        switch(option_val) {
            case 'r':
                if(optarg != NULL) {
                    regex_path = optarg;
                }
                break;
            case 'm':
                if(optarg != NULL) {
                    module_name = optarg;
                }
                break;
            default:
                showUsage();
                return 1;
        }
    }

    if(regex_path.empty() || module_name.empty()) { // Missing required rc path
        showUsage();
        return 1;
    }
    
    SyslogParser* parser = new SyslogParser({}, json::array());
    RsyslogPlugin* plugin = new RsyslogPlugin(parser, module_name, regex_path);

    plugin->run();
    return 0;
}
