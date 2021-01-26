/*
 * MuxException.h
 *
 *  Created on: Oct 4, 2020
 *      Author: tamer
 */

#ifndef MUXEXCEPTION_H_
#define MUXEXCEPTION_H_

#include <exception>
#include <string>

/**
 * A macro for generating an MuxException with file path and line number.
 */
#define MUX_ERROR(name, msg)    common::name##Exception(msg, __FILE__, __LINE__)

namespace common
{

class MuxException : public std::exception {
public:
    MuxException(
        std::string excStr,
        const char *excFile,
        unsigned int excLine
    ) noexcept
    {
        #pragma GCC diagnostic push
        #pragma GCC diagnostic ignored "-Wterminate"
        throw std::string(excFile) + ":" + std::to_string(excLine) + ": " + excStr;
        #pragma GCC diagnostic pop
    };

    virtual ~MuxException () noexcept {};
};

/**
* Exception for Runtime Expression
*
* This is thrown when a runtime exception is detected
*/
class RunTimeErrorException : public MuxException {
public:
    using MuxException::MuxException;

    virtual ~RunTimeErrorException () noexcept {};
};

/**
* Exception for receiving invalid arguments.
*
* This is thrown when invalid arguments are received
*/
class InvalidArgsException : public RunTimeErrorException {
public:
    using RunTimeErrorException::RunTimeErrorException;

    virtual ~InvalidArgsException () noexcept {};
};

/**
* Exception for MUX Logger
*
* This is thrown when boost logger report exceptions
*/
class MuxLoggerException : public RunTimeErrorException {
public:
    using RunTimeErrorException::RunTimeErrorException;

    virtual ~MuxLoggerException () noexcept {};
};

/**
* Exception for Bad Memory Alloc
*
* This is thrown when failing to allocated memory
*/
class BadAllocException : public RunTimeErrorException {
public:
    using RunTimeErrorException::RunTimeErrorException;

    virtual ~BadAllocException () noexcept {};
};

/**
* Exception for Socket Errors
*
* This is thrown when socket operation fails
*/
class SocketErrorException : public RunTimeErrorException {
public:
    using RunTimeErrorException::RunTimeErrorException;

    virtual ~SocketErrorException () noexcept {};
};

/**
* Exception for File Not Found
*
* This is thrown when unsupported platform is detected
*/
class FileNotFoundException : public RunTimeErrorException {
public:
    using RunTimeErrorException::RunTimeErrorException;

    virtual ~FileNotFoundException () noexcept {};
};

/**
* Exception for Internal Error
*
* This is thrown when unexpected behavior is detected. This should never happen.
*/
class InternalErrorException : public MuxException {
public:
    using MuxException::MuxException;

    virtual ~InternalErrorException () noexcept {};
};

/**
* Exception for IO Error
*
* This is thrown when failing to read signal list file.
*/
class IOErrorException : public MuxException {
public:
    using MuxException::MuxException;

    virtual ~IOErrorException () noexcept {};
};

} /* namespace common */

#endif /* MUXEXCEPTION_H_ */
