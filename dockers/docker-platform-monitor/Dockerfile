FROM docker-config-engine

## Make apt-get non-interactive
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update

RUN apt-get install -y sensord monit

## Config monit
RUN sed -i 's/^\s*set daemon/# set daemon/' /etc/monit/monitrc
RUN sed -i 's/^# set logfile syslog/set logfile syslog/' /etc/monit/monitrc
RUN sed -i 's/^\s*set logfile \/var/# set logfile \/var/' /etc/monit/monitrc
RUN sed -i 's/^# set httpd port/set httpd port/' /etc/monit/monitrc
RUN sed -i 's/^#    use address localhost/   use address localhost/' /etc/monit/monitrc
RUN sed -i 's/^#    allow localhost/   allow localhost/' /etc/monit/monitrc
RUN sed -i 's/^#    allow admin:monit/   allow admin:monit/' /etc/monit/monitrc
RUN sed -i 's/^#    allow @monit/   allow @monit/' /etc/monit/monitrc
RUN sed -i 's/^#    allow @users readonly/   allow @users readonly/' /etc/monit/monitrc

RUN echo "check filesystem root-aufs with path /" >> /etc/monit/monitrc
RUN echo "  if space usage > 85% for 5 times within 15 cycles then alert" >> /etc/monit/monitrc

## Clean up
RUN apt-get clean -y; apt-get autoclean -y; apt-get autoremove -y
RUN rm -rf /debs

COPY ["start.sh", "lm-sensors.sh", "/usr/bin/"]
COPY ["supervisord.conf", "/etc/supervisor/conf.d/"]

ENTRYPOINT ["/usr/bin/supervisord"]

