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

#define VEC_SIZE(p) ((int)p.size())

int
eventd_proxy::init()
{
    int ret = -1, rc = 0;
    SWSS_LOG_INFO("Start xpub/xsub proxy");

    m_frontend = zmq_socket(m_ctx, ZMQ_XSUB);
    RET_ON_ERR(m_frontend != NULL, "failing to get ZMQ_XSUB socket");

    rc = zmq_bind(m_frontend, get_config(string(XSUB_END_KEY)).c_str());
    RET_ON_ERR(rc == 0, "Failing to bind XSUB to %s", get_config(string(XSUB_END_KEY)).c_str());

    m_backend = zmq_socket(m_ctx, ZMQ_XPUB);
    RET_ON_ERR(m_backend != NULL, "failing to get ZMQ_XPUB socket");

    rc = zmq_bind(m_backend, get_config(string(XPUB_END_KEY)).c_str());
    RET_ON_ERR(rc == 0, "Failing to bind XPUB to %s", get_config(string(XPUB_END_KEY)).c_str());

    m_capture = zmq_socket(m_ctx, ZMQ_PUB);
    RET_ON_ERR(m_capture != NULL, "failing to get ZMQ_PUB socket for capture");

    rc = zmq_bind(m_capture, get_config(string(CAPTURE_END_KEY)).c_str());
    RET_ON_ERR(rc == 0, "Failing to bind capture PUB to %s", get_config(string(CAPTURE_END_KEY)).c_str());

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

    SWSS_LOG_INFO("Stopped xpub/xsub proxy");
}


capture_service::~capture_service()
{
    stop_capture();
}

void
capture_service::stop_capture()
{
    m_ctrl = STOP_CAPTURE;

    if (m_thr.joinable()) {
        m_thr.join();
    }
}

static bool
validate_event(const internal_event_t &event, runtime_id_t &rid, sequence_t &seq)
{
    bool ret = false;

    internal_event_t::const_iterator itc_r, itc_s, itc_e;
    itc_r = event.find(EVENT_RUNTIME_ID);
    itc_s = event.find(EVENT_SEQUENCE);
    itc_e = event.find(EVENT_STR_DATA);

    if ((itc_r != event.end()) && (itc_s != event.end()) && (itc_e != event.end())) {
        ret = true;
        rid = itc_r->second;
        seq = str_to_seq(itc_s->second);
    }
    else {
        SWSS_LOG_ERROR("Invalid evt: %s", map_to_str(event).c_str());
    }

    return ret;
}
        

