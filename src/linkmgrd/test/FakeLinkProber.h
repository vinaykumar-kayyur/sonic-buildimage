/*
 * FakeLinkProber.h
 *
 *  Created on: Oct 23, 2020
 *      Author: tamer
 */

#ifndef FAKELINKPROBER_H_
#define FAKELINKPROBER_H_

#include "link_prober/LinkProberStateMachine.h"
namespace test
{

class FakeLinkProber
{
public:
    FakeLinkProber(link_prober::LinkProberStateMachine *linkProberStateMachine);
    virtual ~FakeLinkProber() = default;

    template<class E>
    void postLinkProberEvent(E &e);

public:
    uint32_t mSuspendTxProbeCallCount = 0;

private:
    link_prober::LinkProberStateMachine *mLinkProberStateMachine;
};

} /* namespace test */

#endif /* FAKELINKPROBER_H_ */
