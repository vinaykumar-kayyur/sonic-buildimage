#ifndef TIMESTAMP_FORMATTER_H
#define TIMESTAMP_FORMATTER_H
#include <iostream>
#include <string>
#include <regex>
#include <ctime>

/***
 *
 * TimestampFormatter is responsible for formatting the timestamps received in syslog messages and to format them into the type needed by YANG model
 *
 */

class TimestampFormatter {
public:
    std::string changeTimestampFormat(std::string message);
    TimestampFormatter(std::string timestampFormatRegex);
    std::string m_storedTimestamp;
    std::string m_storedYear;
private:
    std::regex m_expression;
    std::string getYear(std::string timestamp);
};

#endif
