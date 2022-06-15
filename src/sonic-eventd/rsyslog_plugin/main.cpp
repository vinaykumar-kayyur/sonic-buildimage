#include <iostream>
#include <unistd.h>
#include "rsyslog_plugin.h"

void showUsage() {
    cout << "Usage for rsyslog_plugin: \n" << "options\n"
        << "\t-r,required,type=string\t\tPath to regex file\n"
        << "\t-m,required,type=string\t\tYANG module name of source generating syslog message\n"
        << "\t-h                     \t\tHelp"
        << endl;
}

int main(int argc, char** argv) {
    string regex_path;
    string module_name;
    int option_val;

    while((option_val = getopt(argc, argv, "r:m:h")) != -1) {
        switch(option_val) {
            case 'r':
                regex_path = optarg;
                break;
            case 'm':
                module_name = optarg;
                break;
            case 'h':
            case '?':
            default:
                showUsage();
                return 1;
        }
    }

    if(regex_path.empty() || module_name.empty()) { // Missing required rc path
        cerr << "Error: Missing regex_path and module_name." << endl;
        return 1;
    }
    
    RsyslogPlugin* plugin = new RsyslogPlugin(module_name, regex_path);
    if(!plugin->onInit()) {
        SWSS_LOG_ERROR("Rsyslog plugin was not able to be initialized.\n");
	return 1;
    }

    plugin->run();
    return 0;
}
