/*
 * MuxPort.cpp
 *
 *  Created on: Oct 23, 2020
 *      Author: tamer
 */

#include <memory>

#include "common/MuxLogger.h"
#include "FakeMuxPort.h"
#include "FakeLinkProber.h"

namespace test
{

FakeMuxPort::FakeMuxPort(
    std::shared_ptr<FakeDbInterface> dbInterface,
    common::MuxConfig &muxConfig,
    std::string &portName,
    uint16_t serverId,
    boost::asio::io_service &ioService
) :
    mux::MuxPort(
        dbInterface,
        muxConfig,
        portName,
        serverId,
        ioService
    ),
    mFakeLinkProber(
        std::make_shared<FakeLinkProber> (&getLinkManagerStateMachine()->getLinkProberStateMachine())
    )
{
    std::string prog_name = "linkmgrd-test";
    std::string log_filename = "/tmp/" + prog_name + ".log";
    common::MuxLogger::getInstance()->initialize(prog_name, log_filename, boost::log::trivial::debug);
    common::MuxLogger::getInstance()->setLevel(boost::log::trivial::trace);
    link_manager::LinkManagerStateMachine::initializeTransitionFunctionTable();
    getLinkManagerStateMachine()->setInitializeProberFnPtr(
        boost::bind(&FakeLinkProber::initialize, mFakeLinkProber.get())
    );
    getLinkManagerStateMachine()->setStartProbingFnPtr(
        boost::bind(&FakeLinkProber::startProbing, mFakeLinkProber.get())
    );
    getLinkManagerStateMachine()->setUpdateEthernetFrameFnPtr(
        boost::bind(&FakeLinkProber::updateEthernetFrame, mFakeLinkProber.get())
    );
    getLinkManagerStateMachine()->setSuspendTxFnPtr(
        boost::bind(&FakeLinkProber::suspendTxProbes, mFakeLinkProber.get(), boost::placeholders::_1)
    );
}

void FakeMuxPort::activateStateMachine()
{
    setComponentInitState(0);
    setComponentInitState(1);
    setComponentInitState(2);
}

} /* namespace test */
