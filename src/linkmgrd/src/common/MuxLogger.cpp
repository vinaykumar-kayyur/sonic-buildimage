/*
 * MuxLogger.cpp
 *
 *  Created on: Oct 4, 2020
 *      Author: tamer
 */

#include <boost/log/attributes.hpp>
#include <boost/log/common.hpp>
#include <boost/log/core.hpp>
#include <boost/log/expressions.hpp>
#include <boost/log/sinks/syslog_backend.hpp>
#include <boost/log/utility/setup/file.hpp>
#include <boost/log/utility/setup/common_attributes.hpp>
#include <boost/log/utility/exception_handler.hpp>
#include <boost/filesystem.hpp>

#include "MuxException.h"
#include "MuxLogger.h"

namespace common
{

//
// ---> operator()(const boost::log::runtime_error &ex);
//
// handles runtime error exceptions
//
void MuxLoggerExceptionHandler::operator()(const boost::log::runtime_error &ex) const
{
    std::ostringstream errMsg;
    errMsg << "MUX Logger exception!!" << ". Exception details: " << ex.what();

    throw MUX_ERROR(MuxLogger, errMsg.str());
}

//
// ---> operator()(const std::exception &ex);
//
// handles std exceptions
//
void MuxLoggerExceptionHandler::operator()(const std::exception &ex) const
{
    std::ostringstream errMsg;
    errMsg << "MUX Logger exception!!" << ". Exception details: " << ex.what();

    throw MUX_ERROR(MuxLogger, errMsg.str());
}

//
// ---> getInstance();
//
// constructs MuxLogger singleton instance
//
MuxLoggerPtr MuxLogger::getInstance()
{
    static std::shared_ptr<MuxLogger> MuxLoggerPtr = nullptr;

    if (MuxLoggerPtr == nullptr) {
        MuxLoggerPtr = std::shared_ptr<MuxLogger> (new MuxLogger);
    }

    return MuxLoggerPtr;
}

//
// ---> initialize(std::string &prog,
//                 std::string &path,
//                 boost::log::trivial::severity_level level);
//
// initialize MUX logging class
//
void MuxLogger::initialize(
    std::string &prog,
    std::string &path,
    boost::log::trivial::severity_level level
)
{
    namespace trivial = boost::log::trivial;
    namespace keywords = boost::log::keywords;

    mLevel = level;

    boost::log::register_simple_formatter_factory<trivial::severity_level, char> ("Severity");
//    boost::filesystem::remove(path);

//    boost::log::add_file_log(
//        keywords::file_name = path,
//        keywords::format = "[%TimeStamp%] [%Severity%] %Message%"
//    );

    boost::log::core::get()->set_filter(trivial::severity >= level);

    boost::log::add_common_attributes();
    boost::log::core::get()->set_exception_handler(
        boost::log::make_exception_handler<boost::log::runtime_error, std::exception> (MuxLoggerExceptionHandler())
    );

    addSyslogSink(prog);
}

//
// ---> setLevel(const boost::log::trivial::severity_level level);
//
// set logger frontend and backend filter level
//
void MuxLogger::setLevel(const boost::log::trivial::severity_level level)
{
    namespace trivial = boost::log::trivial;

    mLevel = level;
    boost::log::core::get()->set_filter(trivial::severity >= level);
}

//
// ---> addSyslogSink(std::string &prog);
//
// Add syslog sink
//
void MuxLogger::addSyslogSink(std::string &prog)
{
    namespace sinks = boost::log::sinks;
    namespace expressions = boost::log::expressions;
    try {
        // Create a syslog sink
        boost::shared_ptr<sinks::synchronous_sink<sinks::syslog_backend>> sink(
            new sinks::synchronous_sink<sinks::syslog_backend> ()
        );

        sink->set_formatter(expressions::format(prog + ": %1%") % expressions::smessage);

        sink->locked_backend()->set_severity_mapper(
            sinks::syslog::direct_severity_mapping<int> ("Severity")
        );

        // Add the sink to the core
        boost::log::core::get()->add_sink(sink);
    }
    catch (std::exception& ex) {
        std::ostringstream errMsg;
        errMsg << "MUX Logger exception!!" << ". Exception details: " << ex.what();

        throw MUX_ERROR(MuxLogger, errMsg.str());
   }
}

} /* namespace common */
