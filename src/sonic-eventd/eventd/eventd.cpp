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

int
eventd_proxy::init()
{
    int ret = -1;
    SWSS_LOG_INFO("Start xpub/xsub proxy");

    m_frontend = zmq_socket(m_ctx, ZMQ_XSUB);
    RET_ON_ERR(m_frontend != NULL, "failing to get ZMQ_XSUB socket");

    int rc = zmq_bind(m_frontend, get_config(XSUB_END_KEY));
    RET_ON_ERR(rc == 0, "Failing to bind XSUB to %s", get_config(XSUB_END_KEY));

    m_backend = zmq_socket(m_ctx, ZMQ_XPUB);
    RET_ON_ERR(m_backend != NULL, "failing to get ZMQ_XPUB socket");

    rc = zmq_bind(m_backend, get_config(XPUB_END_KEY));
    RET_ON_ERR(rc == 0, "Failing to bind XPUB to %s", get_config(XPUB_END_KEY));

    m_capture = zmq_socket(m_ctx, ZMQ_PUB);
    RET_ON_ERR(m_capture != NULL, "failing to get ZMQ_PUB socket for capture");

    rc = zmq_bind(m_capture, get_config(CAPTURE_END_KEY));
    RET_ON_ERR(rc == 0, "Failing to bind capture PUB to %s", get_config(CAPTURE_END_KEY));

    m_thr = thread(&eventd_proxy::run, this);
    ret = 0;
out:
    return ret;
}

void
eventd_proxy::run()
{
    SWSS_LOG_INFO("Running xpub/xsub proxy");

    /* runs forever until zmq context is terminated */
    zmq_proxy(m_frontend, m_backend, m_capture);

    return 0;
}


capture_service::~capture_service()
{
    stop_capture();
}

capture_service::stop_capture()
{
    if (m_socket != NULL) {
        zmq_close(m_socket);
        m_socket = NULL;
    }
    if (m_thr.joinable()) {
        m_thr.join();
    }
}

static bool
validate_event(const internal_event_t &event, string &rid, string &seq)
{
    bool ret = false;

    internal_event_t::const_iterator itc_r, itc_s, itc_e;
    itc_r = event.find(EVENT_RUNTIME_ID);
    itc_s = event.find(EVENT_SEQUENCE);
    itc_e = event.find(EVENT_STR_DATA);

    if ((itc_r != event.end()) && (itc_s != event.end()) && (itc_e != event.end())) {
        invalid_evt = true;

        rid = itc_r->second;
        seq = itc_s->second;
    }
    else {
        SWSS_LOG_ERROR("Invalid evt: %s", map_to_str(event).str());
    }

    return ret;
}
        

void
capture_service::init_capture_cache(events_data_lst_t &lst)
{
    /* clean any pre-existing cache */
    int ret = -1;
    int i;
    string rid, seq;

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
    for (events_data_lst_t::it = lst.begin(); it != lst.end(); ++it) {
        internal_event_t event;

        if (deserialize(*itc, event) == 0) {
            if (validate_event(event, rid, seq)) {
                m_pre_exist_id[event[EVENT_RUNTIME_ID]] = rid;
                m_events.push_back(*itc);
            }
        }
        else {
            SWSS_LOG_ERROR("failed to serialize cache message from subscriber; DROP");
        }
    }
}


