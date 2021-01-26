/*
 * MuxPortConfig.cpp
 *
 *  Created on: Oct 21, 2020
 *      Author: tamer
 */

#include "common/MuxPortConfig.h"

namespace common
{

//
// ---> MuxPortConfig(MuxConfig &muxConfig, const std::string &portName, uint16_t serverId);
//
// class constructor
//
MuxPortConfig::MuxPortConfig(
    MuxConfig &muxConfig,
    const std::string &portName,
    uint16_t serverId
) :
    mMuxConfig(muxConfig),
    mPortName(portName),
    mServerId(serverId)
{
}

} /* namespace common */
