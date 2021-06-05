#include "eventutils.h"
#include <swss/logger.h>
#include <swss/table.h>
#include <string.h>
#include <cstdlib>
#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <unistd.h>
#include <sys/stat.h>
#include <algorithm>
#include <string>
#include "json.h"
#include "json.hpp"

namespace evtutils {
using namespace std;
using namespace swss;
using namespace std::chrono;
using json = nlohmann::json;

bool isValidSeverity(string severityStr) {
    transform(severityStr.begin(), severityStr.end(), severityStr.begin(), ::toupper);
    if (severityStr == EVENT_SEVERITY_MAJOR_STR) return true;
    if (severityStr == EVENT_SEVERITY_CRITICAL_STR) return true;
    if (severityStr == EVENT_SEVERITY_MINOR_STR) return true;
    if (severityStr == EVENT_SEVERITY_WARNING_STR) return true;
    if (severityStr == EVENT_SEVERITY_INFORMATIONAL_STR) return true;
    return false;
}

bool isValidEnable(string enableStr) {
    if (enableStr == EVENT_ENABLE_TRUE_STR) return true;
    if (enableStr == EVENT_ENABLE_FALSE_STR) return true;
    return false;
}

bool parse_config(const char *filename, unsigned int& days, unsigned int& count) {
    days = EHT_MAX_DAYS;
    count = EHT_MAX_ELEMS;
    std::ifstream ifs(filename);
    json j = json::parse(ifs);
    for (json::iterator it = j.begin(); it != j.end(); ++it) {
        if(it.key() == "max-days") {
            days = it.value();
        }
        if(it.key() == "max-records") {
            count = it.value();
        }
    }
    return true;
}

bool parse(const char *filename, EventMap& tmp_event_table) {
    ifstream fs(filename);
    if (!fs.is_open()) {
        return false;
    }

    fstream file(filename, fstream::in);
    json j;
    file >> j;

    if (j["events"].size() == 0) {
        SWSS_LOG_ERROR("No entries in 'events' field in %s", filename);
        return false;
    }

    for (size_t i = 0; i < j["events"].size(); i++) {
        auto elem = j["events"][i];
        struct EventInfo_t ev_info;
        string ev_name = elem["name"];
        ev_info.severity = elem["severity"];
        ev_info.enable = elem["enable"];
        ev_info.static_event_msg = elem["message"];
        tmp_event_table.emplace(ev_name, ev_info);
    }

    return true;
}

void merge(EventMap& static_event_table, EventMap &profile_map) {
    for (auto it = profile_map.begin(); it != profile_map.end(); it++) {
        if (static_event_table.find(it->first) != static_event_table.end()) {
            //TODO: try copying individual parametrs
            static_event_table[it->first] = it->second;
        } else {
            static_event_table.emplace(it->first, it->second);
        }
    }
}

void create_symlink() {
    struct stat info;
    if (lstat(EVENTD_PROFILE_SYMLINK, &info) != 0) {
        if (symlink(EVENTD_DEFAULT_MAP_FILE, EVENTD_PROFILE_SYMLINK) != 0) {
            SWSS_LOG_ERROR("Error creating symlink to default profile");
        } else {
            SWSS_LOG_NOTICE("Created symlink to default profile");
        }
    } 
}

// timeticks are relative to the Unix Epoch 
string getTimeTicks() {
    const auto p1 = system_clock::now();
    return to_string(duration_cast<nanoseconds>(p1.time_since_epoch()).count());
}

}