void
capture_service::do_capture()
{
    /* clean any pre-existing cache */
    int ret = -1;
    int i;
    string rid, seq;

    /* Check read events against provided cache for 2 seconds to skip */
    chrono::steady_clock::timepoint start = chrono::steady_clock::now();
    while(!m_pre_exist_id.empty()) {
        internal_event_t event;
        string source, evt_str;

        RET_ON_ERR(zmq_message_read(m_socket, 0, source, event) == 0,
                "Failed to read from capture socket");

        if (validate_event(event, rid, seq)) {

            serialize(event, evt_str);
            m_pre_exist_id_t::iterator it = m_pre_exist_id.find(rid);

            if (it != m_pre_exist_id.end()) {
                seq = events_base::str_to_seq(seq);
                if (seq > it->second) {
                    m_events.push_back(evt_str);
                }
                if (seq >= it->second) {
                    m_pre_exist_id.erase(it);
                }
            }
        }
        if(chrono::steady_clock::now() - start > chrono::seconds(2))
            break;
    }
    pre_exist_id_t().swap(m_pre_exist_id);

    /* Save until max allowed */
    while(m_events.size() < m_cache_max) {
        internal_event_t event;
        string source, evt_str;

        RET_ON_ERR(zmq_message_read(m_socket, 0, source, event) == 0,
                "Failed to read from capture socket");
        if (validate_event(event, rid, seq)) {
            serialize(event, evt_str);
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
    }


    /* Save only last event per sender */
    while(true) {
        internal_event_t event;
        string source, evt_str;

        RET_ON_ERR(zmq_message_read(m_socket, 0, source, event) == 0,
                "Failed to read from capture socket");

        if (validate_event(event, rid, seq)) {
            serialize(event, evt_str);
            m_last_events[rid] = evt_str;
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
capture_service::set_control(capture_control_t ctrl, events_data_lst_t *lst)
{
    int ret = -1;

    /* Can go in single step only. */
    RET_ON_ERR((ctrl - m_ctrl) == 1, "m_ctrl(%d) > ctrl(%d)", m_ctrl, ctrl);
    m_ctrl = ctrl;

    switch(m_ctrl) {
        case INIT_CAPTURE:
            {
            void *sock = NULL;
            sock = zmq_socket(m_ctx, ZMQ_SUB);
            RET_ON_ERR(sock != NULL, "failing to get ZMQ_SUB socket");

            rc = zmq_connect(sock, get_config(CAPTURE_END_KEY));
            RET_ON_ERR(rc == 0, "Failing to bind capture SUB to %s", get_config(CAPTURE_END_KEY));

            rc = zmq_setsockopt(sock, ZMQ_SUBSCRIBE, "", 0);
            RET_ON_ERR(rc == 0, "Failing to ZMQ_SUBSCRIBE");

            m_socket = sock;
            }
            ret = 0;
            break;

        case START_CAPTURE:
            
            /*
             * Reserve a MAX_PUBLISHERS_COUNT entries for last events, as we use it only
             * upon m_events/vector overflow, which might block adding new entries in map
             * if overall mem consumption is too high. Clearing the map just before use
             * is likely to help.
             */
            for (i=0; i<MAX_PUBLISHERS_COUNT; ++i) {
                m_last_events[to_string(i)] = "";
            }
            
            if ((lst != NULL) && (!lst->empty())) {
                init_capture_cache(*lst);
            }

            m_thr = thread(&capture_service::do_capture, this);
            RET_ON_ERR(m_thr.joinable(), "Capture thread not running");
            ret = 0;
            break;


        case STOP_CAPTURE:
            /*
             * Caller would have initiated SUBS channel.
             * Read for CACHE_DRAIN_IN_MILLISECS to drain off cache
             * before stopping.
             */
            this_thread::sleep_for(chrono::milliseconds(CACHE_DRAIN_IN_MILLISECS));
            stop_capture();
            break;

        default:
            SWSS_LOG_ERROR("Unexpected code=%d", m_ctrl);
            break;
    }
out:
    return ret;
}

int
capture_service::read_cache(events_data_lst_t &lst_fifo,
        last_events_t &lst_last)
{
    lst_fifo.swap(m_events);
    lst_last.swap(m_last_events);
    last_events_t().swap(m_last_events);
    events_data_lst_t().swap(m_events);
    return 0;
}


void
run_eventd_service()
{
    event_service service;
    eventd_proxy *proxy = NULL;
    capture_service *capture = NULL;

    events_data_lst_t capture_fifo_events;
    last_events_t capture_last_events;

    SWSS_LOG_ERROR("Eventd service starting\n");

    void *zctx = zmq_ctx_new();
    RET_ON_ERR(ctx != NULL, "Failed to get zmq ctx");

    cache_max = get_config_data(CACHE_MAX_CNT, (uint32_t)MAX_CACHE_SIZE);
    RET_ON_ERR(cache_max > 0, "Failed to get CACHE_MAX_CNT");

    proxy = new eventd_proxy(zctx);
    RET_ON_ERR(proxy != NULL, "Failed to create proxy");

    RET_ON_ERR(proxy->init() == 0, "Failed to init proxy");

    RET_ON_ERR(service.init_server(zctx) == 0, "Failed to init service");

    while(true) {
        int code, resp = -1; 
        events_data_lst_t req_data, resp_data;

        RET_ON_ERR(channel_read(code, data) == 0,
                "Failed to read request");

        switch(code) {
            case EVENT_CACHE_INIT:
                /* connect only*/
                if (capture != NULL) {
                    delete capture;
                }
                events_data_lst_t().swap(capture_fifo_events);
                last_events_t().swap(capture_last_events);

                capture = new capture_service(zctx, cache_max);
                if (capture != NULL) {
                    resp = capture->set_control(INIT_CAPTURE);
                }
                break;

                
            case EVENT_CACHE_START:
                if (capture == NULL) {
                    SWSS_LOG_ERROR("Cache is not initialized to start");
                    resp = -1;
                    break;
                }
                resp = capture->set_control(START_CAPTURE, req_data);
                break;

                
            case EVENT_CACHE_STOP:
                if (capture == NULL) {
                    SWSS_LOG_ERROR("Cache is not initialized to stop");
                    resp = -1;
                    break;
                }
                resp = capture->set_control(STOP_CAPTURE);
                if (resp == 0) {
                    resp = capture->read_cache(capture_fifo_events, capture_last_events);
                }
                delete capture;
                capture = NULL;
                break;


            case EVENT_CACHE_READ:
                if (capture != NULL) {
                    SWSS_LOG_ERROR("Cache is not stopped yet.");
                    resp = -1;
                    break;
                }
                resp = 0;

                if (capture_fifo_events.empty()) {
                    for (last_events_t::iterator it = capture_last_events.begin();
                            it != capture_last_events.end(); ++it) {
                        capture_fifo_events.push_back(it->second);
                    }
                    last_events_t().swap(capture_last_events);
                }

                int sz = capture_fifo_events.size() < READ_SET_SIZE ?
                    capture_fifo_events.size() : READ_SET_SIZE;

                if (sz != 0) {
                    auto it = std::next(capture_fifo_events.begin(), sz);
                    move(capture_fifo_events.begin(), capture_fifo_events.end(),
                            back_inserter(resp_data));

                    if (sz == capture_fifo_events.size()) {
                        events_data_lst_t().swap(capture_fifo_events);
                    } else {
                        events.erase(capture_fifo_events.begin(), it);
                    }
                }
                break;


            case EVENT_ECHO:
                resp = 0;
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
    m_service.close();
    if (proxy != NULL) {
        delete proxy;
    }
    if (capture != NULL) {
        delete capture;
    }
    if (zctx != NULL) {
        zmq_ctx_term(zctx);
    }
    SWSS_LOG_ERROR("Eventd service exiting\n");
}


int main()
{
    SWSS_LOG_INFO("The eventd service started");

    run_eventd_service();

    SWSS_LOG_INFO("The eventd service exited");

    return 0;
}


