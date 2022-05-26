#include <thread>
#include "eventd.h"

/*
 * There are 3 threads, including the main
 *
 * main thread -- Runs eventd service that accepts commands event_req_type_t
 *  This can be used to control caching events and a no-op echo service.
 *
 * capture/cache service 
 *  Saves all the events between cache start & stop
 *
 * Main proxy service that runs XSUB/XPUB ends
 */

#define MB(N) ((N) * 1024 * 1024)
#define EVT_SIZE_AVG 150

#define MAX_CACHE_SIZE (MB(100) / (EVT_SIZE_AVG))

/* Count of elements returned in each read */
#define READ_SET_SIZE 100

/*
 * Max count of possible concurrent event publishers
 * A rough estimate only, more for mem reserve.
 * So this does not limit any usage
 */
#define MAX_PUBLISHERS_COUNT  1000


eventd_server::eventd_server() : m_capture(NULL)
{
    m_ctx = zmq_ctx_new();
    RET_ON_ERR(m_ctx != NULL, "Failed to get zmq ctx");
    m_cache_max = get_config_data(CACHE_MAX_CNT, (uint32_t)MAX_CACHE_SIZE);

out:
    return;
}


eventd_server::~eventd_server()
{
    close();
}


int
eventd_server::zproxy_service()
{
    int ret = -1;
    SWSS_LOG_INFO("Start xpub/xsub proxy");

    void *frontend = zmq_socket(m_ctx, ZMQ_XSUB);
    RET_ON_ERR(frontend != NULL, "failing to get ZMQ_XSUB socket");

    int rc = zmq_bind(frontend, get_config(XSUB_END_KEY));
    RET_ON_ERR(rc == 0, "Failing to bind XSUB to %s", get_config(XSUB_END_KEY));

    void *backend = zmq_socket(m_ctx, ZMQ_XPUB);
    RET_ON_ERR(backend != NULL, "failing to get ZMQ_XPUB socket");

    rc = zmq_bind(backend, get_config(XPUB_END_KEY));
    RET_ON_ERR(rc == 0, "Failing to bind XPUB to %s", get_config(XPUB_END_KEY));

    void *capture = zmq_socket(m_ctx, ZMQ_PUB);
    RET_ON_ERR(capture != NULL, "failing to get ZMQ_PUB socket for capture");

    rc = zmq_bind(capture, get_config(CAPTURE_END_KEY));
    RET_ON_ERR(rc == 0, "Failing to bind capture PUB to %s", get_config(CAPTURE_END_KEY));

    m_thread_proxy = thread(&eventd_server::zproxy_service_run, this, frontend, 
            backend, capture);
    ret = 0;
out:
    return ret;
}


void
eventd_server::zproxy_service_run(void *frontend, void *backend, void *capture)
{
    SWSS_LOG_INFO("Running xpub/xsub proxy");

    /* runs forever until zmq context is terminated */
    zmq_proxy(frontend, backend, capture);

    zmq_close(frontend);
    zmq_close(backend);
    zmq_close(capture);

    SWSS_LOG_ERR("Terminating xpub/xsub proxy");

    return 0;
}


int
eventd_server::capture_events(events_data_lst_t &lst)
{
    /* clean any pre-existing cache */
    int ret = -1;
    int i;

    /*
     * Reserve a MAX_PUBLISHERS_COUNT entries for last events, as we use it only
     * upon m_events/vector overflow, which might block adding new entries in map
     * if overall mem consumption is too high. Clearing the map just before use
     * is likely to help.
     */
    for (i=0; i<MAX_PUBLISHERS_COUNT; ++i) {
        m_last_events[to_string(i)] = "";
    }

    /* Cache last 
    typedef map<runtime_id_t, sequence_t> pre_exist_id_t;
    pre_exist_id_t pre_exist_id;

    RET_ON_ERR(m_capture != NULL, "capture sock is not initialized yet");

    if (!lst.empty()) {
        for (events_data_lst_t::it = lst.begin(); it != lst.end(); ++it) {
            internal_event_t event;

            if (deserialize(*itc, event) == 0) {
                pre_exist_id[event[EVENT_RUNTIME_ID]] = events_base::str_to_seq(event[EVENT_SEQUENCE]);
            }
            else {
                SWSS_LOG_ERROR("failed to serialize cache message from subscriber; DROP");
            }
        }
        m_events.swap(lst);
    }

    if (!pre_exist_id.empty()) {
        /* Check read events against provided cache for 2 seconds to skip */
        chrono::steady_clock::timepoint start = chrono::steady_clock::now();
        while(!pre_exist_id.empty()) {
            internal_event_t event;
            string source, evt_str;

            RET_ON_ERR(zmq_message_read(m_socket, 0, source, evt_str) == 0,
                    "Failed to read from capture socket");

            if (deserialize(evt_str, event) == 0) {
                pre_exist_id_t::iterator it = pre_exist_id.find(event[EVENT_RUNTIME_ID]);
                if (it != pre_exist_id.end()) {
                    seq = events_base::str_to_seq(event[EVENT_SEQUENCE]);
                    if (seq > it->second) {
                        m_events.push_back(evt_str);
                    }
                    if (seq >= it->second) {
                        pre_exist_id.erase(it);
                    }
                }
            }
            else {
                SWSS_LOG_ERROR("failed to serialize received event from publisher. DROP");
            }
            if(chrono::steady_clock::now() - start > chrono::seconds(2))
                break;
        }
        pre_exist_id_t().swap(pre_exist_id);
    }

    /* Save until max allowed */
    while(m_events.size() < m_cache_max) {
        string source, evt_str;

        RET_ON_ERR(zmq_message_read(m_socket, 0, source, evt_str) == 0,
                "Failed to read from capture socket");
        try
        {
            m_events.push_back(evt_str);
        }
        catch (exception& e)
        {
            stringstream ss;
            ss << e.what();
            SWSS_LOG_ERROR("Cache save event failed with %s events:size=%d",
                    ss.str().c_str(), m_events.size());
            break;
        }
    }


    /* Save only last event per sender */
    while(true) {
        internal_event_t event;
        string source, evt_str;

        RET_ON_ERR(zmq_message_read(m_socket, 0, source, evt_str) == 0,
                "Failed to read from capture socket");

        if (deserialize(evt_str, event) == 0) {
            m_last_events[event[EVENT_RUNTIME_ID]] = evt_str;
        }
        else {
            SWSS_LOG_ERROR("FAILED to serialize received event from publisher. DROP");
        }
    }