void
capture_service::init_capture_cache(const event_serialized_lst_t &lst)
{
    /* clean any pre-existing cache */
    runtime_id_t rid;
    sequence_t seq;

    /* Cache given events as initial stock.
     * Save runtime ID with last seen seq to avoid duplicates, while reading
     * from capture socket.
     * No check for max cache size here, as most likely not needed.
     */
    for (event_serialized_lst_t::const_iterator itc = lst.begin(); itc != lst.end(); ++itc) {
        internal_event_t event;

        if (deserialize(*itc, event) == 0) {
            if (validate_event(event, rid, seq)) {
                m_pre_exist_id[rid] = seq;
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
    int rc;
    int block_ms=300;
    int init_cnt;

    typedef enum {
        /*
         * In this state every event read is compared with init cache given 
         * Only new events are saved.
         */
        CAP_STATE_INIT = 0, 

        /* In this state, all events read are cached until max limit */
        CAP_STATE_ACTIVE,

        /* Cache has hit max. Hence only save last event for each runime ID */
        CAP_STATE_LAST
    } cap_state_t;

    cap_state_t cap_state = CAP_STATE_INIT;

    void *sock = zmq_socket(m_ctx, ZMQ_SUB);
    RET_ON_ERR(sock != NULL, "failing to get ZMQ_SUB socket");

    rc = zmq_connect(sock, get_config(string(CAPTURE_END_KEY)).c_str());
    RET_ON_ERR(rc == 0, "Failing to bind capture SUB to %s", get_config(string(CAPTURE_END_KEY)).c_str());

    rc = zmq_setsockopt(sock, ZMQ_SUBSCRIBE, "", 0);
    RET_ON_ERR(rc == 0, "Failing to ZMQ_SUBSCRIBE");

    rc = zmq_setsockopt(sock, ZMQ_RCVTIMEO, &block_ms, sizeof (block_ms));
    RET_ON_ERR(rc == 0, "Failed to ZMQ_RCVTIMEO to %d", block_ms);

    m_cap_run = true;

    while (m_ctrl != START_CAPTURE) {
        /* Wait for capture start */
        this_thread::sleep_for(chrono::milliseconds(10));
    }

    /*
     * The cache service connects but defers any reading until caller provides
     * the startup cache. But all events that arrived since connect, though not read
     * will be held by ZMQ in its local cache. 
     *
     * When cache service starts reading, check against the initial stock for duplicates.
     * m_pre_exist_id caches the last seq number in initial stock for each runtime id.
     * So only allow sequence number greater than cached number.
     *
     * Theoretically all the events provided via initial stock could be duplicates.
     * Hence until as many events as in initial stock or until the cached id map
     * is empty, do this check.
     */
    init_cnt = (int)m_events.size();

    /* Read until STOP_CAPTURE */
    while(m_ctrl == START_CAPTURE) {
        runtime_id_t rid;
        sequence_t seq;
        internal_event_t event;
        string source, evt_str;

        if ((rc = zmq_message_read(sock, 0, source, event)) != 0) {
            /*
             * The capture socket captures SUBSCRIBE requests too.
             * The messge could contain subscribe filter strings and binary code.
             * Empty string with binary code will fail to deserialize.
             * Else would fail event validation.
             */
            RET_ON_ERR((rc == EAGAIN) || (rc == ERR_MESSAGE_INVALID),
                "0:Failed to read from capture socket");
            continue;
        }
        if (!validate_event(event, rid, seq)) {
            continue;
        }
        serialize(event, evt_str);

        switch(cap_state) {
        case CAP_STATE_INIT:
            {
                bool add = true;
                init_cnt--;
                pre_exist_id_t::iterator it = m_pre_exist_id.find(rid);

                if (it != m_pre_exist_id.end()) {
                    if (seq <= it->second) {
                        /* Duplicate; Later/same seq in cache. */
                        add = false;
                    }
                    if (seq >= it->second) {
                        /* new one; This runtime ID need not be checked again */
                        m_pre_exist_id.erase(it);
                    }
                }
                if (add) {
                    m_events.push_back(evt_str);
                }
            }
            if(m_pre_exist_id.empty() || (init_cnt <= 0)) {
                /* Init check is no more needed. */
                pre_exist_id_t().swap(m_pre_exist_id);
                cap_state = CAP_STATE_ACTIVE;
            }
            break;

        case CAP_STATE_ACTIVE:
            /* Save until max allowed */
            try
            {
                m_events.push_back(evt_str);
                if (VEC_SIZE(m_events) >= m_cache_max) {
                    cap_state = CAP_STATE_LAST;
                }
                break;
            }
            catch (bad_alloc& e) 
            {
                stringstream ss;
                ss << e.what();
                SWSS_LOG_ERROR("Cache save event failed with %s events:size=%d",
                        ss.str().c_str(), VEC_SIZE(m_events));
                cap_state = CAP_STATE_LAST;
                // fall through to save this event in last set.
            }

        case CAP_STATE_LAST:
            if (!m_last_events_init) {
                /* Clear the map, created to ensure memory space available */
                m_last_events.clear();
                m_last_events_init = true;
            }
            m_last_events[rid] = evt_str;
            break;
        }
    }

out:
    /*
     * Capture stop will close the socket which fail the read
     * and hence bail out.
     */
    zmq_close(sock);
    m_cap_run = false;
    return;
}


int
capture_service::set_control(capture_control_t ctrl, event_serialized_lst_t *lst)
{
    int ret = -1;

    /* Can go in single step only. */
    RET_ON_ERR((ctrl - m_ctrl) == 1, "m_ctrl(%d)+1 < ctrl(%d)", m_ctrl, ctrl);

    switch(ctrl) {
        case INIT_CAPTURE:
            m_thr = thread(&capture_service::do_capture, this);
            for(int i=0; !m_cap_run && (i < 100); ++i) {
                /* Wait max a second for thread to init */
                this_thread::sleep_for(chrono::milliseconds(10));
            }
            RET_ON_ERR(m_cap_run, "Failed to init capture");
            m_ctrl = ctrl;
            ret = 0;
            break;

        case START_CAPTURE:
            
            /*
             * Reserve a MAX_PUBLISHERS_COUNT entries for last events, as we use it only
             * upon m_events/vector overflow, which might block adding new entries in map
             * if overall mem consumption is too high. Clearing the map just before use
             * is likely to help.
             */
            for (int i=0; i<MAX_PUBLISHERS_COUNT; ++i) {
                m_last_events[to_string(i)] = "";
            }
            
            if ((lst != NULL) && (!lst->empty())) {
                init_capture_cache(*lst);
            }
            m_ctrl = ctrl;
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
            ret = 0;
            break;

        default:
            SWSS_LOG_ERROR("Unexpected code=%d", ctrl);
            break;
    }
out:
    return ret;
}

int
capture_service::read_cache(event_serialized_lst_t &lst_fifo,
        last_events_t &lst_last)
{
    lst_fifo.swap(m_events);
    if (m_last_events_init) {
        lst_last.swap(m_last_events);
    } else {
        last_events_t().swap(lst_last);
    }
    last_events_t().swap(m_last_events);
    event_serialized_lst_t().swap(m_events);
    return 0;
}


void
run_eventd_service()
{
    int code = 0;
    int cache_max;
    event_service service;
    eventd_proxy *proxy = NULL;
    capture_service *capture = NULL;

    event_serialized_lst_t capture_fifo_events;
    last_events_t capture_last_events;

    SWSS_LOG_ERROR("Eventd service starting\n");

    void *zctx = zmq_ctx_new();
    RET_ON_ERR(zctx != NULL, "Failed to get zmq ctx");

    cache_max = get_config_data(string(CACHE_MAX_CNT), (int)MAX_CACHE_SIZE);
    RET_ON_ERR(cache_max > 0, "Failed to get CACHE_MAX_CNT");

    proxy = new eventd_proxy(zctx);
    RET_ON_ERR(proxy != NULL, "Failed to create proxy");

    RET_ON_ERR(proxy->init() == 0, "Failed to init proxy");

    RET_ON_ERR(service.init_server(zctx) == 0, "Failed to init service");

    while(code != EVENT_EXIT) {
        int resp = -1; 
        event_serialized_lst_t req_data, resp_data;

        RET_ON_ERR(service.channel_read(code, req_data) == 0,
                "Failed to read request");

        switch(code) {
            case EVENT_CACHE_INIT:
                /* connect only*/
                if (capture != NULL) {
                    delete capture;
                }
                event_serialized_lst_t().swap(capture_fifo_events);
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
                resp = capture->set_control(START_CAPTURE, &req_data);
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

                {
                    int sz = VEC_SIZE(capture_fifo_events) < READ_SET_SIZE ?
                        VEC_SIZE(capture_fifo_events) : READ_SET_SIZE;

                    if (sz != 0) {
                        auto it = std::next(capture_fifo_events.begin(), sz);
                        move(capture_fifo_events.begin(), capture_fifo_events.end(),
                                back_inserter(resp_data));

                        if (sz == VEC_SIZE(capture_fifo_events)) {
                            event_serialized_lst_t().swap(capture_fifo_events);
                        } else {
                            capture_fifo_events.erase(capture_fifo_events.begin(), it);
                        }
                    }
                }
                break;


            case EVENT_ECHO:
                resp = 0;
                resp_data.swap(req_data);
                break;

            case EVENT_EXIT:
                resp = 0;
                break;

            default:
                SWSS_LOG_ERROR("Unexpected request: %d", code);
                assert(false);
                break;
        }
        RET_ON_ERR(service.channel_write(resp, resp_data) == 0,
                "Failed to write response back");
    }
out:
    service.close_service();
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

