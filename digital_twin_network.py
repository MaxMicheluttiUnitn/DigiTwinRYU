from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSKernelSwitch, RemoteController
from mininet.cli import CLI
from mininet.link import TCLink
from traffic_sim import simulate_traffic

class DigitalTwinTopo(Topo):
    def __init__(self):
        Topo.__init__(self)

        host_config = dict(inNamespace=True)
        host_link_config = dict()
        for i in range(4):
            sconfig = {"dpid": "%016x" % (i+1)}
            self.addSwitch(f"s{i+1}", **sconfig)
        for i in range(4):
            self.addHost("h%d" % (i + 1), **host_config)

        self.addLink("s1", "s3", **host_link_config)
        self.addLink("s3", "h3", **host_link_config)
        self.addLink("s4", "h4", **host_link_config)
        self.addLink("s2", "h2", **host_link_config)
        self.addLink("s2", "s3", **host_link_config)
        self.addLink("s1", "h1", **host_link_config)
        self.addLink("s2", "s4", **host_link_config)

topos = {"digitaltwintopo": (lambda: DigitalTwinTopo())}

if __name__ == "__main__":
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
    simulate_traffic(net, False)
    net.stop()
