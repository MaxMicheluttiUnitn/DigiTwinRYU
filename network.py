#!/usr/bin/python3

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSKernelSwitch, RemoteController
from mininet.cli import CLI
from mininet.link import TCLink


class DigitalTwinTopo(Topo):
    def __init__(self):
        # Initialize topology
        Topo.__init__(self)

        # Create template host, switch, and link
        host_config = dict(inNamespace=True)
        host_link_config = dict()

        # Create switch nodes
        for i in range(3):
            sconfig = {"dpid": "%016x" % (i+1)}
            self.addSwitch(f"s{i+1}", **sconfig)

        # Create host nodes
        for i in range(2):
            self.addHost("h%d" % (i + 1), **host_config)

        # Add switch links
        # self.addLink("s1", "s2", **video_link_config)
        # self.addLink("s2", "s4", **video_link_config)
        # self.addLink("s1", "s3", **http_link_config)
        # self.addLink("s3", "s4", **http_link_config)
        self.addLink("s1", "s2", **host_link_config)
        self.addLink("s2", "s3", **host_link_config)
        #self.addLink("s3", "s1", **host_link_config)

        # Add host links
        self.addLink("h1", "s1", **host_link_config)
        #self.addLink("h2", "s2", **host_link_config)
        self.addLink("h2", "s3", **host_link_config)


topos = {"digitaltwintopo": (lambda: DigitalTwinTopo())}

def main():
    topo = DigitalTwinTopo()
    net = Mininet(
        topo=topo,
        switch=OVSKernelSwitch,
        build=False,
        autoSetMacs=True,
        autoStaticArp=True,
        link=TCLink,
    )
    controller = RemoteController("c1", ip="127.0.0.1", port=6633)
    net.addController(controller)
    net.build()
    net.start()
    CLI(net)
    net.stop()

if __name__ == "__main__":
    main()
