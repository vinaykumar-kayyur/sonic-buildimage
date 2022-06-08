#include <iostream>
#include <memory>
#include <thread>
#include <algorithm>
#include <deque>
#include <regex>
#include <chrono>
#include "gtest/gtest.h"
#include "events_common.h"
#include "events.h"
#include "../src/eventd.h"

using namespace std;

typedef vector<internal_event_t> lst_events_t;

void run_sub(void *zctx, bool &term, string &read_source, lst_events_t &lst)
{
    void *mock_sub = zmq_socket (zctx, ZMQ_SUB);
    string source;
    internal_event_t ev_int;
    int block_ms = 200;

    EXPECT_TRUE(NULL != mock_sub);
    EXPECT_EQ(0, zmq_connect(mock_sub, get_config(XPUB_END_KEY).c_str()));
    EXPECT_EQ(0, zmq_setsockopt(mock_sub, ZMQ_SUBSCRIBE, "", 0));
    EXPECT_EQ(0, zmq_setsockopt(mock_sub, ZMQ_RCVTIMEO, &block_ms, sizeof (block_ms)));

    while(!term) {
        if (0 == zmq_message_read(mock_sub, 0, source, ev_int)) {
            lst.push_back(ev_int);
            read_source.swap(source);
        }
    }

    zmq_close(mock_sub);
}

void *init_pub(void *zctx)
{
    void *mock_pub = zmq_socket (zctx, ZMQ_PUB);
    EXPECT_TRUE(NULL != mock_pub);
    EXPECT_EQ(0, zmq_connect(mock_pub, get_config(XSUB_END_KEY).c_str()));

    return mock_pub;
}

void run_pub(void *mock_pub, const string wr_source, lst_events_t &lst)
{
    for(lst_events_t::const_iterator itc = lst.begin(); itc != lst.end(); ++itc) {
        EXPECT_EQ(0, zmq_message_send(mock_pub, wr_source, *itc));
    }
}


static internal_event_t
create_ev(const string rid, sequence_t n, const string d)
{
    stringstream ss;

    ss << d << ":" << n;

    return internal_event_t({ {EVENT_STR_DATA, ss.str()},
            { EVENT_RUNTIME_ID, rid }, { EVENT_SEQUENCE, seq_to_str(n) }});
}



TEST(eventd, proxy)
{
    printf("TEST started\n");
    bool term_sub = false;
    string rd_source, wr_source("hello");
    lst_events_t rd_evts, wr_evts;

    void *zctx = zmq_ctx_new();
    EXPECT_TRUE(NULL != zctx);

    eventd_proxy *pxy = new eventd_proxy(zctx);
    EXPECT_TRUE(NULL != pxy);

    /* Starting proxy */
    EXPECT_EQ(0, pxy->init());

    /* subscriber in a thread */
    thread thr(&run_sub, zctx, ref(term_sub), ref(rd_source), ref(rd_evts));

    /* Init pub connection */
    void *mock_pub = init_pub(zctx);

    /* Provide time for async connect to complete */
    this_thread::sleep_for(chrono::milliseconds(100));

    for(int i=0; i<5; ++i) {
        wr_evts.push_back(create_ev("hello", i, "test body"));
    }

    EXPECT_TRUE(rd_evts.empty());
    EXPECT_TRUE(rd_source.empty());

    /* Publish events. */
    run_pub(mock_pub, wr_source, wr_evts);

    while(rd_evts.size() != wr_evts.size()) {
        printf("rd_evts.size != wr_evts.size %d != %d\n", 
                (int)rd_evts.size(), (int)wr_evts.size());
        this_thread::sleep_for(chrono::milliseconds(10));
    }

    term_sub = true;
    printf("Waiting for sub thread to join...\n");

    thr.join();
    zmq_close(mock_pub);
    zmq_ctx_term(zctx);
}

