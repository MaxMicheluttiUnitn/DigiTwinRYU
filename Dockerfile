FROM ubuntu:22.04

USER root
WORKDIR /root

COPY traffic_sim.py /root/
COPY start_routine.py /root/
COPY ENTRYPOINT.sh /

RUN apt-get update
RUN apt-get install python3 -y

RUN apt-get install -y --no-install-recommends \
    curl \
    dnsutils \
    ifupdown \
    iproute2 \
    iptables \
    iputils-ping \
    mininet \
    net-tools \
    openvswitch-switch \
    openvswitch-testcontroller \
    tcpdump \
    vim \
    x11-xserver-utils \
    xterm \
 && rm -rf /var/lib/apt/lists/* \
 && touch /etc/network/interfaces \
 && chmod +x /ENTRYPOINT.sh

RUN cd /root/ && mkdir traffic

EXPOSE 6633 6653 6640

ENTRYPOINT ["/ENTRYPOINT.sh"]
