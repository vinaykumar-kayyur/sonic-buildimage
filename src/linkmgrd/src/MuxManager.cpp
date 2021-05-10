/*
 * MuxManager.cpp
 *
 *  Created on: Oct 4, 2020
 *      Author: tamer
 */
#include <ctype.h>
#include <iostream>
#include <string>
#include <net/ethernet.h>

#include <boost/bind/bind.hpp>

#include "common/MuxException.h"
#include "common/MuxLogger.h"
#include "MuxManager.h"

namespace mux
{
//
// ---> MuxManager();
//
// class constructor
//
MuxManager::MuxManager() :
    mMuxConfig(),
    mWork(mIoService),
    mSignalSet(boost::asio::signal_set(mIoService, SIGINT, SIGTERM)),
    mDbInterface(this, &mIoService)
{
    mSignalSet.add(SIGUSR1);
    mSignalSet.add(SIGUSR2);
    mSignalSet.async_wait(boost::bind(&MuxManager::handleSignal,
        this,
        boost::asio::placeholders::error,
        boost::asio::placeholders::signal_number
    ));
}

//
// ---> initialize();
//
// initialize MuxManager class and creates DbInterface instance that reads/listen from/to Redis db
//
void MuxManager::initialize()
{
    for (uint8_t i = 0; (mMuxConfig.getNumberOfThreads() > 2) &&
                        (i < mMuxConfig.getNumberOfThreads() - 2); i++) {
        mThreadGroup.create_thread(
            boost::bind(&boost::asio::io_service::run, &mIoService)
        );
    }

    mDbInterface.initialize();
}

//
// ---> deinitialize();
//
// deinitialize MuxManager class and deinitialize DbInterface instance
//
void MuxManager::deinitialize()
{
    mDbInterface.deinitialize();
}

//
// ---> run();
//
// start Boost IO Service event loop
//
void MuxManager::run()
{
    mIoService.run();
}

//
// ---> terminate();
//
// stop and terminate Boost IO Service event loop
//
void MuxManager::terminate()
{
    mIoService.stop();
    mThreadGroup.join_all();
}

//
// ---> addOrUpdateMuxPort(const std::string &portName, boost::asio::ip::address);
//
// update MUX port server/blade IPv4 Address. If port is not found, create new MuxPort object
//
void MuxManager::addOrUpdateMuxPort(const std::string &portName, boost::asio::ip::address smartNicIpAddress)
{
    MUXLOGINFO(boost::format("%s: server IP: %s") % portName % smartNicIpAddress);
    boost::system::error_code errorCode;
    std::shared_ptr<MuxPort> muxPortPtr = getMuxPortPtrOrThrow(portName);

    if (smartNicIpAddress.is_v4()) {
        muxPortPtr->setServerIpv4Address(smartNicIpAddress);
        muxPortPtr->initializeLinkProber();
    }
    else if (smartNicIpAddress.is_v6()) {
        // handle IPv6 probing
    }
}

//
// ---> updateMuxPortConfig(const std::string &portName, const std::string &config);
//
// update MUX port server/blade IPv4 Address. If port is not found, create new MuxPort object
//
void MuxManager::updateMuxPortConfig(const std::string &portName, const std::string &config)
{
    MUXLOGINFO(boost::format("%s: Mux port config: %s") % portName % config);

    PortMapIterator portMapIterator = mPortMap.find(portName);
    if (portMapIterator != mPortMap.end()) {
        portMapIterator->second->handleMuxConfig(config);
    }
}

//
// ---> addOrUpdateMuxPortLinkState(const std::string &portName, const std::string &linkState);
//
// update MUX port server/blade IPv4 Address. If port is not found, create new MuxPort object
//
void MuxManager::addOrUpdateMuxPortLinkState(const std::string &portName, const std::string &linkState)
{
    MUXLOGINFO(boost::format("%s: link state: %s") % portName % linkState);

    std::shared_ptr<MuxPort> muxPortPtr = getMuxPortPtrOrThrow(portName);
    muxPortPtr->handleLinkState(linkState);
}

//
// ---> addOrUpdateMuxPortMuxState(const std::string &portName, const std::string &muxState);
//
// update MUX port state db notification
//
void MuxManager::addOrUpdateMuxPortMuxState(const std::string &portName, const std::string &muxState)
{
    MUXLOGDEBUG(boost::format("%s: state db mux state: %s") % portName % muxState);

    std::shared_ptr<MuxPort> muxPortPtr = getMuxPortPtrOrThrow(portName);
    muxPortPtr->handleMuxState(muxState);
}

//
// ---> processGetServerMacAddress(const std::string &portName, const std::array<uint8_t, ETHER_ADDR_LEN> &address);
//
// update MUX port server MAC address
//
void MuxManager::processGetServerMacAddress(
    const std::string &portName,
    const std::array<uint8_t, ETHER_ADDR_LEN> &address
)
{
    MUXLOGDEBUG(portName);

    PortMapIterator portMapIterator = mPortMap.find(portName);
    if (portMapIterator != mPortMap.end()) {
        portMapIterator->second->handleGetServerMacAddress(address);
    }
}

//
// ---> processGetMuxState(const std::string &portName, const std::string &muxState);
//
// update MUX port state db notification
//
void MuxManager::processGetMuxState(const std::string &portName, const std::string &muxState)
{
    MUXLOGDEBUG(boost::format("%s: state db mux state: %s") % portName % muxState);

    PortMapIterator portMapIterator = mPortMap.find(portName);
    if (portMapIterator != mPortMap.end()) {
        portMapIterator->second->handleGetMuxState(muxState);
    }
}

//
// ---> processProbeMuxState(const std::string &portName, const std::string &muxState);
//
// update MUX port app db notification
//
void MuxManager::processProbeMuxState(const std::string &portName, const std::string &muxState)
{
    MUXLOGDEBUG(boost::format("%s: app db mux state: %s") % portName % muxState);

    PortMapIterator portMapIterator = mPortMap.find(portName);
    if (portMapIterator != mPortMap.end()) {
        portMapIterator->second->handleProbeMuxState(muxState);
    }
}

//
// ---> getMuxPortPtrOrThrow(const std::string &portName);
//
// retrieve a pointer to MuxPort if it exist or create a new MuxPort object
//
std::shared_ptr<MuxPort> MuxManager::getMuxPortPtrOrThrow(const std::string &portName)
{
    std::shared_ptr<MuxPort> muxPortPtr;

    try {
        PortMapIterator portMapIterator = mPortMap.find(portName);
        if (portMapIterator == mPortMap.end()) {
            uint16_t serverId = atoi(portName.substr(portName.find_last_not_of("0123456789") + 1).c_str());
            muxPortPtr = std::make_shared<MuxPort> (
                &mDbInterface,
                mMuxConfig,
                portName,
                serverId,
                mIoService
            );
            mPortMap.insert({portName, muxPortPtr});
        }
        else {
            muxPortPtr = portMapIterator->second;
        }
    }
    catch (const std::bad_alloc &ex) {
        std::ostringstream errMsg;
        errMsg << "Failed allocate memory. Exception details: " << ex.what();

        throw MUX_ERROR(BadAlloc, errMsg.str());
    }

    return muxPortPtr;
}

//
// ---> handleSignal(const boost::system::error_code errorCode, int signalNumber)'
//
// handles system signal
//
void MuxManager::handleSignal(const boost::system::error_code errorCode, int signalNumber)
{
    if (!errorCode) {
        MUXLOGFATAL(boost::format("Got signal: %d") % signalNumber);

        boost::log::trivial::severity_level level;
        switch (signalNumber) {
        case SIGINT:
        case SIGTERM:
            break;
        case SIGUSR1:
             level = common::MuxLogger::getInstance()->getLevel() == boost::log::trivial::severity_level::trace ?
                    boost::log::trivial::severity_level::fatal :
                    static_cast<boost::log::trivial::severity_level> (common::MuxLogger::getInstance()->getLevel() - 1);
            common::MuxLogger::getInstance()->setLevel(level);
            MUXLOGFATAL(boost::format("Updated log level to: %s") % level);
            break;
        case SIGUSR2:
            //@TODO: try to dumb state transition of all MUXes here
            break;
        default:
            break;
        }
    }

    if (signalNumber == SIGINT || signalNumber == SIGTERM) {
        mSignalSet.clear();
        handleProcessTerminate();
    } else {
        mSignalSet.async_wait(boost::bind(&MuxManager::handleSignal,
            this,
            boost::asio::placeholders::error,
            boost::asio::placeholders::signal_number
        ));
    }
}

//
// ---> handleProcessTerminate();
//
// stop DB interface thread and stop boost io service
//
void MuxManager::handleProcessTerminate()
{
    mDbInterface.stopSwssNotificationPoll();
    mDbInterface.getBarrier().wait();
    mIoService.stop();
    mDbInterface.getBarrier().wait();
}

} /* namespace mux */
