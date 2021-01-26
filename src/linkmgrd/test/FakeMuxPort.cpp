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
    setLinkProberPtr(std::dynamic_pointer_cast<link_prober::LinkProber> (mFakeLinkProber));
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
