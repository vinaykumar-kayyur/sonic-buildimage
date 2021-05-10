/*
 * FakeDbInterface.cpp
 *
 *  Created on: Oct 23, 2020
 *      Author: tamer
 */

#include "FakeDbInterface.h"

namespace test
{

FakeDbInterface::FakeDbInterface(boost::asio::io_service *ioService) :
    mux::DbInterface(nullptr, ioService),
    mNextMuxState(mux_state::MuxState::Label::Unknown)
{
}

void FakeDbInterface::setMuxState(const std::string &portName, mux_state::MuxState::Label label)
{
    mSetMuxStateInvokeCount++;
}

void FakeDbInterface::getMuxState(const std::string &portName)
{
    mGetMuxStateInvokeCount++;
}

void FakeDbInterface::probeMuxState(const std::string &portName)
{
    mProbeMuxStateInvokeCount++;
}

void FakeDbInterface::setMuxLinkmgrState(const std::string &portName, link_manager::LinkManagerStateMachine::Label label)
{
    mSetMuxLinkmgrStateInvokeCount++;
}

void FakeDbInterface::postMetricsEvent(
    const std::string &portName,
    link_manager::LinkManagerStateMachine::Metrics metrics,
    mux_state::MuxState::Label label
)
{
    mPostMetricsInvokeCount++;
}

} /* namespace test */
