FROM docker-base

## TODO: remove if redis-server 3.2.4 comes into stable sources
COPY backports.list /etc/apt/sources.list.d/

## Install packages
## Clean up
RUN apt-get update &&                                                               \
    apt-get -y -t jessie-backports install                                          \
        redis-server                                                                \
        &&                                                                          \
    apt-get clean -y && apt-get autoclean -y && apt-get autoremove -y

RUN sed -ri 's/^daemonize yes$/daemonize no/' /etc/redis/redis.conf                 \
 && sed -ri 's/^logfile .*$/logfile ""/' /etc/redis/redis.conf                      \
 && sed -ri 's/^# syslog-enabled no$/syslog-enabled no/' /etc/redis/redis.conf

ENTRYPOINT service redis-server start
