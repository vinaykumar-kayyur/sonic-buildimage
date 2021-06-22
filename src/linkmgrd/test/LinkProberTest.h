/*
 * LinkProberTest.h
 *
 *  Created on: May 12, 2021
 *      Author: taahme
 */

#ifndef LINKPROBERTEST_H_
#define LINKPROBERTEST_H_

#include "gtest/gtest.h"

#include "FakeMuxPort.h"
#include "link_prober/LinkProber.h"

namespace test
{

class LinkProberTest: public ::testing::Test
{
public:
    LinkProberTest();
    virtual ~LinkProberTest() = default;

    void initialize() {mLinkProber.initialize();};
    void initializeSendBuffer() {mLinkProber.initializeSendBuffer();};
    void handleUpdateEthernetFrame() {mLinkProber.handleUpdateEthernetFrame();};
    void handleUpdateSequenceNumber() {mLinkProber.updateIcmpSequenceNo();};
    std::array<uint8_t, MUX_MAX_ICMP_BUFFER_SIZE> getTxBuffer() {return mLinkProber.getTxBuffer();};

    boost::asio::io_service mIoService;
    common::MuxConfig mMuxConfig;
    std::shared_ptr<FakeDbInterface> mDbInterfacePtr;
    std::string mPortName = "EtherTest01";
    std::string mSmartNicIpAddress = "192.168.1.20";
    uint16_t mServerId = 01;

    FakeMuxPort mFakeMuxPort;
    link_prober::LinkProber mLinkProber;
};

} /* namespace test */

#endif /* LINKPROBERTEST_H_ */
