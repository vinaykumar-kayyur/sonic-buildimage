/*
 * FakeDbInterface.h
 *
 *  Created on: Oct 23, 2020
 *      Author: tamer
 */

#ifndef FAKEDBINTERFACE_H_
#define FAKEDBINTERFACE_H_

#include "DbInterface.h"

namespace test
{

class FakeDbInterface: public mux::DbInterface
{
public:
    FakeDbInterface(boost::asio::io_service *ioService);
    FakeDbInterface(mux::MuxManager *muxManager, boost::asio::io_service *ioService);
    virtual ~FakeDbInterface() = default;

    virtual void setMuxState(const std::string &portName, mux_state::MuxState::Label label) override;
    virtual void getMuxState(const std::string &portName) override;
    virtual void probeMuxState(const std::string &portName) override;
    virtual void setMuxLinkmgrState(
        const std::string &portName,
        link_manager::LinkManagerStateMachine::Label label
    ) override;
    virtual void postMetricsEvent(
        const std::string &portName,
        link_manager::LinkManagerStateMachine::Metrics metrics,
        mux_state::MuxState::Label label
    ) override;

    void setNextMuxState(mux_state::MuxState::Label label) {mNextMuxState = label;};

public:
    mux_state::MuxState::Label mNextMuxState;

    uint32_t mMuxStateRequest[mux_state::MuxState::Label::Count] = {0, 0, 0, 0};

    uint32_t mSetMuxStateInvokeCount = 0;
    uint32_t mGetMuxStateInvokeCount = 0;
    uint32_t mProbeMuxStateInvokeCount = 0;
    uint32_t mSetMuxLinkmgrStateInvokeCount = 0;
    uint32_t mPostMetricsInvokeCount = 0;
};

} /* namespace test */

#endif /* FAKEDBINTERFACE_H_ */
