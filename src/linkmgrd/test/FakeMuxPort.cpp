/*
 * MuxPort.cpp
 *
 *  Created on: Oct 23, 2020
 *      Author: tamer
 */

#include <memory>

#include "FakeMuxPort.h"
#include "FakeLinkProber.h"

namespace test
{

FakeMuxPort::FakeMuxPort(
    FakeDbInterface *dbInterface,
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
        std::make_shared<FakeLinkProber>(&getLinkManagerStateMachine()->getLinkProberStateMachine())
    )
{
    setSuspendTxFnPtr(boost::bind(&FakeLinkProber::suspendTxProbes, mFakeLinkProber.get(), boost::placeholders::_1));
    link_manager::LinkManagerStateMachine::initializeTransitionFunctionTable();
}

void FakeMuxPort::activateStateMachine()
{
    setComponentInitState(0);
    setComponentInitState(1);
    setComponentInitState(2);
    setComponentInitState(3);
}

} /* namespace test */
