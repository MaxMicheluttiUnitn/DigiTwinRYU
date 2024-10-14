from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
import time
import os

# from ryu.lib.packet import udp
# from ryu.lib.packet import tcp
# from ryu.lib.packet import icmp

FRAME_LENGTH_SECONDS = 10

INCLUDES = """from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSKernelSwitch, RemoteController
from mininet.cli import CLI
from mininet.link import TCLink
from traffic_sim import simulate_traffic

"""


DIGITAL_TWIN_CLASS_DEFINITION = """class DigitalTwinTopo(Topo):
    def __init__(self):
        Topo.__init__(self)

        host_config = dict(inNamespace=True)
        host_link_config = dict()
"""

SWITCH_CREATION_BLOCK ="""
            sconfig = {"dpid": "%016x" % (i+1)}
            self.addSwitch(f"s{i+1}", **sconfig)
"""

HOST_CREATION_BLOCK = """
            self.addHost("h%d" % (i + 1), **host_config)
"""

DIGITAL_TWIN_MAIN = """
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
    #controller = RemoteController("c1", ip="127.0.0.1", port=6633)
    #net.addController(controller)
    net.build()
    net.start()
    simulate_traffic(net, True)
    net.stop()
"""




class DigitalTwin(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(DigitalTwin, self).__init__(*args, **kwargs)
        # outport = self.slice_ports[dpid][slicenumber]
        self.mac_to_port = {}
        self.has_topology = False
        self.current_frame = 0
        self.creation_time = time.time()
        self.created_log_file = False

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install the table-miss flow entry.
        match = parser.OFPMatch()
        actions = [
            parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)
        ]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # construct flow_mod message and send it.
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(
                datapath=datapath,
                priority=priority,
                match=match,
                instructions=inst,
                burrer_id=buffer_id,
            )
        else:
            mod = parser.OFPFlowMod(
                datapath=datapath, priority=priority, match=match, instructions=inst
            )
        datapath.send_msg(mod)

    def _send_package(self, msg, datapath, in_port, actions):
        data = None
        ofproto = datapath.ofproto
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data
        out = datapath.ofproto_parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=data,
        )
        datapath.send_msg(out)

    def compute_topology(self):
        print("Computing topology")
        self.hosts = set()
        self.switches = set()
        self.links = set()
        # retrieve nodes in the network
        for dpid in self.mac_to_port.keys():
            self.switches.add("switch_"+str(dpid))
            for mac in self.mac_to_port[dpid].keys():
                if mac.startswith("00:00:00:00:00:"):
                    self.hosts.add("host_"+mac)
        self.nodes = list(self.switches.union(self.hosts))
        self.hosts = list(self.hosts)
        self.switches = list(self.switches)
        self.nodes_to_ids = dict()
        for i in range(len(self.nodes)):
            self.nodes_to_ids[self.nodes[i]] = i
        print(self.nodes)
        print(self.nodes_to_ids)
        # find links between a hosts and a switch
        for dpid in self.mac_to_port.keys():
            ports = dict()
            for mac in self.mac_to_port[dpid].keys():
                out_port = self.mac_to_port[dpid][mac]
                if out_port in ports.keys():
                    ports[out_port].append(mac)
                else:
                    ports[out_port] = [mac]
            for port in ports.keys():
                if len(ports[port]) == 1:
                    for mac in self.mac_to_port[dpid].keys():
                        if self.mac_to_port[dpid][mac] == port:
                            self.links.add((self.nodes_to_ids["switch_" + str(dpid)], self.nodes_to_ids["host_" + mac]))
                            break
        # find links between switches
        switchlist = list(self.switches)
        for i in range(len(switchlist)):
            for j in range(i + 1, len(switchlist)):
                s1 = switchlist[i]
                s2 = switchlist[j]
                s1_id = int(s1.replace("switch_", ""))
                s2_id = int(s2.replace("switch_", ""))
                maclist1 = set(self.mac_to_port[s1_id].keys())
                maclist1_copy = maclist1.copy()
                maclist2 = set(self.mac_to_port[s2_id].keys())
                maclist2_copy = maclist2.copy()
                for item in maclist1:
                    if item in maclist2_copy:
                        maclist2_copy.remove(item)
                for item in maclist2:
                    if item in maclist1_copy:
                        maclist1_copy.remove(item)
                if len(maclist1_copy) <= 1 and len(maclist2_copy) <= 1:
                    self.links.add((self.nodes_to_ids[s1],self.nodes_to_ids[s2]))
        print(self.hosts)
        print(self.switches)
        print(self.links)
        print("Topology computed")

    def build_twin_python(self):
        # # Create switch nodes

        # for i in range(3):
        switch_loop = f"""        for i in range({len(self.switches)}):"""

        # # Create host nodes
        hosts_loop = f"""        for i in range({len(self.hosts)}):"""

        links_code = """
"""
        for link in self.links:
            left = link[0]
            right = link[1]
            left_name = self.nodes[left]
            right_name = self.nodes[right]
            if left_name.startswith("switch_"):
                left_index = self.switches.index(left_name)
                left_name = f"s{left_index+1}"
            else:
                left_index = self.hosts.index(left_name)
                left_name = f"h{left_index+1}"
            if right_name.startswith("switch_"):
                right_index = self.switches.index(right_name)
                right_name = f"s{right_index+1}"
            else:
                right_index = self.hosts.index(right_name)
                right_name = f"h{right_index+1}"
            links_code += f"        self.addLink(\"{left_name}\", \"{right_name}\", **host_link_config)\n"

        with open("digital_twin_network.py","w",encoding='utf8') as out:
            out.write(INCLUDES)
            out.write(DIGITAL_TWIN_CLASS_DEFINITION)
            out.write(switch_loop)
            out.write(SWITCH_CREATION_BLOCK)
            out.write(hosts_loop)
            out.write(HOST_CREATION_BLOCK)
            out.write(links_code)
            out.write(DIGITAL_TWIN_MAIN)
        
        # docker cp digital_twin_network.py mikimax:root/network.py
        os.system("docker cp digital_twin_network.py mikimax:root/network.py")

        # optional (is it doable?): run the network in the container
        print("Twin Network Ready")


    def register_package(self, src, dst, size):
        now = time.time()
        elapsed = now - self.frame_start
        src = src.replace("00:00:00:00:00:", "")
        dst = dst.replace("00:00:00:00:00:", "")
        if src.startswith("0"):
            src = src[1:]
        if dst.startswith("0"):
            dst = dst[1:]
        src = "h" + src
        dst = "h" + dst
        if elapsed > FRAME_LENGTH_SECONDS:
            # SEND FRAME TO CONTAINER
            # docker cp traffic/1.txt mikimax:root/traffic/1.txt
            os.system(f"docker cp traffic/{self.current_frame}.txt mikimax:root/traffic/{self.current_frame}.txt")
            # UPDATE TO NEXT FRAME
            self.frame_start = now
            self.current_frame += 1
            elapsed = time.time() - self.frame_start
            with open(f"traffic/{self.current_frame}.txt", "w", encoding='utf8') as out:
                out.write(f"{elapsed} {src} {dst} {size}\n")
        else:
            # UPDATE CURRENT FRAME DATA
            with open(f"traffic/{self.current_frame}.txt", "a", encoding='utf8') as out:
                out.write(f"{elapsed} {src} {dst} {size}\n")

    def _count_msg(self, size):
        if not self.created_log_file:
            self.created_log_file = True
            with open("msg_count_parallel.txt", "w") as out:
                out.write("")
        elapsed = time.time() - self.creation_time
        with open("msg_count_parallel.txt", "a") as out:
            out.write(f"{elapsed} {size}\n")

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        self._count_msg(msg.msg_len)
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match["in_port"]

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        # ip4 = pkt.get_protocol(ipv4.ipv4)
        # print(ip4)

        # if eth.ethertype == ether_types.ETH_TYPE_IPV6:
        #     ip6 = pkt.get_protocol(ipv6.ipv6)
        #     print(ip6)

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        dst = eth.dst
        src = eth.src
        dpid = datapath.id
        # print(datapath.__dir__())
        self.mac_to_port.setdefault(dpid, {})

        # print("packet in ", dpid, src, dst, in_port, eth.ethertype)
        # print(self.mac_to_port)

        # learn a mac address
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
            # print("not flood")
            if not self.has_topology:
                self.frame_start = time.time()
                self.compute_topology()
                self.build_twin_python()
                self.has_topology = True
            self.register_package(src, dst, msg.msg_len)
        else:
            out_port = ofproto.OFPP_FLOOD
            # print("flood")

        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        # if out_port != ofproto.OFPP_FLOOD:
        #     match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
        #     # verify if we have a valid buffer_id, if yes avoid to send both
        #     # flow_mod & packet_out
        #     if msg.buffer_id != ofproto.OFP_NO_BUFFER:
        #         self.add_flow(datapath, 1, match, actions, msg.buffer_id)
        #         return
        #     else:
        #         self.add_flow(datapath, 1, match, actions)
        self._send_package(msg, datapath, in_port, actions)
