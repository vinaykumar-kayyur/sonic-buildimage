/*
 * Header file for eventd daemon
 */
#include "events_service.h"

typedef map<runtime_id_t, events_data_type_t> last_events_t;

/*
 *  Started by eventd_service.
 *  Creates XPUB & XSUB end points.
 onicanalytics.azurecr.io  Bind the same
 *  Create a PUB socket end point for capture and bind.
 *  Call run_proxy method with sockets in a dedicated thread.
 *  Thread runs forever until the zmq context is terminated.
 */
class eventd_proxy
{
    public:
        eventd_proxy(void *ctx) : m_ctx(ctx), m_frontend(NULL), m_backend(NULL),
            m_capture(NULL) {};

        ~eventd_proxy() {
            zmq_close(m_frontend);
            zmq_close(m_backend);
            zmq_close(m_capture);

            if (m_thr.joinable())
                m_thr.join();
        }

        int init();

    private:
        void run();

        void *m_ctx;
        void *m_frontend;
        void *m_backend;
        void *m_capture;
        thread m_thr;
};


/*
 *  Capture/Cache service
 *
 *  The service started in a dedicted thread upon demand.
 *  It is controlled by the caller.
 *  On cache init, the thread is created.
 *      Upon create, it creates a SUB socket to PUB end point of capture.
 *      PUB end point is maintained by zproxy service.
 *
 *  On Cache start, the thread is signalled to start reading.
 *
 *  On cache stop, it is signalled to stop reading and exit. Caller waits
 *  for thread to exit, before starting to read cached data, to ensure
 *  that the data is not handled by two threads concurrently.
 *
 *  This thread maintains its own copy of cache. Reader, does a swap
 *  after thread exits.
 *  This thread ensures the cache is empty at the init.
 *
 *  Upon cache start, the thread is blocked in receive call with timeout.
 *  Only upon receive/timeout, it would notice stop signal. Hence stop
 *  is not synchronous. The caller may wait for thread to terminate
 *  via thread.join().
 *
 *  Each event is 2 parts. It drops the first part, which is
 *  more for filtering events. It creates string from second part
 *  and saves it.
 *
 *  The string is the serialized version of internal_event_ref
 *
 *  It keeps two sets of data
 *      1) List of all events received in vector in same order as received
 *      2) Map of last event from each runtime id upon list overflow max size.
 *
 *  We add to the vector as much as allowed by vector and max limit,
 *  whichever comes first.
 *  
 *  The sequence number in internal event will help assess the missed count
 *  by the consumer of the cache data.
 *
 */
typedef enum {
    NEED_INIT = 0, 
    INIT_CAPTURE,
    START_CAPTURE,
    STOP_CAPTURE
} capture_control_t;


int capture_status;

class capture_service
{
    public:
        capture_service(void *ctx, int cache_max) : m_ctx(ctx), m_socket(NULL),
            m_ctrl(NEED_INIT), m_cache_max(cache_max)
        {}

        ~capture_service();

        int set_control(capture_control_t ctrl, events_data_lst_t *p=NULL);

        int read_cache(events_data_lst_t &lst_fifo,
                last_events_t &lst_last);

    private:
        void init_capture_cache(const events_data_lst_t &lst);
        void do_capture();

        void stop_capture();

        void *m_ctx;
        void *m_socket;
        capture_control_t m_ctrl;
        thread m_thr;

        int m_cache_max;

        events_data_lst_t m_events;

        last_events_t m_last_events;

        typedef map<runtime_id_t, sequence_t> pre_exist_id_t;
        pre_exist_id_t m_pre_exist_id;

};


/*
 * Main server, that starts the zproxy service and honor
 * eventd service requests event_req_type_t
 *
 *  For echo, it just echoes
 *
 *  FOr cache start, create the SUB end of capture and kick off
 *  capture_events thread. Upon cache stop command, close the handle
 *  which will stop the caching thread with read failure.
 *
 *  for cache read, returns the collected events in chunks.
 *
 */
void run_eventd_service();