out:
    /*
     * Capture stop will close the socket which fail the read
     * and hence bail out.
     */
    return 0;
}


int
eventd_server::eventd_service()
{
    event_service service;

    RET_ON_ERR(zproxy_service() == 0, "Failed to start zproxy_service");

    RET_ON_ERR(service.init_server(m_ctx) == 0, "Failed to init service");

    while(true) {
        int code, resp = -1; 
        events_data_lst_t req_data, resp_data;

        RET_ON_ERR(channel_read(code, data) == 0,
                "Failed to read request");

        switch(code) {
            case EVENT_CACHE_INIT:
                /* connect only*/
                if (m_capture != NULL) {
                    resp_code = 1;
                    break;
                }
                m_capture = zmq_socket(m_ctx, ZMQ_SUB);
                RET_ON_ERR(capture != NULL, "failing to get ZMQ_SUB socket");

                rc = zmq_connect(capture, get_config(CAPTURE_END_KEY));
                RET_ON_ERR(rc == 0, "Failing to bind capture SUB to %s", get_config(CAPTURE_END_KEY));

                rc = zmq_setsockopt(sub_read, ZMQ_SUBSCRIBE, "", 0);
                RET_ON_ERR(rc == 0, "Failing to ZMQ_SUBSCRIBE");

                resp_code = 0;
                break;

                
            case EVENT_CACHE_START:
                if (m_capture == NULL) {
                    resp_code = -1;
                    break;
                }
                events_data_lst_t.swap(m_events);
                last_events_t.swap(m_last_events);

                /* Kick off the service */
                m_thread_capture = thread(&eventd_server::capture_events, this, req_data);

                resp_code = 0;
                break;

                
            case EVENT_CACHE_STOP:
                if (m_capture != NULL) {
                    /*
                     * Caller would have initiated SUBS channel.
                     * Read for CACHE_DRAIN_IN_MILLISECS to drain off cache
                     * before stopping.
                     */
                    this_thread::sleep_for(chrono::milliseconds(CACHE_DRAIN_IN_MILLISECS));
                    close(m_capture);
                    m_capture = NULL;

                    /* Wait for thread to end */
                    m_thread_capture.join();
                    resp_code = 0;
                }
                else {
                    resp_code = -1;
                }
                break;


            case EVENT_CACHE_READ:
                resp_code = 0;

                if (m_events.empty()) {
                    for (last_events_t::iterator it = m_last_events.begin();
                            it != m_last_events.end(); ++it) {
                        m_events.push_back(it->second);
                    }
                    last_events_t().swap(m_last_events);
                }

                int sz = m_events.size() < READ_SET_SIZE ? m_events.size() : READ_SET_SIZE;

                if (sz != 0) {
                    auto it = std::next(m_events.begin(), sz);
                    move(m_events.begin(), m_events.end(), back_inserter(resp_data));

                    if (sz == m_events.size()) {
                        events_data_lst_t().swap(m_events);
                    } else {
                        m_events.erase(m_events.begin(), it);
                    }
                }
                break;


            case EVENT_ECHO:
                resp_code = 0;
                resp_data.swap(req_data);

            default:
                SWSS_LOG_ERROR("Unexpected request: %d", code);
                assert(false);
                break;
        }
        RET_ON_ERR(channel_write(resp_code, resp_data) == 0,
                "Failed to write response back");
    }
out:
    /* Breaks here on fatal failure */
    if (m_capture != NULL) {
        close(m_capture);
        m_capture = NULL;
    }
    close();
    m_thread_proxy.join();
    m_thread_capture.join();
    return 0;
}



void eventd_server::close()
{
    zmq_ctx_term(m_ctx); m_ctx = NULL;

}

