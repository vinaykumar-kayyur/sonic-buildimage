/*
 * MuxPort.h
 *
 *  Created on: Oct 23, 2020
 *      Author: tamer
 */

#ifndef FAKEMUXPORT_H_
#define FAKEMUXPORT_H_

#include <gtest/gtest.h>
#include <boost/asio.hpp>

#include "MuxPort.h"
#include "FakeDbInterface.h"
#include "FakeLinkProber.h"

namespace test
{

class FakeMuxPort: public ::mux::MuxPort
{
public:
    FakeMuxPort(
        FakeDbInterface *dbInterface,
        common::MuxConfig &muxConfig,
        std::string &portName,
        uint16_t serverId,
        boost::asio::io_service &ioService
    );
    virtual ~FakeMuxPort() = default;

    void activateStateMachine();

    const link_manager::LinkManagerStateMachine::CompositeState& getCompositeState() {return getLinkManagerStateMachine()->getCompositeState();};
    link_prober::LinkProberStateMachine& getLinkProberStateMachine() {return getLinkManagerStateMachine()->getLinkProberStateMachine();};
    mux_state::MuxStateMachine& getMuxStateMachine() {return getLinkManagerStateMachine()->getMuxStateMachine();};
    link_state::LinkStateMachine& getLinkStateMachine() {return getLinkManagerStateMachine()->getLinkStateMachine();};

    std::shared_ptr<FakeLinkProber> mFakeLinkProber;
};

} /* namespace test */

#endif /* FAKEMUXPORT_H_ */
